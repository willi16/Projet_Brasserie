from decimal import Decimal, InvalidOperation
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.views.decorators.http import require_POST
from django.contrib import messages
from django.db import transaction
from django.db.models import Sum, Case, When, F, FloatField
from django.contrib.auth.models import User
from datetime import datetime

from gestion_depot.models import BonVente, Client, LigneVente, Produit, Mouvement
from gestion_depot.views.casier_views import produit_casier_du_bon


FRACTION_MIN = Decimal('0.25')
FRACTION_MAX = Decimal('9.99')
TYPES_PAIEMENT_VALIDES = {'especes', 'credit'}


def stocks_disponibles(produits):
    """Retourne un dict {id_produit: stock} pour les produits donnés (1 requête)."""
    ids = [p.id for p in produits]
    rows = Produit.objects.filter(id__in=ids).annotate(
        stock=Sum(
            Case(
                When(mouvement__type_mouvement='entree', then=F('mouvement__quantite_casiers')),
                When(mouvement__type_mouvement='sortie', then=-F('mouvement__quantite_casiers')),
                default=0,
                output_field=FloatField(),
            )
        )
    ).values_list('id', 'stock')
    return {pid: (stock or 0) for pid, stock in rows}


@login_required
@transaction.atomic
def creer_bon_vente(request):
    if request.method == 'POST':
        client_nom = (request.POST.get('client_nom') or '').strip()
        type_paiement = request.POST.get('type_paiement')

        produits = request.POST.getlist('produit')
        fractions = request.POST.getlist('fraction')
        quantites = request.POST.getlist('quantite')

        # Vérifier que les listes ne sont pas vides
        if not produits or not all(quantites):
            messages.error(request, "Veuillez remplir tous les champs du formulaire.")
            return redirect('gestion_depot:creer_bon_vente')

        if not client_nom:
            messages.error(request, "Le nom du client est obligatoire.")
            return redirect('gestion_depot:creer_bon_vente')

        if type_paiement not in TYPES_PAIEMENT_VALIDES:
            messages.error(request, "Type de paiement invalide.")
            return redirect('gestion_depot:creer_bon_vente')

        # Convertir et valider les données
        try:
            produit_ids = [int(p) for p in produits]
            quantites_dec = [Decimal(q) for q in quantites]
            fractions_dec = [Decimal(f) for f in fractions]
        except (ValueError, TypeError, InvalidOperation):
            messages.error(request, "Données de quantité ou fraction invalides.")
            return redirect('gestion_depot:creer_bon_vente')

        for f in fractions_dec:
            if not (FRACTION_MIN <= f <= FRACTION_MAX):
                messages.error(request, f"Fraction invalide. Valeur comprise entre {FRACTION_MIN} et {FRACTION_MAX}.")
                return redirect('gestion_depot:creer_bon_vente')

        # Récupérer les produits en une seule requête
        produits_dict = Produit.objects.in_bulk(produit_ids)
        stocks = stocks_disponibles(produits_dict.values())

        # Vérifier les droits de l'utilisateur (admin ou gérant ?)
        is_admin_or_gestionnaire = request.user.is_superuser or request.user.groups.filter(
            name__in=['Admin', 'Gérant']
        ).exists()

        # Vérification du stock ET du seuil
        for p_id, f, q in zip(produit_ids, fractions_dec, quantites_dec):
            prod = produits_dict.get(p_id)
            if not prod:
                messages.error(request, "Produit introuvable.")
                return redirect('gestion_depot:creer_bon_vente')

            quantite_totale = f * q

            if quantite_totale <= 0:
                messages.error(
                    request,
                    f"La quantité saisie pour {prod.nom} est invalide (fraction : {f}, casiers : {q})."
                )
                return redirect('gestion_depot:creer_bon_vente')

            stock = stocks.get(p_id, 0)

            # Stock insuffisant → bloquer pour tous
            if quantite_totale > stock:
                messages.error(
                    request,
                    f"Stock insuffisant pour {prod.nom}. Disponible : {stock}, demandé : {quantite_totale:.2f}"
                )
                return redirect('gestion_depot:creer_bon_vente')

            # Quantité ≥ seuil → autorisé uniquement à admin/gérant
            if quantite_totale >= prod.seuil_alerte and not is_admin_or_gestionnaire:
                messages.warning(
                    request,
                    f"La quantité demandée pour {prod.nom} ({quantite_totale:.2f}) atteint ou dépasse le seuil ({prod.seuil_alerte}). "
                    "Seul un admin ou un gérant peut effectuer cette vente."
                )
                return redirect('gestion_depot:creer_bon_vente')

        # Tout est OK → Créer le client
        client_obj, _ = Client.objects.get_or_create(nom=client_nom)

        # Créer le bon de vente (statut 'en_cours', validé ensuite)
        bon = BonVente.objects.create(
            client=client_obj,
            type_paiement=type_paiement,
            vendeur=request.user,
            statut='en_cours',
        )

        # Créer les lignes de vente
        lignes = []
        for p_id, f, q in zip(produit_ids, fractions_dec, quantites_dec):
            prod = produits_dict.get(p_id)
            if prod:
                lignes.append(
                    LigneVente(
                        bon=bon,
                        produit=prod,
                        fraction=f,
                        quantite_casiers=q,
                    )
                )
        LigneVente.objects.bulk_create(lignes)

        messages.success(request, f"Bon de vente {bon.reference} créé avec succès !")
        return redirect('gestion_depot:liste_bons_vente')

    # GET request
    produits = Produit.objects.annotate(
        stock_actuel=Sum(
            Case(
                When(mouvement__type_mouvement='entree', then=F('mouvement__quantite_casiers')),
                When(mouvement__type_mouvement='sortie', then=-F('mouvement__quantite_casiers')),
                default=0,
                output_field=FloatField(),
            )
        )
    )
    return render(request, 'gestion_depot/creer_bon_vente.html', {'produits': produits})


def user_can_manage_bon(user, bon):
    """Vérifie si l'utilisateur peut gérer ce bon de vente."""
    if user.is_superuser:
        return True
    if user.groups.filter(name__in=['Gérant', 'Admin']).exists():
        return True
    if user.groups.filter(name='Caissier').exists() and bon.vendeur == user:
        return True
    return False


@login_required
@require_POST
@transaction.atomic
def valider_bon_vente(request, id):
    bon = get_object_or_404(BonVente, id=id)

    if not user_can_manage_bon(request.user, bon):
        messages.error(request, "Vous n'êtes pas autorisé à valider cette vente.")
        return redirect('gestion_depot:liste_bons_vente')

    if bon.statut != 'valide':
        # Vérifier à nouveau le stock (au cas où changé entre-temps)
        for ligne in bon.lignes.select_related('produit'):
            if ligne.produit.stock_disponible() < (ligne.fraction * ligne.quantite_casiers):
                messages.error(request, f"Stock insuffisant pour {ligne.produit.nom} au moment de la validation.")
                return redirect('gestion_depot:liste_bons_vente')

        # Créer les mouvements de sortie
        for ligne in bon.lignes.all():
            Mouvement.objects.create(
                produit=ligne.produit,
                type_mouvement='sortie',
                quantite_casiers=ligne.quantite_casiers,
                utilisateur=request.user,
                ligne_vente=ligne,
            )
        bon.statut = 'valide'
        bon.save(update_fields=['statut'])
        messages.success(request, f"Le bon de vente {bon.reference} a été validé.")
    else:
        messages.warning(request, "Ce bon est déjà validé.")

    return redirect('gestion_depot:liste_bons_vente')


@login_required
@require_POST
@transaction.atomic
def annuler_bon_vente(request, id):
    bon = get_object_or_404(BonVente, id=id)

    if not user_can_manage_bon(request.user, bon):
        messages.error(request, "Vous n'êtes pas autorisé à annuler cette vente.")
        return redirect('gestion_depot:liste_bons_vente')

    if bon.statut == 'valide':
        # Créer des mouvements inverses (entrée)
        for ligne in bon.lignes.all():
            Mouvement.objects.create(
                produit=ligne.produit,
                type_mouvement='entree',
                quantite_casiers=ligne.quantite_casiers,
                utilisateur=request.user,
                fournisseur=None,
            )
        bon.statut = 'annule'
        bon.save(update_fields=['statut'])
        messages.success(request, f"Le bon de vente {bon.reference} a été annulé et le stock restauré.")
    else:
        messages.warning(request, "Ce bon n’est pas encore validé ou est déjà annulé.")

    return redirect('gestion_depot:liste_bons_vente')


@login_required
def liste_bons_vente(request):
    # Vérifie si l'utilisateur est caissier
    is_caissier = request.user.groups.filter(name='Caissier').exists()

    if is_caissier:
        bons = BonVente.objects.filter(vendeur=request.user)
    else:
        bons = BonVente.objects.all()

    # Filtres (ne s'appliquent qu'aux données déjà filtrées)
    statut = request.GET.get('statut')
    vendeur_id = request.GET.get('vendeur') if not is_caissier else None
    date_debut = request.GET.get('date_debut')
    date_fin = request.GET.get('date_fin')

    if statut:
        bons = bons.filter(statut=statut)
    if vendeur_id and not is_caissier:  # Un caissier ne peut pas filtrer par vendeur
        bons = bons.filter(vendeur_id=vendeur_id)
    if date_debut:
        bons = bons.filter(date_vente__gte=date_debut)
    if date_fin:
        try:
            date_fin_complet = datetime.strptime(date_fin, '%Y-%m-%d').replace(hour=23, minute=59, second=59)
            bons = bons.filter(date_vente__lte=date_fin_complet)
        except ValueError:
            pass

    bons = bons.select_related('client', 'vendeur').annotate(
        montant_total=Sum(
            F('lignes__produit__prix_vente_casier') * F('lignes__fraction') * F('lignes__quantite_casiers'),
            output_field=FloatField(),
        )
    ).order_by('-date_vente')

    vendeurs = User.objects.all()

    return render(request, 'gestion_depot/liste_bons_vente.html', {
        'bons': bons,
        'vendeurs': vendeurs,
        'statut_filter': statut,
        'vendeur_filter': vendeur_id,
        'date_debut': date_debut,
        'date_fin': date_fin,
        'is_caissier': is_caissier,
    })


@login_required
def detail_bon_vente(request, id):
    bon = get_object_or_404(
        BonVente.objects.select_related('client', 'vendeur').prefetch_related('lignes__produit'),
        id=id,
    )

    if not user_can_manage_bon(request.user, bon):
        messages.error(request, "Vous n'êtes pas autorisé à consulter cette vente.")
        return redirect('gestion_depot:liste_bons_vente')

    return render(request, 'gestion_depot/detail_bon_vente.html', {
        'bon': bon,
        'produit_casier': produit_casier_du_bon(bon),
    })
