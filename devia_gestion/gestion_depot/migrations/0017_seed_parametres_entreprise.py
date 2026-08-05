# gestion_depot/migrations/0017_seed_parametres_entreprise.py
import os
import shutil
from pathlib import Path
from django.conf import settings
from django.db import migrations


def seed_entreprise(apps, schema_editor):
    ParametresEntreprise = apps.get_model('gestion_depot', 'ParametresEntreprise')
    obj, _ = ParametresEntreprise.objects.get_or_create(pk=1)

    entreprise_dir = Path(settings.MEDIA_ROOT) / 'entreprise'
    entreprise_dir.mkdir(parents=True, exist_ok=True)

    images = {
        'logo': 'logo.png',
        'cachet': 'cachet.jpeg',
        'fond_login': 'youki.jpg',
    }

    for champ, fichier in images.items():
        if getattr(obj, champ):
            continue
        src = Path(settings.BASE_DIR) / 'static' / 'images' / fichier
        if not src.exists():
            continue
        dst = entreprise_dir / fichier
        shutil.copy(src, dst)
        setattr(obj, champ, f"entreprise/{fichier}")

    obj.save()


def undo_seed_entreprise(apps, schema_editor):
    ParametresEntreprise = apps.get_model('gestion_depot', 'ParametresEntreprise')
    ParametresEntreprise.objects.filter(pk=1).delete()


class Migration(migrations.Migration):

    dependencies = [
        ('gestion_depot', '0016_parametresentreprise'),
    ]

    operations = [
        migrations.RunPython(seed_entreprise, undo_seed_entreprise),
    ]
