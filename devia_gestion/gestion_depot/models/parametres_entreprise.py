# gestion_depot/models/parametres_entreprise.py
from django.db import models


class ParametresEntreprise(models.Model):
    """Paramètres uniques de l'entreprise (configurés lors de l'installation client)."""

    nom = models.CharField(max_length=100, default="DEIVA")
    sous_titre = models.CharField(max_length=200, blank=True, default="Commerce Général")
    description = models.TextField(
        blank=True,
        default="Vente en Gros et en Détails de Boissons,\nEaux Minérales et Divers",
    )
    telephone = models.CharField(max_length=100, blank=True, default="+22890695391 / 98888642")
    email = models.EmailField(blank=True, default="etsdeivtg@gmail.com")
    adresse = models.CharField(max_length=255, blank=True, default="Lomé - TOGO")
    devise = models.CharField(max_length=10, blank=True, default="F")
    logo = models.ImageField(upload_to="entreprise/", blank=True, null=True)
    cachet = models.ImageField(upload_to="entreprise/", blank=True, null=True)
    fond_login = models.ImageField(upload_to="entreprise/", blank=True, null=True)

    @classmethod
    def get_singleton(cls):
        obj, _ = cls.objects.get_or_create(pk=1)
        return obj

    def description_lignes(self):
        return self.description.splitlines() or [""]

    def __str__(self):
        return self.nom
