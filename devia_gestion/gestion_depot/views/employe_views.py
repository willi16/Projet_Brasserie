# from django.contrib.auth.models import User



# @login_required
# def voir_documents_employe(request, user_id):
#     if not request.user.is_superuser:
#         return redirect('gestion_depot:dashboard')
#     employe = get_object_or_404(User, id=user_id)
#     profil = get_object_or_404(ProfilUtilisateur, user=employe)
#     return render(request, 'gestion_depot/voir_documents.html', {'employe': employe, 'profil': profil})

# @login_required
# def liste_employes(request):
#     if not request.user.is_superuser:
#         return redirect('gestion_depot:dashboard')
#     employes = User.objects.filter(is_superuser=False)
#     return render(request, 'gestion_depot/liste_employes.html', {'employes': employes})





from django.http import HttpResponse, Http404
from django.conf import settings
import os
from django.contrib.auth.decorators import login_required

@login_required
def serve_protected_document(request, path):
    full_path = os.path.join(settings.MEDIA_ROOT, path)
    if os.path.exists(full_path):
        with open(full_path, 'rb') as f:
            response = HttpResponse(f.read(), content_type="image/jpeg")
            response['Content-Disposition'] = f'inline; filename={os.path.basename(full_path)}'
            return response
    raise Http404()