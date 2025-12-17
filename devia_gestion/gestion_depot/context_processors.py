# gestion_depot/context_processors.py

def user_role(request):
    if request.user.is_authenticated:
        groups = request.user.groups.values_list('name', flat=True)
        return {
            'is_caissier': 'Caissiers' in groups,
            'is_gerant': 'Gérants' in groups,
            'is_admin': 'Admin' in groups or request.user.is_superuser,
        }
    return {}