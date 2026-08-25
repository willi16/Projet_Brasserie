# gestion_depot/views/fournisseur_views.py
from django.shortcuts import render, redirect, get_object_or_404
from django.views.decorators.http import require_POST
from django.contrib import messages
from django.db.models import ProtectedError
from ..models import Fournisseur
from ..decorators import group_required
from ..forms import FournisseurForm
from ..models.userActionLog import UserActionLog

@group_required('Gérant', 'Admin')
def liste_fournisseurs(request):
    fournisseurs = Fournisseur.objects.all()
    return render(request, 'gestion_depot/fournisseur_liste.html', {'fournisseurs': fournisseurs})

@group_required('Gérant', 'Admin')
def ajouter_fournisseur(request):
    if request.method == 'POST':
        form = FournisseurForm(request.POST)
        if form.is_valid():
            fournisseur = form.save()
            UserActionLog.log_action(
                request.user, 'création_fournisseur', module='fournisseurs',
                details=f"Création du fournisseur « {fournisseur.nom} »", request=request,
            )
            messages.success(request, f"Fournisseur '{fournisseur.nom}' ajouté.")
            return redirect('gestion_depot:liste_fournisseurs')
    else:
        form = FournisseurForm()

    return render(request, 'gestion_depot/fournisseur_form.html', {
        'form': form,
        'action': 'Ajouter',
    })

@group_required('Gérant', 'Admin')
def modifier_fournisseur(request, pk):
    fournisseur = get_object_or_404(Fournisseur, pk=pk)

    if request.method == 'POST':
        form = FournisseurForm(request.POST, instance=fournisseur)
        if form.is_valid():
            form.save()
            UserActionLog.log_action(
                request.user, 'modification_fournisseur', module='fournisseurs',
                details=f"Modification du fournisseur « {fournisseur.nom} »", request=request,
            )
            messages.success(request, f"Fournisseur '{fournisseur.nom}' mis à jour.")
            return redirect('gestion_depot:liste_fournisseurs')
    else:
        form = FournisseurForm(instance=fournisseur)

    return render(request, 'gestion_depot/fournisseur_form.html', {
        'form': form,
        'action': 'Modifier',
        'fournisseur': fournisseur,
    })

@require_POST
@group_required('Gérant', 'Admin')
def supprimer_fournisseur(request, pk):
    fournisseur = get_object_or_404(Fournisseur, pk=pk)
    nom = fournisseur.nom
    try:
        fournisseur.delete()
    except ProtectedError:
        messages.error(
            request,
            f"Impossible de supprimer « {nom} » : ce fournisseur est lié à des livraisons existantes."
        )
        return redirect('gestion_depot:liste_fournisseurs')
    UserActionLog.log_action(
        request.user, 'suppression_fournisseur', module='fournisseurs',
        details=f"Suppression du fournisseur « {nom} »", request=request,
    )
    messages.success(request, f"Fournisseur '{nom}' supprimé.")
    return redirect('gestion_depot:liste_fournisseurs')