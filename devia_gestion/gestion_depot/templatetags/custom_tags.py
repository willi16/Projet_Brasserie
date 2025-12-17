# gestion_depot/templatetags/custom_tags.py
from django import template

register = template.Library()

@register.simple_tag
def user_can_edit(user):
    """Retourne True si l'utilisateur peut modifier/supprimer (pas caissier)."""
    if user.is_superuser:
        return True
    groupes_autorises = ['Gérants','Gérant','Gerant', 'Admin']
    return user.groups.filter(name__in=groupes_autorises).exists()