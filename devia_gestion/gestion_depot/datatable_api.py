# gestion_depot/datatable_api.py
# Helper générique pour le protocole "server-side" de DataTables.
from django.db.models import Q
from django.http import JsonResponse
from django.middleware.csrf import get_token


def dt_json(request, qs, columns, searchable, order_map, serializer,
            filter_fn=None, default_order=None, search_map=None):
    """Rend la réponse JSON attendue par DataTables (mode serveur).

    - qs         : queryset de base (déjà filtré par les droits d'accès).
    - columns    : liste des clés de colonnes (dans l'ordre d'affichage).
    - searchable : liste des champs (lookups Django) sur lesquels la recherche
                   globale s'applique.
    - order_map  : dict {clé colonne: expression de tri (ou None si non triable)}.
    - serializer : classe de sérialiseur DRF (many=True, context request+csrf).
    - filter_fn  : callable(qs, request) -> qs, applique les filtres spécifiques
                   (statut, vendeur, dates, groupe...).
    - default_order : tuple (clé, 'asc'|'desc') si aucune colonne de tri.
    - search_map : dict {clé colonne: champ de recherche} pour les recherches
                   individuelles par colonne (ex. 'statut_html' -> 'statut').
    """
    draw = request.GET.get('draw', '1')
    try:
        start = int(request.GET.get('start', '0'))
    except (ValueError, TypeError):
        start = 0
    try:
        length = int(request.GET.get('length', '10'))
    except (ValueError, TypeError):
        length = 10
    if length < 0:
        length = 10

    if filter_fn:
        qs = filter_fn(qs, request)

    # Recherche globale (champ "search")
    search_value = (request.GET.get('search[value]') or '').strip()
    if search_value:
        q = Q()
        for field in searchable:
            q |= Q(**{f'{field}__icontains': search_value})
        qs = qs.filter(q)

    # Recherche individuelle par colonne (columns[i][search][value])
    for idx, col in enumerate(columns):
        col_search = request.GET.get(f'columns[{idx}][search][value]', '').strip()
        if not col_search:
            continue
        field = (search_map or {}).get(col, col)
        if field:
            qs = qs.filter(**{f'{field}__icontains': col_search})

    # Tri
    order_idx = request.GET.get('order[0][column]')
    order_dir = request.GET.get('order[0][dir]', 'asc')
    order_col = None
    if order_idx is not None:
        try:
            order_col = columns[int(order_idx)]
        except (ValueError, IndexError):
            order_col = None
    if order_col is None and default_order:
        order_col, order_dir = default_order
    if order_col is not None:
        expr = order_map.get(order_col)
        if expr is not None:
            prefix = '-' if order_dir == 'desc' else ''
            qs = qs.order_by(f'{prefix}{expr}')

    records_total = qs.count()
    page_qs = qs[start:start + length]

    context = {'request': request, 'csrf': get_token(request)}
    data = serializer(page_qs, many=True, context=context).data

    return JsonResponse({
        'draw': draw,
        'recordsTotal': records_total,
        'recordsFiltered': records_total,
        'data': data,
    })
