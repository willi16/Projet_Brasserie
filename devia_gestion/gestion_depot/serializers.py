# gestion_depot/serializers.py
from django.urls import reverse
from django.utils import timezone
from django.utils.html import escape
from rest_framework import serializers

from django.contrib.auth.models import User
from .models import Produit, Fournisseur, BonLivraison, BonVente, CasierEmporte
from .models.userActionLog import UserActionLog


def _badge(text, cls):
    return f'<span class="badge {cls}">{escape(str(text))}</span>'


def _fmt_dt(dt):
    if dt is None:
        return '-'
    return timezone.localtime(dt).strftime('%d/%m/%Y %H:%M')


def _fmt_date(dt):
    if dt is None:
        return '-'
    return timezone.localtime(dt).strftime('%d/%m/%Y')


def _user_can_manage_bon(user, bon):
    if user.is_superuser:
        return True
    if user.groups.filter(name__in=['Gérant', 'Admin']).exists():
        return True
    if user.groups.filter(name='Caissier').exists() and bon.vendeur == user:
        return True
    return False


def _peut_gerer_casiers(user):
    if user.is_superuser:
        return True
    return user.groups.filter(name__in=['Caissier', 'Gérant', 'Admin']).exists()


def _can_edit(user):
    if user.is_superuser:
        return True
    return user.groups.filter(name__in=['Gérant', 'Admin']).exists()


class ProduitSerializer(serializers.ModelSerializer):
    categorie_display = serializers.CharField(source='get_categorie_display')
    modele_display = serializers.CharField(source='get_modele_display')
    stock_actuel = serializers.FloatField()
    statut_html = serializers.SerializerMethodField()
    actions_html = serializers.SerializerMethodField()

    class Meta:
        model = Produit
        fields = [
            'id', 'nom', 'categorie_display', 'casier_contenu',
            'modele_display', 'prix_vente_casier', 'stock_actuel',
            'seuil_alerte', 'statut_html', 'actions_html',
        ]

    def _en_alerte(self, obj):
        return (obj.stock_actuel or 0) <= obj.seuil_alerte

    def get_statut_html(self, obj):
        if self._en_alerte(obj):
            return _badge('Stock bas', 'badge-warning')
        return _badge('OK', 'badge-success')

    def get_actions_html(self, obj):
        if not _can_edit(self.context['request'].user):
            return '-'
        edit_url = reverse('gestion_depot:modifier_produit', args=[obj.id])
        del_url = reverse('gestion_depot:supprimer_produit', args=[obj.id])
        return (
            f'<div class="flex gap-1">'
            f'<a href="{edit_url}" class="btn btn-sm btn-warning">Modifier</a>'
            f'<a href="{del_url}" class="btn btn-sm btn-danger confirm-delete" '
            f'data-title="Supprimer le produit" '
            f'data-text="Voulez-vous vraiment supprimer « {escape(obj.nom)} » ? Cette action est irréversible.">'
            f'Supprimer</a></div>'
        )


class FournisseurSerializer(serializers.ModelSerializer):
    actions_html = serializers.SerializerMethodField()

    class Meta:
        model = Fournisseur
        fields = ['id', 'nom', 'contact', 'adresse', 'actions_html']

    def get_actions_html(self, obj):
        edit_url = reverse('gestion_depot:modifier_fournisseur', args=[obj.id])
        del_url = reverse('gestion_depot:supprimer_fournisseur', args=[obj.id])
        return (
            f'<div class="flex gap-1">'
            f'<a href="{edit_url}" class="btn btn-sm btn-warning">Modifier</a>'
            f'<a href="{del_url}" class="btn btn-sm btn-danger confirm-delete" '
            f'data-title="Supprimer le fournisseur" '
            f'data-text="Voulez-vous vraiment supprimer « {escape(obj.nom)} » ? Cette action est irréversible.">'
            f'Supprimer</a></div>'
        )


class LivraisonSerializer(serializers.ModelSerializer):
    date_livraison = serializers.SerializerMethodField()
    fournisseur_nom = serializers.CharField(source='fournisseur.nom')
    utilisateur_nom = serializers.CharField(source='utilisateur.username')
    total_quantite = serializers.SerializerMethodField()
    total_montant = serializers.SerializerMethodField()
    actions_html = serializers.SerializerMethodField()

    class Meta:
        model = BonLivraison
        fields = [
            'id', 'reference', 'date_livraison', 'fournisseur_nom',
            'utilisateur_nom', 'total_quantite', 'total_montant', 'actions_html',
        ]

    def get_date_livraison(self, obj):
        return _fmt_dt(obj.date_livraison)

    def get_total_quantite(self, obj):
        return float(obj.total_quantite_ann or 0)

    def get_total_montant(self, obj):
        return float(obj.total_montant_ann or 0)

    def get_actions_html(self, obj):
        detail_url = reverse('gestion_depot:detail_bon_livraison', args=[obj.id])
        return f'<a href="{detail_url}" class="btn btn-sm btn-info">Détail</a>'


class BonVenteSerializer(serializers.ModelSerializer):
    date_vente = serializers.SerializerMethodField()
    client_nom = serializers.SerializerMethodField()
    vendeur_nom = serializers.CharField(source='vendeur.username')
    statut_html = serializers.SerializerMethodField()
    montant_total = serializers.SerializerMethodField()
    actions_html = serializers.SerializerMethodField()

    class Meta:
        model = BonVente
        fields = [
            'id', 'reference', 'date_vente', 'client_nom', 'vendeur_nom',
            'montant_total', 'statut_html', 'actions_html',
        ]

    def get_date_vente(self, obj):
        return _fmt_dt(obj.date_vente)

    def get_client_nom(self, obj):
        return obj.client.nom if obj.client else '-'

    def get_montant_total(self, obj):
        return round(float(obj.montant_total or 0), 0)

    def get_statut_html(self, obj):
        cls = {
            'valide': 'badge-success',
            'annule': 'badge-danger',
        }.get(obj.statut, 'badge-warning')
        return _badge(obj.get_statut_display(), cls)

    def get_actions_html(self, obj):
        user = self.context['request'].user
        csrf = self.context['csrf']
        detail_url = reverse('gestion_depot:detail_bon_vente', args=[obj.id])
        facture_url = reverse('gestion_depot:generer_facture', args=[obj.id])
        if not _user_can_manage_bon(user, obj):
            return '-'

        buttons = (
            f'<div class="flex gap-1 flex-wrap">'
            f'<a href="{detail_url}" class="btn btn-sm btn-info">Détail</a>'
            f'<a href="{facture_url}" class="btn btn-sm btn-warning">Facture</a>'
        )
        if obj.statut == 'en_cours':
            valider_url = reverse('gestion_depot:valider_bon_vente', args=[obj.id])
            buttons += (
                f'<form method="post" action="{valider_url}" class="confirm-form" '
                f'data-title="Valider le bon de vente" '
                f'data-text="Confirmer la validation du bon {escape(obj.reference)} ? Le stock sera déduit." '
                f'data-confirm-text="Valider">'
                f'<input type="hidden" name="csrfmiddlewaretoken" value="{csrf}">'
                f'<button type="submit" class="btn btn-sm btn-success">Valider</button></form>'
            )
        elif obj.statut == 'valide':
            annuler_url = reverse('gestion_depot:annuler_bon_vente', args=[obj.id])
            buttons += (
                f'<form method="post" action="{annuler_url}" class="confirm-form" '
                f'data-title="Annuler le bon de vente" '
                f'data-text="Confirmer l\'annulation du bon {escape(obj.reference)} ? Le stock sera restitué." '
                f'data-confirm-text="Oui, annuler">'
                f'<input type="hidden" name="csrfmiddlewaretoken" value="{csrf}">'
                f'<button type="submit" class="btn btn-sm btn-danger">Annuler</button></form>'
            )
        buttons += '</div>'
        return buttons


class CasierSerializer(serializers.ModelSerializer):
    client_nom = serializers.CharField(source='client.nom')
    bon_reference = serializers.SerializerMethodField()
    modele_display = serializers.CharField(source='get_modele_display')
    date_emport = serializers.SerializerMethodField()
    date_limite = serializers.SerializerMethodField()
    restant = serializers.SerializerMethodField()
    restant_bouteilles = serializers.IntegerField()
    statut = serializers.SerializerMethodField()
    statut_html = serializers.SerializerMethodField()
    sanction_html = serializers.SerializerMethodField()
    actions_html = serializers.SerializerMethodField()

    class Meta:
        model = CasierEmporte
        fields = [
            'id', 'client_nom', 'bon_reference', 'modele_display',
            'date_emport', 'date_limite', 'nombre_casiers', 'nombre_rendus',
            'restant', 'restant_bouteilles', 'statut', 'statut_html',
            'sanction_html', 'actions_html',
        ]

    def get_date_emport(self, obj):
        return _fmt_dt(obj.date_emport)

    def get_date_limite(self, obj):
        return _fmt_dt(obj.date_limite)

    def get_restant(self, obj):
        return obj.restant

    def get_statut(self, obj):
        if obj.date_retour_complet:
            return 'retourne'
        if obj.en_retard:
            return 'en_retard'
        return 'en_cours'

    def get_statut_html(self, obj):
        cls = {
            'retourne': 'badge-success',
            'en_retard': 'badge-danger',
        }.get(self.get_statut(obj), 'badge-warning')
        txt = {
            'retourne': 'Retourné',
            'en_retard': 'En retard',
        }.get(self.get_statut(obj), 'En attente')
        return _badge(txt, cls)

    def get_sanction_html(self, obj):
        if obj.en_retard:
            return f'<span class="text-red-600 font-semibold">{obj.montant_sanction} FCFA</span>'
        return '-'

    def get_actions_html(self, obj):
        if not _peut_gerer_casiers(self.context['request'].user):
            return '-'
        csrf = self.context['csrf']
        bon_url = reverse('gestion_depot:detail_bon_vente', args=[obj.bon.id])
        bon_link = (
            f'<a href="{bon_url}" class="text-brand-600 dark:text-brand-400">{escape(obj.bon.reference)}</a>'
        )
        if obj.restant > 0:
            retour_url = reverse('gestion_depot:enregistrer_retour_casiers', args=[obj.id])
            return (
                f'<div class="flex items-center gap-1">'
                f'<form method="post" action="{retour_url}" class="flex gap-1 items-end">'
                f'<input type="hidden" name="csrfmiddlewaretoken" value="{csrf}">'
                f'<input type="number" name="quantite_rendue" min="1" max="{obj.restant}" step="1" '
                f'value="{obj.restant}" class="form-input !w-20" required>'
                f'<button type="submit" class="btn btn-sm btn-success">Retour</button></form></div>'
            )
        return '-'

    def get_bon_reference(self, obj):
        bon_url = reverse('gestion_depot:detail_bon_vente', args=[obj.bon.id])
        return (
            f'<a href="{bon_url}" class="text-brand-600 dark:text-brand-400">{escape(obj.bon.reference)}</a>'
        )


class UserSerializer(serializers.ModelSerializer):
    statut_html = serializers.SerializerMethodField()
    roles_html = serializers.SerializerMethodField()
    actions_html = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = ['id', 'username', 'email', 'statut_html', 'roles_html', 'actions_html']

    def get_statut_html(self, obj):
        if obj.is_active:
            return _badge('Actif', 'badge-success')
        return _badge('Inactif', 'badge-danger')

    def get_roles_html(self, obj):
        if obj.is_superuser:
            return _badge('Superadmin', 'badge-secondary')
        groups = list(obj.groups.all())
        if not groups:
            return _badge('Aucun', 'badge-secondary')
        return ' '.join(_badge(g.name, 'badge-info') for g in groups)

    def get_actions_html(self, obj):
        user = self.context['request'].user
        csrf = self.context['csrf']
        edit_url = reverse('gestion_depot:edit_user_roles', args=[obj.id])
        action = 'deactivate' if obj.is_active else 'activate'
        cls = 'btn-warning' if obj.is_active else 'btn-success'
        label = 'Désactiver' if obj.is_active else 'Activer'
        return (
            f'<div class="flex gap-1 flex-wrap items-center">'
            f'<form method="post" action="{reverse("gestion_depot:manage_users")}">'
            f'<input type="hidden" name="csrfmiddlewaretoken" value="{csrf}">'
            f'<input type="hidden" name="user_id" value="{obj.id}">'
            f'<button type="submit" name="action" value="{action}" class="btn btn-sm {cls}">{label}</button></form>'
            f'<a href="{edit_url}" class="btn btn-sm btn-info">Modifier les rôles</a></div>'
        )


class UserLogSerializer(serializers.ModelSerializer):
    timestamp = serializers.SerializerMethodField()
    performed_by_nom = serializers.SerializerMethodField()
    action_display = serializers.CharField(source='get_action_display')
    target_user_nom = serializers.CharField(source='target_user.username')

    class Meta:
        model = UserActionLog
        fields = [
            'id', 'timestamp', 'performed_by_nom', 'action_display',
            'target_user_nom', 'details',
        ]

    def get_timestamp(self, obj):
        return _fmt_dt(obj.timestamp)

    def get_performed_by_nom(self, obj):
        return obj.performed_by.username if obj.performed_by else 'System'
