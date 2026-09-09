import re

from django import forms
from django.contrib.auth.forms import UserCreationForm, AuthenticationForm
from django.contrib.auth.models import User, Group
from django.core.exceptions import ValidationError
from crispy_forms.helper import FormHelper
from .models import ProfilUtilisateur, Produit, Fournisseur, ParametresEntreprise
from .models.produit import CASIERS_PAR_CATEGORIE, capacite_cl, SEUIL_GRAND_MODELE_CL


def _valider_extensions_image(fichier):
    """Restreint les uploads d'images aux formats sûrs (JPEG/PNG/WebP)."""
    if fichier is None:
        return
    nom = (fichier.name or '').lower()
    extensions_ok = ('.jpg', '.jpeg', '.png', '.webp', '.gif')
    if not nom.endswith(extensions_ok):
        raise ValidationError(
            "Format d'image non autorisé. Formats acceptés : JPG, PNG, WEBP, GIF."
        )
    if len(fichier.content_type) > 0:
        mime_autorise = ('image/jpeg', 'image/png', 'image/webp', 'image/gif')
        if fichier.content_type not in mime_autorise:
            raise ValidationError(
                "Type MIME de l'image non autorisé. Formats acceptés : JPG, PNG, WEBP, GIF."
            )
    if fichier.size > 5 * 1024 * 1024:
        raise ValidationError("L'image ne doit pas dépasser 5 Mo.")


def _purge_controle(value):
    """Supprime les caractères de contrôle (sauf \n\t) et les balises HTML."""
    if not value:
        return value
    value = re.sub(r'[\x00-\x08\x0b\x0c\x0e-\x1f\x7f]', '', value)
    value = re.sub(r'<\s*/?\s*[a-zA-Z][^>]*>', '', value)
    return value.strip()


def _valider_telephone(value):
    if not value:
        return value
    value = re.sub(r'[^0-9+\s\-().]', '', value)
    if not re.fullmatch(r'[0-9+\s\-().]{7,20}', value):
        raise ValidationError(
            f"« {value} » n'est pas un numéro de téléphone valide."
        )
    return value.strip()


def _nettoyer_champ(nom, champs_textuels):
    """Applique le nettoyage des caractères de contrôle/HTML à un champ."""
    valeur = champs_textuels.get(nom)
    if valeur is None:
        return
    champs_textuels[nom] = _purge_controle(str(valeur))


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


    def clean_nom_complet(self):
        return _purge_controle(self.cleaned_data.get('nom_complet', ''))

    def clean_telephone(self):
        return _valider_telephone(self.cleaned_data.get('telephone', ''))

    def clean_adresse(self):
        return _purge_controle(self.cleaned_data.get('adresse', ''))

    def clean_photo(self):
        _valider_extensions_image(self.cleaned_data.get('photo'))
        return self.cleaned_data.get('photo')

    def clean_carte_id_recto(self):
        _valider_extensions_image(self.cleaned_data.get('carte_id_recto'))
        return self.cleaned_data.get('carte_id_recto')

    def clean_carte_id_verso(self):
        _valider_extensions_image(self.cleaned_data.get('carte_id_verso'))
        return self.cleaned_data.get('carte_id_verso')

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

        _nettoyer_champ('nom', cleaned_data)
        if not cleaned_data.get('nom'):
            self.add_error('nom', 'Le nom du produit est obligatoire.')

        pourcentage = cleaned_data.get('pourcentage_prix_vente')
        if pourcentage is not None and pourcentage < 0:
            self.add_error('pourcentage_prix_vente', 'Le pourcentage doit être positif ou nul.')

        seuil = cleaned_data.get('seuil_alerte')
        if seuil is not None and seuil < 0:
            self.add_error('seuil_alerte', 'Le seuil d’alerte doit être positif ou nul.')

        nom = cleaned_data.get('nom')
        if cleaned_data.get('categorie') in ('sucrerie', 'biere') and cleaned_data.get('casier_contenu'):
            label = 'Bière' if cleaned_data.get('categorie') == 'biere' else 'Sucrerie'
            capacite = capacite_cl(nom)
            casier = cleaned_data.get('casier_contenu')
            if capacite is not None and capacite < SEUIL_GRAND_MODELE_CL and casier != 24:
                self.add_error(
                    'casier_contenu',
                    f"Une {label.lower()} de moins de 50cl doit avoir un casier de 24 bouteilles.",
                )
            elif capacite is not None and capacite >= SEUIL_GRAND_MODELE_CL and casier not in (12, 20):
                self.add_error(
                    'casier_contenu',
                    f"Une {label.lower()} de 50cl ou plus doit avoir un casier de 12 ou 20 bouteilles.",
                )

        return cleaned_data

    def clean_nom(self):
        return _purge_controle(self.cleaned_data.get('nom', ''))

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

    def clean_nom(self):
        return _purge_controle(self.cleaned_data.get('nom', ''))

    def clean_contact(self):
        return _valider_telephone(self.cleaned_data.get('contact', ''))

    def clean_adresse(self):
        return _purge_controle(self.cleaned_data.get('adresse', ''))

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

    def clean_telephone(self):
        return _valider_telephone(self.cleaned_data.get('telephone', ''))

    def clean_adresse(self):
        return _purge_controle(self.cleaned_data.get('adresse', ''))

    def clean_photo(self):
        _valider_extensions_image(self.cleaned_data.get('photo'))
        return self.cleaned_data.get('photo')

    class Meta:
        model = ProfilUtilisateur
        fields = ['telephone', 'adresse', 'photo']
        widgets = {
            'telephone': forms.TextInput(attrs={'placeholder': "Téléphone"}),
            'adresse': forms.Textarea(attrs={'rows': 3, 'placeholder': "Adresse"}),
            'photo': forms.ClearableFileInput(attrs={'accept': 'image/*'}),
        }

class ParametresEntrepriseForm(forms.ModelForm):
    def clean_nom(self):
        return _purge_controle(self.cleaned_data.get('nom', ''))

    def clean_sous_titre(self):
        return _purge_controle(self.cleaned_data.get('sous_titre', ''))

    def clean_description(self):
        return _purge_controle(self.cleaned_data.get('description', ''))

    def clean_telephone(self):
        return _valider_telephone(self.cleaned_data.get('telephone', ''))

    def clean_email(self):
        email = (self.cleaned_data.get('email') or '').strip().lower()
        if email and not re.fullmatch(r"[^@\s]+@[^@\s]+\.[^@\s]+", email):
            raise ValidationError("Adresse email invalide.")
        return email

    def clean_adresse(self):
        return _purge_controle(self.cleaned_data.get('adresse', ''))

    def clean_devise(self):
        return _purge_controle(self.cleaned_data.get('devise', ''))

    def clean_logo(self):
        _valider_extensions_image(self.cleaned_data.get('logo'))
        return self.cleaned_data.get('logo')

    def clean_cachet(self):
        _valider_extensions_image(self.cleaned_data.get('cachet'))
        return self.cleaned_data.get('cachet')

    def clean_fond_login(self):
        _valider_extensions_image(self.cleaned_data.get('fond_login'))
        return self.cleaned_data.get('fond_login')

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
