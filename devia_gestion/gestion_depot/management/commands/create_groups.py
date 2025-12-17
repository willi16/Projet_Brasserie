# gestion_depot/management/commands/create_groups.py
from django.core.management.base import BaseCommand
from django.contrib.auth.models import Group

class Command(BaseCommand):
    help = 'Crée les groupes Caissier, Gerant, Admin'

    def handle(self, *args, **options):
        groups = ['Caissier', 'Gerant', 'Admin']
        for group_name in groups:
            group, created = Group.objects.get_or_create(name=group_name)
            if created:
                self.stdout.write(self.style.SUCCESS(f'Groupe "{group_name}" créé'))
            else:
                self.stdout.write(self.style.WARNING(f'Groupe "{group_name}" déjà existant'))