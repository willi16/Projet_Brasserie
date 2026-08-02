import os
import tempfile
import shutil
import subprocess
from pathlib import Path
from django.shortcuts import get_object_or_404
from django.utils import timezone
from django.contrib.auth.decorators import login_required
from django.http import HttpResponse, HttpResponseForbidden
from django.conf import settings
from gestion_depot.models import BonVente
from jinja2 import Environment, FileSystemLoader


def user_can_view_facture(user, bon):
    """Vérifie si l'utilisateur peut voir la facture d'un bon."""
    if user.is_superuser:
        return True
    if user.groups.filter(name__in=['Gérant', 'Admin']).exists():
        return True
    if user.groups.filter(name='Caissier').exists() and bon.vendeur == user:
        return True
    return False


def latex_escape(text):
    """Échappe les caractères spéciaux LaTeX pour éviter les injections/cassures."""
    if text is None:
        return ""
    text = str(text)
    replacements = {
        '\\': r'\textbackslash{}',
        '&': r'\&',
        '%': r'\%',
        '$': r'\$',
        '#': r'\#',
        '_': r'\_',
        '{': r'\{',
        '}': r'\}',
        '~': r'\textasciitilde{}',
        '^': r'\textasciicircum{}',
    }
    for char, escaped in replacements.items():
        text = text.replace(char, escaped)
    return text


def format_decimal(value):
    return "%.2f" % float(value)


@login_required
def generer_facture(request, id):
    bon = get_object_or_404(
        BonVente.objects.select_related('client', 'vendeur').prefetch_related('lignes__produit'),
        id=id,
    )

    if not user_can_view_facture(request.user, bon):
        return HttpResponseForbidden("Vous n'êtes pas autorisé à générer cette facture.")

    total_facture = 0
    lignes = []
    for ligne in bon.lignes.all():
        prix_unitaire = float(ligne.produit.prix_vente_casier) * float(ligne.fraction)
        montant = prix_unitaire * float(ligne.quantite_casiers)
        total_facture += montant
        lignes.append({
            'quantite_casiers': format_decimal(ligne.quantite_casiers),
            'produit_nom': latex_escape(ligne.produit.nom),
            'fraction_display': latex_escape(ligne.get_fraction_display()),
            'prix_unitaire': format_decimal(prix_unitaire),
            'montant': format_decimal(montant),
        })

    date_str = timezone.localtime().strftime("%d/%m/%Y à %Hh%M")

    template_dir = Path(settings.BASE_DIR) / 'gestion_depot' / 'templates'
    env = Environment(loader=FileSystemLoader(str(template_dir)))
    template = env.get_template('facture_jinja_template.tex')

    safe_bon = {
        'reference': latex_escape(bon.reference),
        'client_nom': latex_escape(bon.client.nom) if bon.client else 'Inconnu',
        'vendeur': latex_escape(bon.vendeur.username),
    }

    latex_content = template.render(
        bon=safe_bon,
        lignes=lignes,
        total_facture=format_decimal(total_facture),
        date_str=date_str,
    )

    # Créer un dossier temporaire dans /app pour éviter les problèmes de permissions
    with tempfile.TemporaryDirectory() as tmp_dir:
        tex_path = os.path.join(tmp_dir, f"facture_{bon.id}.tex")
        pdf_path = os.path.join(tmp_dir, f"facture_{bon.id}.pdf")
        logo_src = os.path.join(settings.BASE_DIR, 'static', 'images', 'logo.png')
        logo_dst = os.path.join(tmp_dir, "logo.png")
        cachet_src = os.path.join(settings.BASE_DIR, 'static', 'images', 'cachet.jpeg')
        cachet_dst = os.path.join(tmp_dir, "cachet.jpeg")

        # Écrire le .tex
        with open(tex_path, 'w', encoding='utf-8') as f:
            f.write(latex_content)

        # Copier le logo et le cachet
        if not os.path.exists(logo_src):
            return HttpResponse(f"Logo non trouvé : {logo_src}", status=500)
        shutil.copy(logo_src, logo_dst)

        if not os.path.exists(cachet_src):
            return HttpResponse(f"Cachet non trouvé : {cachet_src}", status=500)
        shutil.copy(cachet_src, cachet_dst)

        # Compiler LaTeX
        result = subprocess.run(
            ['pdflatex', '-interaction=nonstopmode', f"facture_{bon.id}.tex"],
            cwd=tmp_dir,
            capture_output=True,
            text=True,
        )

        if result.returncode != 0:
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
        archive_filename = f"facture_{bon.reference}_{timezone.localtime().strftime('%Y%m%d_%H%M%S')}.pdf"
        archive_path = os.path.join(facture_dir, archive_filename)

        with open(archive_path, 'wb') as f:
            f.write(pdf_data)

        bon.facture_pdf = f"factures/{archive_filename}"
        bon.date_facture_generee = timezone.now()
        bon.save(update_fields=['facture_pdf', 'date_facture_generee'])

        return response
