# gestion_depot/views/fournisseur_views.py
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from ..models import Fournisseur
from ..decorators import group_required

@group_required('Gérant', 'Admin')
def liste_fournisseurs(request):
    fournisseurs = Fournisseur.objects.all()
    return render(request, 'gestion_depot/fournisseur_liste.html', {'fournisseurs': fournisseurs})

@group_required('Gérant', 'Admin')
def ajouter_fournisseur(request):
    if request.method == 'POST':
        nom = request.POST.get('nom')
        contact = request.POST.get('contact', '')
        adresse = request.POST.get('adresse', '')

        fournisseur = Fournisseur.objects.create(
            nom=nom,
            contact=contact,
            adresse=adresse
        )
        messages.success(request, f"✅ Fournisseur '{fournisseur.nom}' ajouté.")
        return redirect('gestion_depot:liste_fournisseurs')

    return render(request, 'gestion_depot/fournisseur_form.html', {'action': 'Ajouter'})

@group_required('Gérant', 'Admin')
def modifier_fournisseur(request, pk):
    fournisseur = get_object_or_404(Fournisseur, pk=pk)

    if request.method == 'POST':
        fournisseur.nom = request.POST.get('nom')
        fournisseur.contact = request.POST.get('contact')
        fournisseur.adresse = request.POST.get('adresse')
        fournisseur.save()

        messages.success(request, f"✅ Fournisseur '{fournisseur.nom}' mis à jour.")
        return redirect('gestion_depot:liste_fournisseurs')

    return render(request, 'gestion_depot/fournisseur_form.html', {
        'action': 'Modifier',
        'fournisseur': fournisseur
    })

@group_required('Gérant', 'Admin')
def supprimer_fournisseur(request, pk):
    fournisseur = get_object_or_404(Fournisseur, pk=pk)
    nom = fournisseur.nom
    fournisseur.delete()
    messages.success(request, f"🗑️ Fournisseur '{nom}' supprimé.")
    return redirect('gestion_depot:liste_fournisseurs')