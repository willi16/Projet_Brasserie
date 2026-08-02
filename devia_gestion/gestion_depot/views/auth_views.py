# gestion_depot/views/auth_views.py
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User, Group
from django.core.exceptions import PermissionDenied
from django.core.mail import send_mail
from django.conf import settings
from django.core.paginator import Paginator
from django.http import JsonResponse, HttpResponse
from datetime import timezone
import openpyxl

from gestion_depot.models import userActionLog


def _is_admin(user):
    return user.is_superuser or user.groups.filter(name='Admin').exists()


@login_required
def manage_users(request):
    # Vérifier si l'utilisateur est admin
    if not _is_admin(request.user):
        raise PermissionDenied("Vous n'êtes pas autorisé à gérer les comptes.")

    # Récupérer tous les groupes disponibles pour le filtre
    all_groups = Group.objects.all().order_by('name')

    # Filtre par groupe (via GET)
    group_filter = request.GET.get('group')
    if group_filter and group_filter != "all":
        users = User.objects.filter(groups__name=group_filter).distinct()
    else:
        users = User.objects.all()

    users = users.order_by('date_joined')

    # Pagination
    paginator = Paginator(users, 15)  # 15 utilisateurs par page
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    # Gestion des actions POST (activer/désactiver)
    if request.method == 'POST':
        user_id = request.POST.get('user_id')
        action = request.POST.get('action')
        user = get_object_or_404(User, id=user_id)

        # Empêcher la désactivation du compte de l'utilisateur courant
        if user == request.user and action == 'deactivate':
            messages.error(request, "Vous ne pouvez pas désactiver votre propre compte.")
            return redirect('manage_users')

        if action == 'activate':
            user.is_active = True
            user.save()
            userActionLog.objects.create(
                performed_by=request.user,
                target_user=user,
                action='activate'
            )
            messages.success(request, f"Le compte {user.username} a été activé.")
        elif action == 'deactivate':
            user.is_active = False
            user.save()

            # Envoyer un email à l'utilisateur désactivé (si email défini)
            if user.email:
                try:
                    send_mail(
                        subject="Votre compte a été désactivé",
                        message=f"""Bonjour {user.username},

Votre compte sur la plateforme Deiva Gestion a été désactivé par un administrateur.

Si vous pensez qu'il s'agit d'une erreur, veuillez contacter le support.

Cordialement,
L'équipe Deiva""",
                        from_email=settings.DEFAULT_FROM_EMAIL,
                        recipient_list=[user.email],
                        fail_silently=True,
                    )
                except Exception:
                    # Ne pas bloquer si l'email échoue
                    pass

            userActionLog.objects.create(
                performed_by=request.user,
                target_user=user,
                action='deactivate'
            )
            messages.success(request, f"Le compte {user.username} a été désactivé.")

        return redirect('manage_users')

    context = {
        'page_obj': page_obj,
        'users': users,
        'all_groups': all_groups,
        'selected_group': group_filter,
    }
    return render(request, 'gestion_depot/manage_users.html', context)


@login_required
def edit_user_roles(request, user_id):
    if not _is_admin(request.user):
        return JsonResponse({'error': 'Non autorisé'}, status=403)

    user = get_object_or_404(User, id=user_id)
    all_groups = Group.objects.all()

    if request.method == "POST":
        # Récupérer les nouveaux rôles
        selected_groups = request.POST.getlist('groups')
        user.groups.clear()
        for group_id in selected_groups:
            group = Group.objects.get(id=group_id)
            user.groups.add(group)
        messages.success(request, f"Rôles de {user.username} mis à jour.")
        return redirect('manage_users')

    context = {
        'user': user,
        'all_groups': all_groups,
        'user_groups': user.groups.values_list('id', flat=True),
    }
    return render(request, 'gestion_depot/edit_user_roles.html', context)


@login_required
def user_logs_full(request):
    if not _is_admin(request.user):
        raise PermissionDenied("Accès refusé.")

    logs = userActionLog.UserActionLog.objects.select_related('performed_by', 'target_user').order_by('-timestamp')

    # Export Excel
    if request.GET.get('export') == 'excel':
        wb = openpyxl.Workbook()
        ws = wb.active
        ws.title = "Historique des actions"

        # En-têtes
        ws.append(['Date', 'Admin', 'Action', 'Utilisateur ciblé', 'Détails'])

        for log in logs:
            ws.append([
                log.timestamp.strftime('%d/%m/%Y %H:%M'),
                str(log.performed_by or 'System'),
                log.get_action_display(),
                log.target_user.username,
                log.details or ''
            ])

        response = HttpResponse(
            content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
        )
        response['Content-Disposition'] = 'attachment; filename=historique_actions_deiva.xlsx'
        wb.save(response)
        return response

    # Pagination pour la page HTML
    paginator = Paginator(logs, 25)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    context = {
        'page_obj': page_obj,
    }
    return render(request, 'gestion_depot/user_logs_full.html', context)
