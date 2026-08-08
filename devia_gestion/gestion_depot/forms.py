from django import forms
from django.contrib.auth.forms import UserCreationForm, AuthenticationForm
from django.contrib.auth.models import User
from crispy_forms.helper import FormHelper
from .models import ProfilUtilisateur, Produit, Fournisseur, ParametresEntreprise
from .models.produit import CASIERS_PAR_CATEGORIE
from django.contrib.auth.models import Group


class LoginForm(AuthenticationForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.helper = FormHelper()
        self.helper.form_tag = False
        self.fields['username'].widget.attrs['placeholder'] = "Nom d'utilisateur"
        self.fields['password'].widget.attrs['placeholder'] = "Mot de passe"

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
        self.helper = FormHelper()
        self.helper.form_tag = False
        for field in self.fields.values():
            if not field.widget.attrs.get('placeholder'):
                field.widget.attrs['placeholder'] = field.label
            css = 'form-select' if isinstance(field.widget, forms.Select) else 'form-input'
            field.widget.attrs['class'] = css
        for nom in ('username', 'email', 'password1', 'password2', 'nom_complet',
                    'telephone', 'adresse', 'date_naissance', 'role',
                    'carte_id_recto', 'carte_id_verso'):
            self.fields[nom].widget.attrs['required'] = 'required'

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
                user.groups.add(Group.objects.get(name='Caissier'))
            elif self.cleaned_data['role'] == 'gerant':
                user.groups.add(Group.objects.get(name='Gérant'))
        return user


class ProduitForm(forms.ModelForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.helper = FormHelper()
        self.helper.form_tag = False

    def clean(self):
        cleaned_data = super().clean()
        categorie = cleaned_data.get('categorie')
        casier_contenu = cleaned_data.get('casier_contenu')
        if categorie and casier_contenu is not None:
            valeurs_autorisees = CASIERS_PAR_CATEGORIE.get(categorie, [])
            if valeurs_autorisees and casier_contenu not in valeurs_autorisees:
                raise forms.ValidationError(
                    f"Le contenu du casier ({casier_contenu} bouteilles) n'est pas valide "
                    f"pour la catégorie « {categorie} ». Valeurs autorisées : {', '.join(map(str, valeurs_autorisees))}."
                )
        return cleaned_data

    class Meta:
        model = Produit
        fields = ['nom', 'categorie', 'casier_contenu', 'pourcentage_prix_vente', 'seuil_alerte']
        widgets = {
            'nom': forms.TextInput(attrs={'placeholder': "Nom du produit"}),
            'pourcentage_prix_vente': forms.NumberInput(attrs={'step': '0.01', 'min': '0'}),
            'seuil_alerte': forms.NumberInput(attrs={'min': '0'}),
        }


class FournisseurForm(forms.ModelForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.helper = FormHelper()
        self.helper.form_tag = False

    class Meta:
        model = Fournisseur
        fields = ['nom', 'contact', 'adresse']
        widgets = {
            'nom': forms.TextInput(attrs={'placeholder': "Nom du fournisseur"}),
            'contact': forms.TextInput(attrs={'placeholder': "Téléphone"}),
            'adresse': forms.TextInput(attrs={'placeholder': "Adresse"}),
        }


class ProfilForm(forms.ModelForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.helper = FormHelper()
        self.helper.form_tag = False

    class Meta:
        model = ProfilUtilisateur
        fields = ['telephone', 'adresse', 'photo']
        widgets = {
            'telephone': forms.TextInput(attrs={'placeholder': "Téléphone"}),
            'adresse': forms.Textarea(attrs={'rows': 3, 'placeholder': "Adresse"}),
            'photo': forms.ClearableFileInput(attrs={'accept': 'image/*'}),
        }

class ParametresEntrepriseForm(forms.ModelForm):
    class Meta:
        model = ParametresEntreprise
        fields = [
            'nom', 'sous_titre', 'description', 'telephone', 'email',
            'adresse', 'devise', 'logo', 'cachet', 'fond_login',
        ]
        widgets = {
            'description': forms.Textarea(attrs={'rows': 3}),
            'logo': forms.ClearableFileInput(attrs={'accept': 'image/*'}),
            'cachet': forms.ClearableFileInput(attrs={'accept': 'image/*'}),
            'fond_login': forms.ClearableFileInput(attrs={'accept': 'image/*'}),
        }
