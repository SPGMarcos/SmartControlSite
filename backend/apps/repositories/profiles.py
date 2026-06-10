from apps.users.models import Profile


class ProfileRepository:
    @staticmethod
    def get_by_supabase_user_id(supabase_user_id):
        return Profile.objects.filter(id=supabase_user_id).first()

    @staticmethod
    def upsert_from_registration(*, supabase_user_id, email, nome, plano="client", creditos=0):
        profile, _ = Profile.objects.update_or_create(
            id=supabase_user_id,
            defaults={
                "email": email,
                "nome": nome,
                "plano": plano,
                "creditos": creditos,
            },
        )
        return profile
