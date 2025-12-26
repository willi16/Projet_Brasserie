from django.contrib.auth.decorators import user_passes_test
from django.core.exceptions import PermissionDenied


def caissier_ou_superieur(user):
    """
    Retourne True si l'utilisateur est :
    - Superutilisateur, OU
    - Membre du groupe 'Caissier', 'Gérant' ou 'Admin'
    """
    if not user.is_authenticated:
        return False
    if user.is_superuser:
        return True
    groupes_autorises = ['Caissier', 'Gérant', 'Admin']
    return user.groups.filter(name__in=groupes_autorises).exists()

def caissier_required(view_func):
    """
    Décorateur pour protéger les vues accessibles aux caissiers et plus.
    """
    return user_passes_test(
        caissier_ou_superieur,
        login_url='/login/',
        redirect_field_name=None
    )


def group_required(*group_names):
    def check_group(user):
        if user.is_authenticated and (user.is_superuser or user.groups.filter(name__in=group_names).exists()):
            return True
        raise PermissionDenied
    return user_passes_test(check_group)