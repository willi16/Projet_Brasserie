from functools import wraps
from django.contrib.auth.decorators import login_required
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
    from django.contrib.auth.decorators import user_passes_test
    return user_passes_test(
        caissier_ou_superieur,
        login_url='/login/',
        redirect_field_name=None
    )(view_func)


def group_required(*group_names):
    """
    Vérifie que l'utilisateur est authentifié et membre d'un des groupes
    (ou superutilisateur). Non authentifié → redirection login.
    Authentifié sans droit → 403.
    """
    def decorator(view_func):
        @wraps(view_func)
        @login_required
        def _wrapped(request, *args, **kwargs):
            user = request.user
            if user.is_superuser or user.groups.filter(name__in=group_names).exists():
                return view_func(request, *args, **kwargs)
            raise PermissionDenied
        return _wrapped
    return decorator
