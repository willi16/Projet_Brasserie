from django.db import models
from django.contrib.auth.models import User


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
        ip = None
        if request is not None:
            xff = request.META.get('HTTP_X_FORWARDED_FOR')
            ip = xff.split(',')[0].strip() if xff else request.META.get('REMOTE_ADDR')
        return cls.objects.create(
            performed_by=performed_by if (performed_by and performed_by.is_authenticated) else None,
            target_user=target_user,
            action=action,
            module=module,
            details=details,
            ip_address=ip,
        )
