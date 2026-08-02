# gestion_depot/views/casier_views.py
from decimal import Decimal, InvalidOperation
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.views.decorators.http import require_POST
from django.contrib import messages
from django.db import transaction
from django.db.models import F
from django.utils import timezone
from datetime import timedelta

from gestion_depot.models import CasierEmporte, Parametre
from gestion_depot.models.parametre import SANCTION_CASIER
from gestion_depot.models.casier_emporte import DELAI_RETOUR_JOURS


def _peut_gerer_casiers(user):
    """Caissiers, Gérants et Admins gèrent les casiers emportés."""
    if user.is_superuser:
        return True
    return user.groups.filter(name__in=['Caissier', 'Gérant', 'Admin']).exists()


@login_required
def liste_casiers_emportes(request):
    if not _peut_gerer_casiers(request.user):
        messages.error(request, "Vous n'êtes pas autorisé à consulter les casiers emportés.")
        return redirect('gestion_depot:dashboard')

    casiers = CasierEmporte.objects.select_related('client', 'bon').order_by('date_emport')

    statut = request.GET.get('statut')
    limite_retard = timezone.now() - timedelta(days=DELAI_RETOUR_JOURS)
    en_retard = casiers.filter(
        nombre_casiers__gt=F('nombre_rendus'),
        date_emport__lt=limite_retard,
    )

    if statut == 'en_retard':
        casiers = en_retard
    elif statut == 'retourne':
        casiers = casiers.filter(date_retour_complet__isnull=False)
    elif statut == 'en_cours':
        casiers = casiers.filter(date_retour_complet__isnull=True).exclude(id__in=en_retard)

    total_restant_bouteilles = sum(c.restant_bouteilles for c in en_retard)
    total_sanction = sum(c.montant_sanction for c in en_retard)

    return render(request, 'gestion_depot/liste_casiers_emportes.html', {
        'casiers': casiers,
        'statut_filter': statut,
        'nb_en_retard': en_retard.count(),
        'nb_en_cours': CasierEmporte.objects.filter(date_retour_complet__isnull=True).exclude(id__in=en_retard).count(),
        'nb_retournes': CasierEmporte.objects.filter(date_retour_complet__isnull=False).count(),
        'total_restant_bouteilles': total_restant_bouteilles,
        'total_sanction': total_sanction,
        'montant_sanction': Parametre.get_sanction_montant(),
    })


@login_required
@require_POST
@transaction.atomic
def enregistrer_retour_casiers(request, id):
    if not _peut_gerer_casiers(request.user):
        messages.error(request, "Vous n'êtes pas autorisé à enregistrer un retour.")
        return redirect('gestion_depot:dashboard')

    casier = get_object_or_404(CasierEmporte, id=id)

    try:
        quantite = int(request.POST.get('quantite_rendue'))
    except (ValueError, TypeError):
        messages.error(request, "La quantité rendue est invalide.")
        return redirect('gestion_depot:liste_casiers_emportes')

    if quantite <= 0:
        messages.error(request, "La quantité rendue doit être positive.")
        return redirect('gestion_depot:liste_casiers_emportes')

    if quantite > casier.restant:
        messages.error(
            request,
            f"Quantité supérieure au restant ({casier.restant} casier(s)).",
        )
        return redirect('gestion_depot:liste_casiers_emportes')

    casier.nombre_rendus += quantite
    if casier.nombre_rendus >= casier.nombre_casiers:
        casier.date_retour_complet = timezone.now()
    casier.save(update_fields=['nombre_rendus', 'date_retour_complet'])

    messages.success(request, f"{quantite} casier(s) retourné(s) enregistré(s).")
    return redirect('gestion_depot:liste_casiers_emportes')


@login_required
def configurer_sanction(request):
    if not (request.user.is_superuser or request.user.groups.filter(name__in=['Gérant', 'Admin']).exists()):
        messages.error(request, "Vous n'êtes pas autorisé à modifier les paramètres.")
        return redirect('gestion_depot:dashboard')

    param, _ = Parametre.objects.get_or_create(
        nom=SANCTION_CASIER,
        defaults={'valeur': Decimal('500')},
    )

    if request.method == 'POST':
        try:
            montant = Decimal(request.POST.get('montant'))
        except (InvalidOperation, TypeError, ValueError):
            messages.error(request, "Le montant est invalide.")
            return redirect('gestion_depot:configurer_sanction')
        if montant < 0:
            messages.error(request, "Le montant ne peut pas être négatif.")
            return redirect('gestion_depot:configurer_sanction')
        param.valeur = montant
        param.save()
        messages.success(request, f"Montant de la sanction mis à jour : {montant} FCFA.")
        return redirect('gestion_depot:configurer_sanction')

    return render(request, 'gestion_depot/parametres_sanction.html', {
        'param': param,
        'delai': DELAI_RETOUR_JOURS,
    })
