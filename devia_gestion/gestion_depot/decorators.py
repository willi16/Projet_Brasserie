# # gestion_depot/decorators.py
# from django.contrib.auth.decorators import user_passes_test

# def group_required(*group_names):
#     """Décorateur pour restreindre l'accès selon le groupe"""
#     def in_groups(u):
#         if u.is_authenticated:
#             if bool(u.groups.filter(name__in=group_names)) | u.is_superuser:
#                 return True
#         return False
#     return user_passes_test(in_groups)


from django.contrib.auth.decorators import user_passes_test
from django.core.exceptions import PermissionDenied

def group_required(*group_names):
    def check_group(user):
        if user.is_authenticated and (user.is_superuser or user.groups.filter(name__in=group_names).exists()):
            return True
        raise PermissionDenied
    return user_passes_test(check_group)