# gestion_depot/management/commands/generer_rapport_quotidien.py
import os
from datetime import datetime, time
from django.core.management.base import BaseCommand
from django.conf import settings
from django.utils import timezone
from gestion_depot.models import LigneVente


class Command(BaseCommand):
    help = "Génère le rapport de vente du jour et l'archive dans media/rapports/"

    def handle(self, *args, **options):
        maintenant = timezone.localtime()
        jour = maintenant.date()
        debut = timezone.make_aware(datetime.combine(jour, time.min), timezone.get_current_timezone())
        fin = timezone.make_aware(datetime.combine(jour, time.max), timezone.get_current_timezone())

        lignes = LigneVente.objects.filter(
            bon__statut='valide',
            bon__date_vente__gte=debut,
            bon__date_vente__lte=fin,
        ).select_related('produit', 'bon')

        total_ca = 0.0
        total_cout = 0.0
        par_produit = {}
        nb_ventes = lignes.values('bon_id').distinct().count()

        for ligne in lignes:
            quantite = float(ligne.quantite_casiers * ligne.fraction)
            prix_vente = float(ligne.produit.prix_vente_casier)
            prix_achat = float(ligne.produit.prix_achat_casier)
            total_ca += prix_vente * quantite
            total_cout += prix_achat * quantite
            par_produit[ligne.produit.nom] = par_produit.get(ligne.produit.nom, 0.0) + quantite

        lignes_texte = "\n".join(
            f"  - {nom}: {qte:.2f} casiers" for nom, qte in sorted(par_produit.items())
        ) or "  - Aucune vente"

        contenu = (
            f"Rapport des ventes du {jour:%d/%m/%Y}\n"
            f"=====================================\n"
            f"Nombre de ventes : {nb_ventes}\n"
            f"Chiffre d'affaires : {total_ca:,.2f} FCFA\n"
            f"Coût total : {total_cout:,.2f} FCFA\n"
            f"Bénéfice : {total_ca - total_cout:,.2f} FCFA\n"
            f"\nDétail par produit :\n{lignes_texte}\n"
        )

        rapport_dir = os.path.join(settings.MEDIA_ROOT, 'rapports')
        os.makedirs(rapport_dir, exist_ok=True)
        chemin = os.path.join(rapport_dir, f"rapport_{jour:%Y%m%d}.txt")
        with open(chemin, 'w', encoding='utf-8') as f:
            f.write(contenu)

        self.stdout.write(self.style.SUCCESS(f"Rapport quotidien écrit dans {chemin}"))
