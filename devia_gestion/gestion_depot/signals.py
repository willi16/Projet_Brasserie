# gestion_depot/signals.py
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.contrib.auth.models import User
from gestion_depot.models import profil

@receiver(post_save, sender=User)
def create_profil_utilisateur(sender, instance, created, **kwargs):
    if created:
        profil.ProfilUtilisateur.objects.create(user=instance)

@receiver(post_save, sender=User)
def save_profil_utilisateur(sender, instance, **kwargs):
    try:
        instance.profilutilisateur.save()
        
    except:
        profil.ProfilUtilisateur.objects.create(user=instance)