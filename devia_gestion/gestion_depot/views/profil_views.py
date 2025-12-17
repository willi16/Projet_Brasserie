# gestion_depot/views/profil_views.py
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.contrib.auth.models import User
from gestion_depot.models import ProfilUtilisateur
from gestion_depot.decorators import group_required

@login_required
def profil_utilisateur(request):
    profil = get_object_or_404(ProfilUtilisateur, user=request.user)
    return render(request, 'gestion_depot/profil.html', {'profil': profil})

@group_required('Gérant', 'Admin')
@login_required
def modifier_profil(request):
    profil = request.user.profilutilisateur

    if request.method == 'POST':
        profil.telephone = request.POST.get('telephone')
        profil.adresse = request.POST.get('adresse')

        if request.FILES.get('photo'):
            profil.photo = request.FILES['photo']

        profil.save()
        messages.success(request, "Profil mis à jour avec succès !")
        return redirect('gestion_depot:profil_utilisateur')

    return render(request, 'gestion_depot/modifier_profil.html', {'profil': profil})