# gestion_depot/signals.py
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.contrib.auth.models import User
from django.contrib.auth.signals import user_logged_in, user_logged_out
from gestion_depot.models import ProfilUtilisateur, UserActionLog


@receiver(post_save, sender=User)
def ensure_profil_utilisateur(sender, instance, created, **kwargs):
    ProfilUtilisateur.objects.get_or_create(user=instance)


@receiver(user_logged_in)
def journal_connexion(sender, request, user, **kwargs):
    UserActionLog.log_action(
        performed_by=user,
        action='connexion',
        module='auth',
        details=f"Connexion de {user.username}",
        request=request,
    )


@receiver(user_logged_out)
def journal_deconnexion(sender, request, user, **kwargs):
    if user is None:
        return
    UserActionLog.log_action(
        performed_by=user,
        action='deconnexion',
        module='auth',
        details=f"Déconnexion de {user.username}",
        request=request,
    )
