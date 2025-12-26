from django.contrib.auth.decorators import login_required
from django.shortcuts import render, redirect
from django.contrib.auth.models import User
from django.contrib import messages
from gestion_depot.forms import CreerCompteEmployeForm
from django.core.mail import send_mail
from django.conf import settings

@login_required
def creer_compte_employe(request):
    if not request.user.is_superuser:
        messages.error(request, "Accès réservé à l'administrateur.")
        return redirect('gestion_depot:dashboard')
    
    if request.method == 'POST':
        form = CreerCompteEmployeForm(request.POST, request.FILES)
        if form.is_valid():
            user = form.save()
             # Envoyer email
            send_mail(
                subject="Bienvenue sur la plateforme DEIVA !",
                message=f"""
            Bonjour {user.username},

            Votre compte a été créé avec succès sur la plateforme de gestion du dépôt DEIVA.

            Identifiants :
            - Nom d'utilisateur : {user.username}
            - Rôle : {form.cleaned_data['role']}

            Veuillez vous connecter dès maintenant : http://devia

            L'équipe DEIVA
            """,
                from_email=settings.DEFAULT_FROM_EMAIL,
                recipient_list=[user.email],
                fail_silently=False,
            )
            messages.success(request, f"Compte '{user.username}' créé avec succès.")
            return redirect('gestion_depot:dashboard')
    else:
        form = CreerCompteEmployeForm()

    return render(request, 'gestion_depot/creer_compte_employe.html', {'form': form})
    
  