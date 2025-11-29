import os
import tempfile
from django.shortcuts import get_object_or_404
from django.contrib.auth.decorators import login_required
from django.http import HttpResponse
from django.conf import settings
from gestion_depot.models import BonVente
from gestion_depot.decorators import group_required
from jinja2 import Environment, FileSystemLoader

@group_required('Gérant', 'Admin')
@login_required
def generer_facture(request, id):
    bon = get_object_or_404(BonVente, id=id)

    # Ajouter les calculs dans les lignes
    lignes = []
    total_facture = 0

    # Ajouter les calculs dans les lignes
    for ligne in bon.lignes.all():
        ligne.prix_unitaire = float(ligne.produit.prix_vente_casier) * float(ligne.fraction)
        ligne.total = ligne.prix_unitaire * float(ligne.quantite_casiers) 
        lignes.append(ligne)
        total_facture += ligne.total


    # Chemin du logo
    logo_path = os.path.join(settings.BASE_DIR, 'gestion_depot', 'static', 'images', 'logo.png')

    # Charger le template Jinja2
    env = Environment(loader=FileSystemLoader('gestion_depot/templates'))
    template = env.get_template('facture_jinja_template.tex')

    # Rendu du template
    latex_content = template.render(bon=bon)

    # Créer un fichier temporaire
    with tempfile.NamedTemporaryFile(mode='w', suffix='.tex', delete=False, encoding='utf-8') as f:
        f.write(latex_content)
        tex_file = f.name

    # Compiler en PDF
    os.system(f'pdflatex -interaction=nonstopmode -output-directory={os.path.dirname(tex_file)} {tex_file}')

    # Lire le PDF
    pdf_file = tex_file.replace('.tex', '.pdf')
    try:
        with open(pdf_file, 'rb') as f:
            response = HttpResponse(f.read(), content_type='application/pdf')
            response['Content-Disposition'] = f'attachment; filename="facture_{bon.reference}.pdf"'
            return response
    except FileNotFoundError:
        return HttpResponse("Erreur : le PDF n’a pas pu être généré. Vérifie que pdflatex est installé.", status=500)