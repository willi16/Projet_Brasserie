from django.contrib.auth.decorators import login_required
from django.shortcuts import render, redirect
from django.contrib.auth.models import User
from django.contrib import messages
from django.urls import reverse
from gestion_depot.forms import CreerCompteEmployeForm
from gestion_depot.models import ParametresEntreprise
from gestion_depot.models.userActionLog import UserActionLog
from django.core.mail import send_mail
from django.conf import settings


def _peut_creer_compte(user):
    return user.is_superuser or user.groups.filter(name='Admin').exists()


@login_required
def creer_compte_employe(request):
    if not _peut_creer_compte(request.user):
        messages.error(request, "Accès réservé à l'administrateur.")
        return redirect('gestion_depot:dashboard')
    
    if request.method == 'POST':
        form = CreerCompteEmployeForm(request.POST, request.FILES)
        if form.is_valid():
            user = form.save()
            UserActionLog.log_action(
                request.user, 'création_compte', module='comptes',
                details=f"Création du compte « {user.username} » (rôle : {form.cleaned_data['role']})",
                target_user=user, request=request,
            )
            # Envoyer email (ne bloque pas la création si l'envoi échoue)
            try:
                entreprise = ParametresEntreprise.get_singleton()
                send_mail(
                    subject=f"Bienvenue sur la plateforme {entreprise.nom} !",
                    message=f"""
Bonjour {user.username},

Votre compte a été créé avec succès sur la plateforme de gestion du dépôt {entreprise.nom}.

Identifiants :
- Nom d'utilisateur : {user.username}
- Rôle : {form.cleaned_data['role']}

Veuillez vous connecter dès maintenant : {request.build_absolute_uri(reverse('login'))}

L'équipe {entreprise.nom}
""",
                    from_email=settings.DEFAULT_FROM_EMAIL,
                    recipient_list=[user.email],
                    fail_silently=True,
                )
            except Exception:
                pass
            messages.success(request, f"Compte '{user.username}' créé avec succès.")
            return redirect('gestion_depot:dashboard')
    else:
        form = CreerCompteEmployeForm()

    return render(request, 'gestion_depot/creer_compte_employe.html', {'form': form})
    
  