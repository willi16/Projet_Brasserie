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


# ---------------------------------------------------------------------------
# Icônes SVG (style Heroicons outline, stroke 24x24) pour les boutons d'action
# ---------------------------------------------------------------------------
_SVG_VIEW = 'M15 12a3 3 0 11-6 0 3 3 0 016 0zM2.458 12C3.732 7.943 7.523 5 12 5c4.478 0 8.268 2.943 9.542 7-1.274 4.057-5.064 7-9.542 7-4.477 0-8.268-2.943-9.542-7z'
_SVG_EDIT = 'M11 5H6a2 2 0 00-2 2v11a2 2 0 002 2h11a2 2 0 002-2v-5m-1.414-9.414a2 2 0 112.828 2.828L11.828 15H9v-2.828l8.586-8.586z'
_SVG_DELETE = 'M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16'
_SVG_VALIDATE = 'M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z'
_SVG_CANCEL = 'M10 14l2-2m0 0l2-2m-2 2l-2-2m2 2l2 2m7-2a9 9 0 11-18 0 9 9 0 0118 0z'
_SVG_RECEIPT = 'M9 14l6 0m-6-4h6M9 19h6M5 21V3h14v18l-2-1.5L15 21l-2-1.5L11 21l-2-1.5L7 21l-2 0z'
_SVG_BACK = 'M10 19l-7-7m0 0l7-7m-7 7h18'
_SVG_ROLES = 'M17 20h5v-2a3 3 0 00-5.356-1.857M17 20H7m10 0v-2c0-.656-.126-1.283-.356-1.857M7 20H2v-2a3 3 0 015.356-1.857M7 20v-2c0-.656.126-1.283.356-1.857m0 0a5.002 5.002 0 019.288 0M15 7a3 3 0 11-6 0 3 3 0 016 0zm6 3a2 2 0 11-4 0 2 2 0 014 0zM7 10a2 2 0 11-4 0 2 2 0 014 0z'


def _icon_svg(path):
    return (
        f'<svg xmlns="http://www.w3.org/2000/svg" class="action-svg" fill="none" '
        f'viewBox="0 0 24 24" stroke="currentColor" stroke-width="2" aria-hidden="true">'
        f'<path stroke-linecap="round" stroke-linejoin="round" d="{path}"/></svg>'
    )


def _action_link(url, label, kind, path, cls='', data=''):
    tip = escape(label)
    classes = ' '.join(x for x in ('action-btn', f'action-{kind}', cls) if x)
    extra = f' class="{classes}" data-tooltip="{tip}"'
    if data:
        extra += f' {data}'
    return f'<a href="{url}"{extra}>{_icon_svg(path)}<span class="action-tip">{tip}</span></a>'


def _action_submit(label, kind, path):
    tip = escape(label)
    return (
        f'<button type="submit" class="action-btn action-{kind}" data-tooltip="{tip}" aria-label="{tip}">'
        f'{_icon_svg(path)}<span class="action-tip">{tip}</span></button>'
    )


def _action_form(url, csrf, label, kind, path, data='', extra_inputs=''):
    return (
        f'<form method="post" action="{url}" {data}>'
        f'<input type="hidden" name="csrfmiddlewaretoken" value="{csrf}">'
        f'{extra_inputs}'
        f'{_action_submit(label, kind, path)}</form>'
    )


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
        del_data = (
            f'data-title="Supprimer le produit" '
            f'data-text="Voulez-vous vraiment supprimer « {escape(obj.nom)} » ? Cette action est irréversible."'
        )
        return (
            f'<div class="flex items-center gap-0.5">'
            f'{_action_link(edit_url, "Modifier", "edit", _SVG_EDIT)}'
            f'{_action_link(del_url, "Supprimer", "delete", _SVG_DELETE, cls="confirm-delete", data=del_data)}'
            f'</div>'
        )


class FournisseurSerializer(serializers.ModelSerializer):
    actions_html = serializers.SerializerMethodField()

    class Meta:
        model = Fournisseur
        fields = ['id', 'nom', 'contact', 'adresse', 'actions_html']

    def get_actions_html(self, obj):
        edit_url = reverse('gestion_depot:modifier_fournisseur', args=[obj.id])
        del_url = reverse('gestion_depot:supprimer_fournisseur', args=[obj.id])
        del_data = (
            f'data-title="Supprimer le fournisseur" '
            f'data-text="Voulez-vous vraiment supprimer « {escape(obj.nom)} » ? Cette action est irréversible."'
        )
        return (
            f'<div class="flex items-center gap-0.5">'
            f'{_action_link(edit_url, "Modifier", "edit", _SVG_EDIT)}'
            f'{_action_link(del_url, "Supprimer", "delete", _SVG_DELETE, cls="confirm-delete", data=del_data)}'
            f'</div>'
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
        return _action_link(detail_url, 'Détail', 'view', _SVG_VIEW)


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
            f'<div class="flex items-center gap-0.5">'
            f'{_action_link(detail_url, "Détail", "view", _SVG_VIEW)}'
            f'{_action_link(facture_url, "Facture", "doc", _SVG_RECEIPT)}'
        )
        if obj.statut == 'en_cours':
            valider_url = reverse('gestion_depot:valider_bon_vente', args=[obj.id])
            data_text = f"Confirmer la validation du bon {escape(obj.reference)} ? Le stock sera déduit."
            data = f'class="confirm-form" data-title="Valider le bon de vente" data-text="{data_text}" data-confirm-text="Valider"'
            buttons += _action_form(valider_url, csrf, 'Valider', 'validate', _SVG_VALIDATE, data=data)
        elif obj.statut == 'valide':
            annuler_url = reverse('gestion_depot:annuler_bon_vente', args=[obj.id])
            data_text = f"Confirmer l'annulation du bon {escape(obj.reference)} ? Le stock sera restitué."
            data = f'class="confirm-form" data-title="Annuler le bon de vente" data-text="{data_text}" data-confirm-text="Oui, annuler"'
            buttons += _action_form(annuler_url, csrf, 'Annuler', 'cancel', _SVG_CANCEL, data=data)
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
                f'<form method="post" action="{retour_url}" class="flex gap-1 items-center">'
                f'<input type="hidden" name="csrfmiddlewaretoken" value="{csrf}">'
                f'<input type="number" name="quantite_rendue" min="1" max="{obj.restant}" step="1" '
                f'value="{obj.restant}" class="form-input !w-16 !py-1" required>'
                f'{_action_submit("Retour", "validate", _SVG_BACK)}'
                f'</form></div>'
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
        label = 'Désactiver' if obj.is_active else 'Activer'
        kind = 'cancel' if obj.is_active else 'validate'
        path = _SVG_CANCEL if obj.is_active else _SVG_VALIDATE
        inputs = (
            f'<input type="hidden" name="user_id" value="{obj.id}">'
            f'<input type="hidden" name="action" value="{action}">'
        )
        return (
            f'<div class="flex items-center gap-0.5">'
            f'{_action_form(reverse("gestion_depot:manage_users"), csrf, label, kind, path, extra_inputs=inputs)}'
            f'{_action_link(edit_url, "Rôles", "edit", _SVG_ROLES)}'
            f'</div>'
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
