from django.db import models
class Client(models.Model):
    nom = models.CharField(max_length=100)
    telephone = models.CharField(max_length=20, blank=True, null=True)
    adresse = models.TextField(blank=True, null=True)
    credit_total = models.DecimalField(max_digits=12, decimal_places=2, default=0)

    def __str__(self):
        return self.nom