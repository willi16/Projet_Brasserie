# gestion_depot/models/casier_emporte.py
from datetime import timedelta
from decimal import Decimal
from django.db import models
from django.utils import timezone
from .client import Client
from .bon_vente import BonVente
from .parametre import Parametre
from .produit import Produit

DELAI_RETOUR_JOURS = 3

BOUTEILLES_PAR_MODELE = {
    'GM12': 12,
    'GM20': 20,
    'PM24': 24,
}


class CasierEmporte(models.Model):
    bon = models.OneToOneField(BonVente, related_name='casier_emporte', on_delete=models.CASCADE)
    client = models.ForeignKey(Client, on_delete=models.CASCADE)
    modele = models.CharField(max_length=10, choices=Produit.MODELE_CHOICES, default='GM12')
    nombre_casiers = models.IntegerField()
    nombre_rendus = models.IntegerField(default=0)
    date_emport = models.DateTimeField(auto_now_add=True)
    date_retour_complet = models.DateTimeField(blank=True, null=True)

    @property
    def restant(self):
        return self.nombre_casiers - self.nombre_rendus

    @property
    def bouteilles_par_casier(self):
        return BOUTEILLES_PAR_MODELE.get(self.modele, 12)

    @property
    def restant_bouteilles(self):
        return self.restant * self.bouteilles_par_casier

    @property
    def date_limite(self):
        return self.date_emport + timedelta(days=DELAI_RETOUR_JOURS)

    @property
    def en_retard(self):
        if self.restant <= 0:
            return False
        return timezone.now() > self.date_limite

    @property
    def montant_sanction(self):
        if not self.en_retard:
            return Decimal('0')
        return self.restant_bouteilles * Parametre.get_sanction_montant()

    def __str__(self):
        return f"Casiers {self.nombre_casiers} - {self.client}"
