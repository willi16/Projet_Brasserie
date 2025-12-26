import os
import tempfile
import shutil
from django.shortcuts import get_object_or_404
from datetime import datetime
from django.contrib.auth.decorators import login_required
from django.http import HttpResponse, HttpResponseForbidden
from django.conf import settings
from gestion_depot.models import BonVente
from jinja2 import Environment, FileSystemLoader


def user_can_view_facture(user, bon):
    """Vérifie si l'utilisateur peut voir la facture d'un bon."""
    if user.is_superuser:
        return True
    if user.groups.filter(name__in=['Gérant','Admin']).exists():
        return True
    if user.groups.filter(name='Caissier').exists() and bon.vendeur == user:
        return True
    return False


def safe_str(text):
    """Convertit n'importe quel objet en chaîne UTF-8 sûre."""
    if text is None:
        return ""
    try:
        # Convertir en str, puis en UTF-8, puis en str à nouveau
        return str(text).encode('utf-8', errors='replace').decode('utf-8')
    except Exception:
        return str(text).encode('latin1', errors='replace').decode('latin1')


@login_required
def generer_facture(request, id):
    bon = get_object_or_404(BonVente, id=id)

    if not user_can_view_facture(request.user, bon):
        return HttpResponseForbidden("Vous n'êtes pas autorisé à générer cette facture.")
    

    lignes = []
    total_facture = 0
    for ligne in bon.lignes.all():
        ligne.prix_unitaire = float(ligne.produit.prix_vente_casier) * float(ligne.fraction)
        ligne.total = ligne.prix_unitaire * float(ligne.quantite_casiers)
        lignes.append(ligne)
        total_facture += ligne.total

    # Date formatée depuis Python
    date_str = datetime.now().strftime("%d/%m/%Y à %Hh%M")

    env = Environment(loader=FileSystemLoader('gestion_depot/templates'))
    template = env.get_template('facture_jinja_template.tex')
    
        # Avant le render, nettoyez les données
    safe_bon = {
        'reference': safe_str(bon.reference),
        'client': {
            'nom': safe_str(bon.client.nom) if bon.client else 'Inconnu'
        },
        'vendeur': {
            'username': safe_str(bon.vendeur.username)
        },
        'lignes': [
            {
                'quantite_casiers': "%.2f" % float(ligne.quantite_casiers),
                'produit': {
                    'nom': safe_str(ligne.produit.nom),
                    'prix_vente_casier': float(ligne.produit.prix_vente_casier),
                },
                'fraction': safe_str(ligne.get_fraction_display()),
                'prix_total': "%.2f" % ligne.prix_total(),
            }
            for ligne in bon.lignes.all()
        ],
        'total': "%.2f" % total_facture,
    }

    # Passez les données nettoyées au template
    
    
    latex_content = template.render(
        bon=safe_bon,
        lignes=lignes,
        total_facture=total_facture,
        date_str=date_str
    )

    # Créer un dossier temporaire dans /app pour éviter les problèmes de permissions
    with tempfile.TemporaryDirectory() as tmp_dir:
        tex_path = os.path.join(tmp_dir, f"facture_{bon.id}.tex")
        pdf_path = os.path.join(tmp_dir, f"facture_{bon.id}.pdf")
        logo_src = os.path.join(settings.BASE_DIR, 'static', 'images', 'logo.png')
        logo_dst = os.path.join(tmp_dir, "logo.png")

        # Écrire le .tex
        with open(tex_path, 'w', encoding='utf-8') as f:
            f.write(latex_content)

        # Copier le logo
        if not os.path.exists(logo_src):
            return HttpResponse(f"Logo non trouvé : {logo_src}", status=500)
        shutil.copy(logo_src, logo_dst)

        # Compiler LaTeX
        result = os.system(f'cd "{tmp_dir}" && pdflatex -interaction=nonstopmode "facture_{bon.id}.tex"')

        if result != 0:
            log_path = os.path.join(tmp_dir, f"facture_{bon.id}.log")
            if os.path.exists(log_path):
                try:
                    with open(log_path, 'r', encoding='utf-8', errors='replace') as f:
                        log_content = f.read()
                except Exception:
                    with open(log_path, 'rb') as f:
                        log_content = f.read().decode('utf-8', errors='replace')
                return HttpResponse(
                    f"Erreur LaTeX :\n{log_content}",
                    status=500,
                    content_type="text/plain"
                )
            else:
                return HttpResponse("Compilation LaTeX échouée sans log.", status=500)

        if not os.path.exists(pdf_path):
            return HttpResponse("PDF non généré.", status=500)

        # Lire le PDF
        try:
            with open(pdf_path, 'rb') as f:
                pdf_data = f.read()
        except Exception as e:
            return HttpResponse(f"Erreur lecture PDF : {e}", status=500)

        # Réponse HTTP
        response = HttpResponse(pdf_data, content_type='application/pdf')
        filename = f"facture_{bon.reference}.pdf"
        response['Content-Disposition'] = f'attachment; filename="{filename}"'

        # Sauvegarder copie
        facture_dir = os.path.join(settings.MEDIA_ROOT, 'factures')
        os.makedirs(facture_dir, exist_ok=True)
        archive_filename = f"facture_{bon.reference}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf"
        archive_path = os.path.join(facture_dir, archive_filename)

        with open(archive_path, 'wb') as f:
            f.write(pdf_data)

        bon.facture_pdf = f"factures/{archive_filename}"
        bon.date_facture_generee = datetime.now()
        bon.save(update_fields=['facture_pdf', 'date_facture_generee'])

        return response

