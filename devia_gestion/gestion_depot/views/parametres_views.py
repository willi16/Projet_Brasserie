# gestion_depot/views/parametres_views.py
from django.contrib import messages
from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.core.exceptions import PermissionDenied
from gestion_depot.models import ParametresEntreprise
from gestion_depot.models.userActionLog import UserActionLog
from gestion_depot.forms import ParametresEntrepriseForm


def _autorise(user):
    return user.is_superuser or user.groups.filter(name__in=['Gérant', 'Admin']).exists()


@login_required
def configurer_entreprise(request):
    if not _autorise(request.user):
        raise PermissionDenied

    entreprise = ParametresEntreprise.get_singleton()

    if request.method == 'POST':
        form = ParametresEntrepriseForm(request.POST, request.FILES, instance=entreprise)
        if form.is_valid():
            form.save()
            UserActionLog.log_action(
                request.user, 'modification_entreprise', module='parametres',
                details="Mise à jour des paramètres de l'entreprise", request=request,
            )
            messages.success(request, "Paramètres de l'entreprise mis à jour.")
            return redirect('gestion_depot:configurer_entreprise')
        messages.error(request, "Veuillez corriger les erreurs du formulaire.")
    else:
        form = ParametresEntrepriseForm(instance=entreprise)

    return render(request, 'gestion_depot/parametres_entreprise.html', {
        'form': form,
        'entreprise': entreprise,
    })
