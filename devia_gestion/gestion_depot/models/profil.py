# gestion_depot/models/profil.py
from django.db import models
from django.contrib.auth.models import User

class ProfilUtilisateur(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    photo = models.ImageField(upload_to='photos/', blank=True, null=True)
    carte_id_recto = models.ImageField(upload_to='cartes_id/recto/', blank=True, null=True)
    carte_id_verso = models.ImageField(upload_to='cartes_id/verso/', blank=True, null=True)
    date_naissance = models.DateField(blank=True, null=True)
    telephone = models.CharField(max_length=20, blank=True, null=True)
    adresse = models.TextField(blank=True, null=True)
    statut_marital = models.CharField(
        max_length=20,
        choices=[
            ('celibataire', 'Célibataire'),
            ('marie', 'Marié(e)'),
            ('divorce', 'Divorcé(e)'),
            ('veuf', 'Veuf(ve)'),
        ],
        blank=True,
        null=True
    )


    def __str__(self):
        return f"Profil de {self.user.username}"