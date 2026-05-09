from django.conf import settings
from rest_framework import status
from rest_framework.generics import GenericAPIView
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework_simplejwt.serializers import TokenRefreshSerializer
from rest_framework_simplejwt.exceptions import TokenError
from rest_framework_simplejwt.tokens import RefreshToken

from apps.core.services import audit

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
        secure=not settings.DEBUG,
        samesite="Lax",
        path="/api/auth/",
    )


def clear_refresh_cookie(response):
    response.delete_cookie(settings.JWT_REFRESH_COOKIE_NAME, path="/api/auth/", samesite="Lax")


class RegisterView(GenericAPIView):
    serializer_class = RegisterSerializer
    permission_classes = [AllowAny]
    throttle_scope = "register"

    def post(self, request):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.save()
        AuthLogService.record(request, "register", user=user, success=True)
        audit(user, "user.register", request=request, target=user)
        return Response(UserSerializer(user).data, status=status.HTTP_201_CREATED)


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
        refresh = RefreshToken.for_user(user)
        AuthLogService.record(request, "login_success", user=user, success=True)
        audit(user, "auth.login", request=request, target=user)
        response = Response(
            {
                "access": str(refresh.access_token),
                "user": UserSerializer(user).data,
            }
        )
        set_refresh_cookie(response, refresh)
        return response


class CookieTokenRefreshView(GenericAPIView):
    serializer_class = TokenRefreshSerializer
    permission_classes = [AllowAny]
    throttle_scope = "auth"

    def post(self, request):
        refresh_token = request.COOKIES.get(settings.JWT_REFRESH_COOKIE_NAME) or request.data.get("refresh")
        serializer = self.get_serializer(data={"refresh": refresh_token})
        serializer.is_valid(raise_exception=True)
        response = Response({"access": serializer.validated_data["access"]})
        if serializer.validated_data.get("refresh"):
            set_refresh_cookie(response, serializer.validated_data["refresh"])
        return response


class LogoutView(GenericAPIView):
    serializer_class = LogoutSerializer
    permission_classes = [IsAuthenticated]

    def post(self, request):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        refresh_token = serializer.validated_data.get("refresh") or request.COOKIES.get(settings.JWT_REFRESH_COOKIE_NAME)
        if refresh_token:
            try:
                token = RefreshToken(refresh_token)
                token.blacklist()
            except TokenError:
                pass
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
        user = serializer.validated_data["user"]
        user.set_password(serializer.validated_data["new_password"])
        user.save(update_fields=["password", "updated_at"])
        AuthLogService.record(request, "password_reset_confirmed", user=user, success=True)
        audit(user, "auth.password_reset", request=request, target=user)
        return Response({"detail": "Senha atualizada com sucesso."})
