# gestion_depot/models/mouvement.py
from django.db import models
from .produit import Produit
from .fournisseur import Fournisseur
from .ligne_vente import LigneVente
from django.contrib.auth.models import User
from django.core.validators import MinValueValidator

class Mouvement(models.Model):
    TYPE_CHOICES = [
        ('entree', 'Entrée'),
        ('sortie', 'Sortie'),
    ]
    produit = models.ForeignKey(Produit, on_delete=models.CASCADE)
    type_mouvement = models.CharField(max_length=10, choices=TYPE_CHOICES)
    quantite_casiers = models.DecimalField(max_digits=6, decimal_places=2, validators=[MinValueValidator(0.01)])
    date = models.DateTimeField(auto_now_add=True)
    fournisseur = models.ForeignKey(Fournisseur, on_delete=models.SET_NULL, null=True, blank=True)
    utilisateur = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)
    ligne_vente = models.ForeignKey(LigneVente, on_delete=models.SET_NULL, null=True, blank=True)


    def __str__(self):
        return f"{self.type_mouvement} - {self.produit.nom} - {self.quantite_casiers} casier(s)"