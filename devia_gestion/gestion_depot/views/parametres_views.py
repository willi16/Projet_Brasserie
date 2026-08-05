# gestion_depot/views/parametres_views.py
from django.contrib import messages
from django.shortcuts import render, redirect
from django.core.exceptions import PermissionDenied
from gestion_depot.models import ParametresEntreprise
from gestion_depot.forms import ParametresEntrepriseForm


def _autorise(request):
    return request.user.is_superuser or request.user.groups.filter(name__in=['Gérant', 'Admin']).exists()


def configurer_entreprise(request):
    if not _autorise(request):
        raise PermissionDenied

    entreprise = ParametresEntreprise.get_singleton()

    if request.method == 'POST':
        form = ParametresEntrepriseForm(request.POST, request.FILES, instance=entreprise)
        if form.is_valid():
            form.save()
            messages.success(request, "Paramètres de l'entreprise mis à jour.")
            return redirect('gestion_depot:configurer_entreprise')
        messages.error(request, "Veuillez corriger les erreurs du formulaire.")
    else:
        form = ParametresEntrepriseForm(instance=entreprise)

    return render(request, 'gestion_depot/parametres_entreprise.html', {
        'form': form,
        'entreprise': entreprise,
    })
