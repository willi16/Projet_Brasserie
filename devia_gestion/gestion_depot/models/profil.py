# gestion_depot/models/profil.py
from django.db import models
from django.contrib.auth.models import User

class ProfilUtilisateur(models.Model):
    utilisateur = models.OneToOneField(User, on_delete=models.CASCADE)
    photo = models.ImageField(upload_to='photos/', blank=True, null=True)
    telephone = models.CharField(max_length=20, blank=True, null=True)
    adresse = models.TextField(blank=True, null=True)


    def __str__(self):
        return f"Profil de {self.utilisateur.username}"