
from django.db import models
from .client import Client

from django.contrib.auth.models import User

class BonVente(models.Model):
    STATUT_CHOICES = [
        ('en_cours', 'En cours'),
        ('valide', 'Validée'),
        ('annule', 'Annulée'),
    ]
    reference = models.CharField(max_length=50, unique=True)
    date_vente = models.DateTimeField(auto_now_add=True)
    vendeur = models.ForeignKey(User, on_delete=models.CASCADE)
    client = models.ForeignKey('Client', on_delete=models.SET_NULL, null=True, blank=True)
    type_paiement = models.CharField(max_length=20, choices=[('especes', 'Espèces'), ('credit', 'Crédit')])
    statut = models.CharField(max_length=20, choices=STATUT_CHOICES, default='valide')
    facture_pdf = models.FileField(upload_to='factures/', blank=True, null=True)
    date_facture_generee = models.DateTimeField(blank=True, null=True)

    def save(self, *args, **kwargs):
        # Sauvegarde initiale pour obtenir un ID si c'est un nouvel objet
        if not self.pk:
            super().save(*args, **kwargs)

        if not self.reference:
            self.reference = f"VENTE-{self.pk:04d}"
            super().save(update_fields=['reference'])

    
    def total(self):
        return sum(ligne.prix_total() for ligne in self.lignes.all())

    def __str__(self):
        return f"Vente {self.reference} - {self.total()} FCFA"

