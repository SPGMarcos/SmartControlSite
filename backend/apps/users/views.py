from django.conf import settings
from rest_framework import status
from rest_framework.generics import GenericAPIView
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.core.services import audit
from apps.lib.supabase.client import SupabaseAuthClient

from .serializers import (
    LoginSerializer,
    LogoutSerializer,
    PasswordResetConfirmSerializer,
    PasswordResetRequestSerializer,
    RegisterSerializer,
    UserSerializer,
)
from .services import AuthLogService, PasswordResetService


def set_refresh_cookie(response, refresh_token):
    response.set_cookie(
        settings.JWT_REFRESH_COOKIE_NAME,
        str(refresh_token),
        max_age=settings.JWT_REFRESH_COOKIE_MAX_AGE,
        httponly=True,
        secure=settings.JWT_REFRESH_COOKIE_SECURE,
        samesite=settings.JWT_REFRESH_COOKIE_SAMESITE,
        path="/api/auth/",
    )


def clear_refresh_cookie(response):
    response.delete_cookie(
        settings.JWT_REFRESH_COOKIE_NAME,
        path="/api/auth/",
        secure=settings.JWT_REFRESH_COOKIE_SECURE,
        samesite=settings.JWT_REFRESH_COOKIE_SAMESITE,
    )


class RegisterView(GenericAPIView):
    serializer_class = RegisterSerializer
    permission_classes = [AllowAny]
    throttle_scope = "register"

    def post(self, request):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.save()
        session = SupabaseAuthClient().sign_in_with_password(
            email=serializer.validated_data["email"],
            password=serializer.validated_data["password"],
        )
        AuthLogService.record(request, "register", user=user, success=True)
        audit(user, "user.register", request=request, target=user)
        response = Response(
            {
                "access": session["access_token"],
                "refresh": session["refresh_token"],
                "user": UserSerializer(user).data,
            },
            status=status.HTTP_201_CREATED,
        )
        set_refresh_cookie(response, session["refresh_token"])
        return response


class LoginView(GenericAPIView):
    serializer_class = LoginSerializer
    permission_classes = [AllowAny]
    throttle_scope = "auth"

    def post(self, request):
        serializer = self.get_serializer(data=request.data)
        if not serializer.is_valid():
            AuthLogService.record(request, "login_failed", email=request.data.get("email", ""), success=False)
            return Response({"detail": "Credenciais invalidas."}, status=status.HTTP_401_UNAUTHORIZED)

        user = serializer.validated_data["user"]
        session = serializer.validated_data["session"]
        AuthLogService.record(request, "login_success", user=user, success=True)
        audit(user, "auth.login", request=request, target=user)
        response = Response(
            {
                "access": session["access_token"],
                "refresh": session["refresh_token"],
                "user": UserSerializer(user).data,
            }
        )
        set_refresh_cookie(response, session["refresh_token"])
        return response


class CookieTokenRefreshView(GenericAPIView):
    permission_classes = [AllowAny]
    throttle_scope = "auth"

    def post(self, request):
        refresh_token = request.COOKIES.get(settings.JWT_REFRESH_COOKIE_NAME) or request.data.get("refresh")
        if not refresh_token:
            return Response({"detail": "Refresh token ausente."}, status=status.HTTP_401_UNAUTHORIZED)
        try:
            session = SupabaseAuthClient().refresh_session(refresh_token=refresh_token)
        except Exception:
            response = Response({"detail": "Sessao expirada."}, status=status.HTTP_401_UNAUTHORIZED)
            clear_refresh_cookie(response)
            return response
        response = Response({"access": session["access_token"], "refresh": session["refresh_token"]})
        set_refresh_cookie(response, session["refresh_token"])
        return response


class LogoutView(GenericAPIView):
    serializer_class = LogoutSerializer
    permission_classes = [IsAuthenticated]

    def post(self, request):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        refresh_token = serializer.validated_data.get("refresh") or request.COOKIES.get(settings.JWT_REFRESH_COOKIE_NAME)
        access_token = serializer.validated_data.get("access") or request.auth
        if access_token:
            SupabaseAuthClient().sign_out(access_token=access_token)
        AuthLogService.record(request, "logout", user=request.user, success=True)
        audit(request.user, "auth.logout", request=request, target=request.user)
        response = Response(status=status.HTTP_204_NO_CONTENT)
        clear_refresh_cookie(response)
        return response


class MeView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        return Response(UserSerializer(request.user).data)


class PasswordResetRequestView(GenericAPIView):
    serializer_class = PasswordResetRequestSerializer
    permission_classes = [AllowAny]
    throttle_scope = "password_reset"

    def post(self, request):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        email = serializer.validated_data["email"].lower().strip()
        PasswordResetService.request_reset(email)
        AuthLogService.record(request, "password_reset_requested", email=email, success=True)
        return Response({"detail": "Se o email estiver cadastrado, voce recebera instrucoes."})


class PasswordResetConfirmView(GenericAPIView):
    serializer_class = PasswordResetConfirmSerializer
    permission_classes = [AllowAny]
    throttle_scope = "password_reset"

    def post(self, request):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        SupabaseAuthClient().update_password(
            access_token=serializer.validated_data["access_token"],
            new_password=serializer.validated_data["new_password"],
        )
        AuthLogService.record(request, "password_reset_confirmed", success=True)
        return Response({"detail": "Senha atualizada com sucesso."})
