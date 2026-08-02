# gestion_depot/models/parametre.py
from django.db import models
from decimal import Decimal

# Montant de la sanction par bouteille non rendue (500 FCFA par défaut)
SANCTION_CASIER = 'sanction_casier_montant'


class Parametre(models.Model):
    nom = models.CharField(max_length=50, unique=True)
    valeur = models.DecimalField(max_digits=12, decimal_places=2)

    @classmethod
    def get(cls, nom, default=None):
        obj = cls.objects.filter(nom=nom).first()
        return obj.valeur if obj else default

    @classmethod
    def get_sanction_montant(cls):
        valeur = cls.get(SANCTION_CASIER, Decimal('500'))
        return valeur or Decimal('0')

    def __str__(self):
        return f"{self.nom} = {self.valeur}"
