from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import User
from .models import ProfilUtilisateur
from django.contrib.auth.models import Group

class CreerCompteEmployeForm(UserCreationForm):
    email = forms.EmailField(required=True)
    nom_complet = forms.CharField(max_length=100, required=True, label="Nom complet")
    telephone = forms.CharField(max_length=15, required=True, label="Téléphone")
    adresse = forms.CharField(widget=forms.Textarea, required=True, label="Adresse")
    date_naissance = forms.DateField(
        widget=forms.DateInput(attrs={'type': 'date'}),
        required=True,
        label="Date de naissance"
    )
    statut_marital = forms.ChoiceField(
        choices=[('', '--- Sélectionnez ---')] + ProfilUtilisateur._meta.get_field('statut_marital').choices,
        required=False,
        label="Statut marital"
    )
    role = forms.ChoiceField(
        choices=[('caissier', 'Caissier'), ('gerant', 'Gérant')],
        required=True,
        label="Rôle"
    )
    photo = forms.ImageField(required=False, label="Photo de profil")
    carte_id_recto = forms.ImageField(required=False, label="Carte d'identité - Recto")
    carte_id_verso = forms.ImageField(required=False, label="Carte d'identité - Verso")
    
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field_name, field in self.fields.items():
            # Si c'est un widget avec input_type (ex: TextInput, PasswordInput, etc.)
            if hasattr(field.widget, 'input_type'):
                if field.widget.input_type == 'checkbox':
                    field.widget.attrs.update({'class': 'form-check-input'})
                else:
                    field.widget.attrs.update({
                        'class': 'form-control',
                        'placeholder': field.label,
                    })
            else:
                # Pour les widgets sans input_type (comme Textarea, Select, etc.)
                field.widget.attrs.update({
                    'class': 'form-control',
                    'placeholder': field.label,
                })

    class Meta:
        model = User
        fields = ['username', 'email', 'password1', 'password2']


    def clean(self):
        cleaned_data = super().clean()
        recto = cleaned_data.get('carte_id_recto')
        verso = cleaned_data.get('carte_id_verso')

        if not recto or not verso:
            raise forms.ValidationError(
                "Veuillez uploader les deux côtés de la carte d'identité (recto et verso).",
                code='missing_id_card'
            )
        return cleaned_data


    def save(self, commit=True):
        user = super().save(commit=False)
        user.email = self.cleaned_data['email']
        if commit:
            user.save()
            # Créer le profil utilisateur
            profil, created = ProfilUtilisateur.objects.get_or_create(
                user=user,
                defaults={
                    'telephone': self.cleaned_data['telephone'],
                    'adresse': self.cleaned_data['adresse'],
                    'date_naissance': self.cleaned_data['date_naissance'],
                    'statut_marital': self.cleaned_data['statut_marital'],
                    'photo': self.cleaned_data['photo'],
                    'carte_id_recto': self.cleaned_data['carte_id_recto'],
                    'carte_id_verso': self.cleaned_data['carte_id_verso']
                }
            )
            
            if not created:
                # Si le profil existe déjà, mettez à jour les champs
                profil.telephone = self.cleaned_data['telephone']
                profil.adresse = self.cleaned_data['adresse']
                profil.date_naissance = self.cleaned_data['date_naissance']
                profil.statut_marital = self.cleaned_data['statut_marital']
                if self.cleaned_data['photo']:
                    profil.photo = self.cleaned_data['photo']
                if self.cleaned_data['carte_id_recto']:
                    profil.carte_id_recto = self.cleaned_data['carte_id_recto']
                if self.cleaned_data['carte_id_verso']:
                    profil.carte_id_verso = self.cleaned_data['carte_id_verso']
                profil.save()
            # Optionnel : assigner un rôle via un groupe ou un champ
            if self.cleaned_data['role'] == 'caissier':
                user.groups.add(Group.objects.get(name='Caissiers'))
            elif self.cleaned_data['role'] == 'gerant':
                user.groups.add(Group.objects.get(name='Gérants'))
        return user