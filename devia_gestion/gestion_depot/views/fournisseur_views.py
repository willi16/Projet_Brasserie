# gestion_depot/views/fournisseur_views.py
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from ..models import Fournisseur
from ..decorators import group_required
from ..forms import FournisseurForm

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
            messages.success(request, f"Fournisseur '{fournisseur.nom}' mis à jour.")
            return redirect('gestion_depot:liste_fournisseurs')
    else:
        form = FournisseurForm(instance=fournisseur)

    return render(request, 'gestion_depot/fournisseur_form.html', {
        'form': form,
        'action': 'Modifier',
        'fournisseur': fournisseur,
    })

@group_required('Gérant', 'Admin')
def supprimer_fournisseur(request, pk):
    fournisseur = get_object_or_404(Fournisseur, pk=pk)
    nom = fournisseur.nom
    fournisseur.delete()
    messages.success(request, f"Fournisseur '{nom}' supprimé.")
    return redirect('gestion_depot:liste_fournisseurs')