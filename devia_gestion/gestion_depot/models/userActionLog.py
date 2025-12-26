from django.db import models
from django.contrib.auth.models import User

class UserActionLog(models.Model):
    ACTION_CHOICES = [
        ('activate', 'Activation'),
        ('deactivate', 'Désactivation'),
        ('role_change', 'Modification des rôles'),
    ]
    performed_by = models.ForeignKey(
        User, 
        on_delete=models.SET_NULL, 
        null=True, 
        related_name='performed_actions'
    )
    target_user = models.ForeignKey(
        User, 
        on_delete=models.CASCADE, 
        related_name='action_logs'
    )
    action = models.CharField(max_length=20, choices=ACTION_CHOICES)
    timestamp = models.DateTimeField(auto_now_add=True)
    details = models.TextField(blank=True)  # utile pour les changements de rôle

    def __str__(self):
        return f"{self.performed_by or 'System'} → {self.action} → {self.target_user}"