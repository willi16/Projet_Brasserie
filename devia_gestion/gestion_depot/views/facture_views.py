import os
import tempfile
import shutil
from django.shortcuts import get_object_or_404
from datetime import datetime
from django.contrib.auth.decorators import login_required
from django.http import HttpResponse, HttpResponseForbidden
from django.conf import settings
from gestion_depot.models import BonVente
from gestion_depot.decorators import group_required
from jinja2 import Environment, FileSystemLoader


def user_can_view_facture(user, bon):
    """Vérifie si l'utilisateur peut voir la facture d'un bon."""
    if user.is_superuser:
        return True
    if user.groups.filter(name__in=['Gérants','Gérant','Gerant', 'Admin']).exists():
        return True
    # Caissier : peut voir sa propre facture
    if ((user.groups.filter(name='Caissiers').exists() and bon.vendeur == user) or (user.groups.filter(name='Caissier').exists() and bon.vendeur == user)):
        return True
    return False

# @group_required('Caissiers','Caissier','Gérant','Gérants','Gerant', 'Admin')
@login_required
def generer_facture(request, id):
    bon = get_object_or_404(BonVente, id=id)

    # Vérifier les permissions
    if not user_can_view_facture(request.user, bon):
        return HttpResponseForbidden("Vous n'êtes pas autorisé à générer cette facture.")

    # Ajouter les calculs dans les lignes
    lignes = []
    total_facture = 0

    # Ajouter les calculs dans les lignes
    for ligne in bon.lignes.all():
        ligne.prix_unitaire = float(ligne.produit.prix_vente_casier) * float(ligne.fraction)
        ligne.total = ligne.prix_unitaire * float(ligne.quantite_casiers) 
        lignes.append(ligne)
        total_facture += ligne.total

    
    
    # logo_src = os.path.join(settings.BASE_DIR, 'gestion_depot', 'static', 'images', 'logo.png')
    # --- Génération LaTeX ---
    env = Environment(loader=FileSystemLoader('gestion_depot/templates'))
    template = env.get_template('facture_jinja_template.tex')

    latex_content = template.render(
        bon=bon,
        lignes=lignes,
        total_facture=total_facture,
        date=datetime.now().strftime("%d/%m/%Y")
    
    )
    # --- Création du PDF dans un dossier temporaire ---
    with tempfile.TemporaryDirectory() as tmp_dir:
        tex_path = os.path.join(tmp_dir, f"facture_{bon.id}.tex")
        pdf_path = os.path.join(tmp_dir, f"facture_{bon.id}.pdf")
        # Chemin du logo
        logo_src = os.path.join(settings.STATIC_ROOT or settings.BASE_DIR, 'gestion_depot', 'static', 'images', 'logo.png')
        

        logo_dst = os.path.join(tmp_dir, "logo.png")

        # Écrire le fichier .tex
        with open(tex_path, 'w', encoding='utf-8') as f:
            f.write(latex_content)

        # Copier le logo dans le dossier temporaire (pour que LaTeX le trouve)
        if os.path.exists(logo_src):
            
            shutil.copy(logo_src, logo_dst)

        # Compiler en PDF (silencieux)
        os.system(f'cd "{tmp_dir}" && pdflatex -interaction=nonstopmode "facture_{bon.id}.tex" > /dev/null 2>&1')

        # Vérifier que le PDF a été généré
        if not os.path.exists(pdf_path):
            return HttpResponse(
                "Erreur : le PDF n’a pas pu être généré. Vérifiez que pdflatex est installé et que le template LaTeX est valide.",
                status=500
            )
            
        # Lire le PDF
        with open(pdf_path, 'rb') as f:
            pdf_data = f.read()

        # --- Envoyer la réponse à l'utilisateur ---
        response = HttpResponse(pdf_data, content_type='application/pdf')
        filename = f"facture_{bon.reference}.pdf"
        response['Content-Disposition'] = f'attachment; filename="{filename}"'

        # --- Sauvegarder une copie dans media/factures/ ---
        facture_dir = os.path.join(settings.MEDIA_ROOT, 'factures')
        os.makedirs(facture_dir, exist_ok=True)

        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        archive_filename = f"facture_{bon.reference}_{timestamp}.pdf"
        archive_path = os.path.join(facture_dir, archive_filename)

        with open(archive_path, 'wb') as f:
            f.write(pdf_data)

        # --- Mettre à jour le modèle ---
        bon.facture_pdf = f"factures/{archive_filename}"
        bon.date_facture_generee = datetime.now()
        bon.save(update_fields=['facture_pdf', 'date_facture_generee'])

        return response
