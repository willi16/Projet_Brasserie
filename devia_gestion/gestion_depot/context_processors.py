# gestion_depot/context_processors.py
from .models import ParametresEntreprise


def user_role(request):
    if request.user.is_authenticated:
        groups = request.user.groups.values_list('name', flat=True)
        return {
            'is_caissier': 'Caissier' in groups,
            'is_gerant': 'Gérant' in groups,
            'is_admin': 'Admin' in groups or request.user.is_superuser,
        }
    return {}


def entreprise(request):
    return {'entreprise': ParametresEntreprise.get_singleton()}
