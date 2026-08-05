# gestion_depot/views/datatable_views.py
from datetime import timedelta

from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.core.exceptions import PermissionDenied
from django.db.models import Sum, Case, When, F, FloatField
from django.utils import timezone

from gestion_depot.datatable_api import dt_json
from gestion_depot.decorators import group_required
from gestion_depot.models import Produit, Fournisseur, BonLivraison, BonVente, CasierEmporte
from gestion_depot.models.casier_emporte import DELAI_RETOUR_JOURS
from gestion_depot.models.userActionLog import UserActionLog
from gestion_depot.serializers import (
    ProduitSerializer,
    FournisseurSerializer,
    LivraisonSerializer,
    BonVenteSerializer,
    CasierSerializer,
    UserSerializer,
    UserLogSerializer,
)


def _stock_annotation():
    return Sum(
        Case(
            When(mouvement__type_mouvement='entree', then=F('mouvement__quantite_casiers')),
            When(mouvement__type_mouvement='sortie', then=-F('mouvement__quantite_casiers')),
            default=0,
            output_field=FloatField(),
        )
    )


def _is_admin(user):
    return user.is_superuser or user.groups.filter(name='Admin').exists()


def _peut_gerer_casiers(user):
    if user.is_superuser:
        return True
    return user.groups.filter(name__in=['Caissier', 'Gérant', 'Admin']).exists()


@group_required('Caissier', 'Gérant', 'Admin')
def dt_produits(request):
    qs = Produit.objects.annotate(stock_actuel=_stock_annotation())
    return dt_json(
        request, qs,
        columns=[
            'nom', 'categorie_display', 'casier_contenu', 'modele_display',
            'prix_vente_casier', 'stock_actuel', 'seuil_alerte',
            'statut_html', 'actions_html',
        ],
        searchable=['nom', 'categorie', 'modele'],
        search_map={
            'categorie_display': 'categorie',
            'modele_display': 'modele',
        },
        order_map={
            'nom': 'nom',
            'categorie_display': 'categorie',
            'casier_contenu': 'casier_contenu',
            'modele_display': 'modele',
            'prix_vente_casier': 'prix_vente_casier',
            'stock_actuel': 'stock_actuel',
            'seuil_alerte': 'seuil_alerte',
            'statut_html': None,
            'actions_html': None,
        },
        serializer=ProduitSerializer,
        default_order=('nom', 'asc'),
    )


@group_required('Gérant', 'Admin')
def dt_fournisseurs(request):
    return dt_json(
        request, Fournisseur.objects.all(),
        columns=['nom', 'contact', 'adresse', 'actions_html'],
        searchable=['nom', 'contact', 'adresse'],
        search_map={'actions_html': None},
        order_map={
            'nom': 'nom',
            'contact': 'contact',
            'adresse': 'adresse',
            'actions_html': None,
        },
        serializer=FournisseurSerializer,
        default_order=('nom', 'asc'),
    )


@group_required('Gérant', 'Admin')
def dt_livraisons(request):
    qs = BonLivraison.objects.select_related('fournisseur', 'utilisateur').annotate(
        total_quantite_ann=Sum('lignes__quantite_casiers'),
        total_montant_ann=Sum(F('lignes__quantite_casiers') * F('lignes__prix_achat_casier')),
    )
    return dt_json(
        request, qs,
        columns=[
            'reference', 'date_livraison', 'fournisseur_nom', 'utilisateur_nom',
            'total_quantite', 'total_montant', 'actions_html',
        ],
        searchable=['reference', 'fournisseur__nom', 'utilisateur__username'],
        search_map={
            'fournisseur_nom': 'fournisseur__nom',
            'utilisateur_nom': 'utilisateur__username',
        },
        order_map={
            'reference': 'reference',
            'date_livraison': 'date_livraison',
            'fournisseur_nom': 'fournisseur__nom',
            'utilisateur_nom': 'utilisateur__username',
            'total_quantite': 'total_quantite_ann',
            'total_montant': 'total_montant_ann',
            'actions_html': None,
        },
        serializer=LivraisonSerializer,
        default_order=('date_livraison', 'desc'),
    )


@login_required
def dt_bons_vente(request):
    user = request.user
    is_caissier = user.groups.filter(name='Caissier').exists()
    qs = BonVente.objects.select_related('client', 'vendeur')
    if is_caissier and not (user.is_superuser or user.groups.filter(name__in=['Gérant', 'Admin']).exists()):
        qs = qs.filter(vendeur=user)
    qs = qs.annotate(
        montant_total=Sum(
            F('lignes__produit__prix_vente_casier') * F('lignes__fraction') * F('lignes__quantite_casiers'),
            output_field=FloatField(),
        )
    )

    def filtre(qs, request):
        statut = request.GET.get('statut')
        vendeur_id = request.GET.get('vendeur')
        date_debut = request.GET.get('date_debut')
        date_fin = request.GET.get('date_fin')
        if statut:
            qs = qs.filter(statut=statut)
        if vendeur_id and not is_caissier:
            qs = qs.filter(vendeur_id=vendeur_id)
        if date_debut:
            qs = qs.filter(date_vente__gte=date_debut)
        if date_fin:
            try:
                date_fin_complet = timezone.datetime.strptime(date_fin, '%Y-%m-%d').replace(
                    hour=23, minute=59, second=59
                )
                qs = qs.filter(date_vente__lte=date_fin_complet)
            except ValueError:
                pass
        return qs

    return dt_json(
        request, qs,
        columns=[
            'reference', 'date_vente', 'client_nom', 'vendeur_nom',
            'montant_total', 'statut_html', 'actions_html',
        ],
        searchable=['reference', 'client__nom', 'vendeur__username'],
        search_map={
            'client_nom': 'client__nom',
            'vendeur_nom': 'vendeur__username',
            'statut_html': 'statut',
        },
        order_map={
            'reference': 'reference',
            'date_vente': 'date_vente',
            'client_nom': 'client__nom',
            'vendeur_nom': 'vendeur__username',
            'montant_total': 'montant_total',
            'statut_html': 'statut',
            'actions_html': None,
        },
        filter_fn=filtre,
        serializer=BonVenteSerializer,
        default_order=('date_vente', 'desc'),
    )


@login_required
def dt_casiers(request):
    if not _peut_gerer_casiers(request.user):
        raise PermissionDenied("Accès refusé.")
    qs = CasierEmporte.objects.select_related('client', 'bon')

    def filtre(qs, request):
        statut = request.GET.get('statut')
        limite_retard = timezone.now() - timedelta(days=DELAI_RETOUR_JOURS)
        en_retard = qs.filter(
            nombre_casiers__gt=F('nombre_rendus'),
            date_emport__lt=limite_retard,
        )
        if statut == 'en_retard':
            return en_retard
        if statut == 'retourne':
            return qs.filter(date_retour_complet__isnull=False)
        if statut == 'en_cours':
            return qs.filter(date_retour_complet__isnull=True).exclude(id__in=en_retard)
        return qs

    return dt_json(
        request, qs,
        columns=[
            'client_nom', 'bon_reference', 'modele_display', 'date_emport',
            'date_limite', 'nombre_casiers', 'nombre_rendus', 'restant',
            'restant_bouteilles', 'statut_html', 'sanction_html', 'actions_html',
        ],
        searchable=['client__nom', 'bon__reference'],
        search_map={
            'client_nom': 'client__nom',
            'bon_reference': 'bon__reference',
            'modele_display': 'modele',
            'statut_html': None,
        },
        order_map={
            'client_nom': 'client__nom',
            'bon_reference': 'bon__reference',
            'modele_display': 'modele',
            'date_emport': 'date_emport',
            'date_limite': None,
            'nombre_casiers': 'nombre_casiers',
            'nombre_rendus': 'nombre_rendus',
            'restant': None,
            'restant_bouteilles': None,
            'statut_html': None,
            'sanction_html': None,
            'actions_html': None,
        },
        filter_fn=filtre,
        serializer=CasierSerializer,
        default_order=('date_emport', 'desc'),
    )


@login_required
def dt_users(request):
    if not _is_admin(request.user):
        raise PermissionDenied("Accès refusé.")
    qs = User.objects.all()

    def filtre(qs, request):
        group = request.GET.get('group')
        if group and group != 'all':
            return qs.filter(groups__name=group).distinct()
        return qs

    return dt_json(
        request, qs,
        columns=['username', 'email', 'statut_html', 'roles_html', 'actions_html'],
        searchable=['username', 'email'],
        search_map={'statut_html': 'is_active'},
        order_map={
            'username': 'username',
            'email': 'email',
            'statut_html': 'is_active',
            'roles_html': None,
            'actions_html': None,
        },
        filter_fn=filtre,
        serializer=UserSerializer,
        default_order=('username', 'asc'),
    )


@login_required
def dt_logs(request):
    if not _is_admin(request.user):
        raise PermissionDenied("Accès refusé.")
    qs = UserActionLog.objects.select_related('performed_by', 'target_user')

    return dt_json(
        request, qs,
        columns=[
            'timestamp', 'performed_by_nom', 'action_display',
            'target_user_nom', 'details',
        ],
        searchable=['performed_by__username', 'target_user__username', 'action', 'details'],
        search_map={
            'performed_by_nom': 'performed_by__username',
            'action_display': 'action',
            'target_user_nom': 'target_user__username',
        },
        order_map={
            'timestamp': 'timestamp',
            'performed_by_nom': 'performed_by__username',
            'action_display': 'action',
            'target_user_nom': 'target_user__username',
            'details': 'details',
        },
        serializer=UserLogSerializer,
        default_order=('timestamp', 'desc'),
    )
