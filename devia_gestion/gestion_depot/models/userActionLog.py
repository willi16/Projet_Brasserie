from django.db import models
from django.contrib.auth.models import User


def _get_client_ip(request):
    """Retourne l'IP du client de manière sûre (valide et propre)."""
    if request is None:
        return None
    xff = request.META.get('HTTP_X_FORWARDED_FOR')
    if xff:
        candidate = xff.split(',')[0].strip()
    else:
        candidate = request.META.get('REMOTE_ADDR')
    if not candidate:
        return None
    try:
        import ipaddress
        return str(ipaddress.ip_address(candidate))
    except ValueError:
        return None


class UserActionLog(models.Model):
    performed_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        related_name='performed_actions'
    )
    target_user = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='action_logs'
    )
    action = models.CharField(max_length=50)
    module = models.CharField(max_length=50, blank=True)
    details = models.TextField(blank=True)
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    timestamp = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-timestamp']

    def __str__(self):
        return f"{self.performed_by or 'System'} → {self.action} → {self.target_user or '-'}"

    @classmethod
    def log_action(cls, performed_by, action, details='', module='', target_user=None, request=None):
        """Enregistre une action utilisateur dans le journal d'activité."""
        ip = _get_client_ip(request)
        return cls.objects.create(
            performed_by=performed_by if (performed_by and performed_by.is_authenticated) else None,
            target_user=target_user,
            action=action,
            module=module,
            details=details,
            ip_address=ip,
        )
