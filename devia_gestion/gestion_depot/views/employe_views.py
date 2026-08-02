from pathlib import Path
from mimetypes import guess_type
from django.http import HttpResponse, Http404
from django.conf import settings
from django.contrib.auth.decorators import login_required


@login_required
def serve_protected_document(request, path):
    media_root = Path(settings.MEDIA_ROOT).resolve()
    full_path = (media_root / path).resolve()

    if not full_path.is_relative_to(media_root) or not full_path.is_file():
        raise Http404()

    content_type, _ = guess_type(full_path.name) or ("application/octet-stream",)
    with open(full_path, 'rb') as f:
        response = HttpResponse(f.read(), content_type=content_type)
        response['Content-Disposition'] = f'inline; filename={full_path.name}'
        return response
