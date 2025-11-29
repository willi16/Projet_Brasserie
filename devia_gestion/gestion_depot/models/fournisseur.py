# gestion_depot/models/fournisseur.py
from django.db import models

class Fournisseur(models.Model):
    nom = models.CharField(max_length=100)
    contact = models.CharField(max_length=50, blank=True)
    adresse = models.CharField(max_length=200, blank=True)

    def __str__(self):
        return self.nom