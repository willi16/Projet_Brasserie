# Deiva Gestion — Gestion du dépôt de boissons

Application web de gestion complète pour un dépôt de vente de boissons (DEIVA - Commerce Général, Lomé - Togo).

Elle permet de gérer les **produits**, les **stocks**, les **ventes** (bons de vente), les **livraisons** des fournisseurs, de **générer des factures** (à l'écran et en PDF), de produire des **rapports de ventes**, et de gérer les **comptes des employés** avec des rôles bien définis.

Ce guide est écrit pour que **même une personne qui n'est pas programmeur** puisse installer, démarrer et utiliser l'application.

---

## Table des matières

1. [Ce dont vous avez besoin](#ce-dont-vous-avez-besoin)
2. [Comprendre en 2 minutes](#comprendre-en-2-minutes)
3. [Installation en local (sans Docker)](#installation-en-local-sans-docker)
4. [Déploiement avec Docker + PostgreSQL (comme en production)](#déploiement-avec-docker--postgresql-comme-en-production)
5. [Le fichier de configuration .env](#le-fichier-de-configuration-env)
6. [Les comptes de démonstration](#les-comptes-de-démonstration)
7. [Utilisation au quotidien](#utilisation-au-quotidien)
8. [Guide des fonctionnalités](#guide-des-fonctionnalités)
9. [La facture (aperçu et PDF)](#la-facture-aperçu-et-pdf)
10. [Commandes utiles](#commandes-utiles)
11. [Problèmes fréquents et solutions](#problèmes-fréquents-et-solutions)
12. [Structure du projet](#structure-du-projet)
13. [Technologies utilisées](#technologies-utilisées)

---

## Ce dont vous avez besoin

- **Un ordinateur** sous Windows, Linux ou macOS.
- **Python 3.10 ou plus récent** : c'est le langage de l'application. Vérifiez en ouvrant un terminal : `python --version` (ou `python3 --version`).
- **(Optionnel) Node.js et npm** : uniquement si vous devez modifier les styles (Tailwind CSS).
- **(Optionnel) Docker Desktop** : pour démarrer tout le système (application + base de données PostgreSQL) en une seule commande, comme en production.
- **(Optionnel) pdflatex (LaTeX)** : uniquement si vous voulez générer les factures au format PDF. Docker l'installe automatiquement. En local, installez le paquet `texlive-latex-*` de votre système.

---

## Comprendre en 2 minutes

| Terme | Ce que c'est |
|---|---|
| **Produit** | Une boisson ou un article vendu (ex. Coca-Cola 50cl). Chaque produit a un **prix d'achat** (par casier) et un **prix de vente** (par casier). |
| **Casier** | L'unité de vente (ex. 24 bouteilles). Une vente peut porter sur un casier complet (fraction 1.00), un demi-casier (0.50), un quart (0.25), etc. |
| **Stock** | Le nombre de casiers disponibles. Il augmente à la livraison (entrée) et diminue à la vente (sortie). |
| **Bon de vente** | La note de vente à un client : produit(s), fraction, quantité, montant total. |
| **Bon de livraison** | L'entrée de marchandises reçue d'un fournisseur (fait remonter le stock). |
| **Facture** | Le document officiel remis au client, avec les détails de la vente. On peut l'**apercevoir à l'écran** puis **l'imprimer** ou **la télécharger en PDF**. |
| **Casier emporté** | Un casier (vide) que le client emporte et doit **rendre sous 3 jours**. Passé ce délai, une **sanction** est calculée automatiquement. |
| **Rapport** | Bilan des ventes, bénéfices et produits sur une période donnée. |

Les utilisateurs ont des **rôles** :

| Rôle | Ce qu'il peut faire |
|---|---|
| **Admin** | Tout : gestion des produits, fournisseurs, ventes, livraisons, rapports, comptes des employés, journal d'activité. |
| **Gérant** | Tout sauf la gestion des comptes des employés. |
| **Caissier** | Enregistrer les ventes (il ne voit que les siennes), créer des factures, saisir et suivre les casiers emportés. |

---

## Installation en local (sans Docker)

Suivez ces étapes **dans l'ordre**. Ouvrez un terminal dans le dossier du projet :

```bash
cd devia_gestion
```

### 1. Créer un environnement Python isolé (recommandé)

Cela évite de mélanger les outils de ce projet avec ceux de votre ordinateur.

**Windows :**
```bash
py -m venv venv
venv\Scripts\activate
```

**Linux / macOS :**
```bash
python3 -m venv venv
source venv/bin/activate
```

Vous devriez voir `(venv)` au début de la ligne du terminal.

### 2. Installer les dépendances

```bash
pip install -r requirements.txt
```

### 3. Créer le fichier de configuration

Le projet lit ses réglages dans un fichier nommé `.env`. **Il n'est pas fourni par défaut** (il contient des mots de passe). Créez-le à la racine du projet (`devia_gestion/.env`) et copiez-y ceci :

```env
# ===== Django =====
DEBUG=True
SECRET_KEY=changez-moi-par-une-longue-chaine-aléatoire
ALLOWED_HOSTS=localhost,127.0.0.1

# ===== Base de données (local = SQLite, rien d'autre à configurer) =====
DB_ENGINE=sqlite

# ===== Email (obligatoire pour démarrer, valeurs d'exemple) =====
EMAIL_HOST=smtp.gmail.com
EMAIL_PORT=587
EMAIL_USE_TLS=True
EMAIL_HOST_USER=votre@email.com
EMAIL_HOST_PASSWORD=votre-mot-de-passe
DEFAULT_FROM_EMAIL=votre@email.com
```

> **Important :** les lignes `EMAIL_HOST_USER` et `EMAIL_HOST_PASSWORD` sont **obligatoires** pour que l'application démarre, même si vous n'envoyez jamais d'email. Mettez n'importe quelle valeur correctement formée au début.
>
> Si vous utilisez Gmail, le mot de passe doit être un **mot de passe d'application** (voir la rubrique « Problèmes fréquents »).

### 4. Créer la base de données

```bash
python manage.py migrate
```

### 5. Créer un compte administrateur

**Option A — données de démonstration (rapide)** : crée des produits, clients, fournisseurs, livraisons, ventes et 3 comptes de test.
> Attention : cette commande **supprime toutes les données existantes** avant de générer les données de test.

```bash
python manage.py seed_data
```

**Option B — compte vide, sans données** :

```bash
python manage.py createsuperuser
```

Suivez les questions (nom d'utilisateur, email, mot de passe).

### 6. Démarrer l'application

```bash
python manage.py runserver
```

Ouvrez votre navigateur à l'adresse : **http://127.0.0.1:8000**

Vous arrivez sur la page de connexion. Connectez-vous avec le compte créé à l'étape 5 (ex. `admin` / `admin123` avec `seed_data`).

> Pour rendre l'application accessible depuis un autre appareil sur le même réseau (tablette, téléphone du caissier) :
> ```bash
> python manage.py runserver 0.0.0.0:8000
> ```
> Puis ajoutez l'adresse IP de l'ordinateur dans `ALLOWED_HOSTS` du fichier `.env` et ouvrez `http://IP-DE-LORDINATEUR:8000` depuis l'autre appareil.

---

## Déploiement avec Docker + PostgreSQL (comme en production)

Docker installe tout automatiquement : l'application, la base PostgreSQL, la génération des rapports du soir (cron) et les outils LaTeX pour les factures PDF.

### 1. Prérequis

Installez **Docker Desktop** (ou Docker Engine sur Linux) et assurez-vous qu'il est démarré. Vérifiez : `docker --version`.

### 2. Préparer le fichier .env

Créez `devia_gestion/.env` avec la configuration de production :

```env
# ===== Django =====
DEBUG=False
SECRET_KEY=une-très-longue-chaine-aléatoire-et-secrète
ALLOWED_HOSTS=localhost,127.0.0.1,0.0.0.0

# ===== Base de données PostgreSQL =====
DB_ENGINE=postgres
DB_NAME=gestion_db
DB_USER=gestion_user
DB_PASSWORD=un-mot-de-passe-fort-pour-la-base
DB_HOST=db
DB_PORT=5432

# ===== Email =====
EMAIL_HOST=smtp.gmail.com
EMAIL_PORT=587
EMAIL_USE_TLS=True
EMAIL_HOST_USER=votre@email.com
EMAIL_HOST_PASSWORD=votre-mot-de-passe
DEFAULT_FROM_EMAIL=votre@email.com
```

> Le fichier `docker-compose.yml` contient déjà `DB_ENGINE=postgres`, `DB_HOST=db` et `DB_PORT=5432`. Le mot de passe de la base doit être **le même** que `DB_PASSWORD`.

### 3. Lancer

```bash
docker compose up -d --build
```

La première construction prend plusieurs minutes (installation de LaTeX). Ensuite :

- Application : **http://localhost** (port 80)
- Base de données : PostgreSQL 16 (volume `pgdata` pour conserver les données)
- Rapports quotidiens : générés automatiquement à **23h55** par le conteneur `cron`

### 4. Créer le compte administrateur (une seule fois)

```bash
docker compose exec web python manage.py seed_data
```

ou pour un compte vide :

```bash
docker compose exec web python manage.py createsuperuser
```

### 5. Arrêter / relancer

```bash
docker compose down        # arrête (les données sont conservées)
docker compose up -d       # relance
docker compose down -v     # arrête ET efface les données de la base (attention !)
```

---

## Le fichier de configuration .env

| Variable | Rôle | Valeur locale conseillée |
|---|---|---|
| `DEBUG` | `True` : mode développement (erreurs détaillées, statiques servies automatiquement). `False` : production. | `True` en local, `False` en prod |
| `SECRET_KEY` | Clé de sécurité. **Doit être secrète et unique.** | chaîne aléatoire |
| `ALLOWED_HOSTS` | Adresses autorisées à ouvrir l'application (séparées par des virgules). | `localhost,127.0.0.1` |
| `DB_ENGINE` | `sqlite` (local, simple) ou `postgres` (production). | `sqlite` en local |
| `DB_NAME` / `DB_USER` / `DB_PASSWORD` / `DB_HOST` / `DB_PORT` | Connexion à PostgreSQL (ignoré avec SQLite). | non utilisées en local |
| `EMAIL_HOST`, `EMAIL_HOST_USER`, `EMAIL_HOST_PASSWORD`, ... | Serveur d'envoi d'emails. | voir plus haut |

> **Ne jamais** publier le fichier `.env` (il est dans la liste des fichiers ignorés par git).

---

## Les comptes de démonstration

Après `python manage.py seed_data` (ou `seed_data` via Docker) :

| Utilisateur | Mot de passe | Rôle |
|---|---|---|
| `admin` | `admin123` | Super-utilisateur / Admin |
| `gerant1` | `gerant123` | Gérant |
| `caissier1` | `caissier123` | Caissier |

**Changez ces mots de passe dès la mise en production** (menu utilisateur en haut à droite → Mon profil, ou via `/admin/`).

---

## Utilisation au quotidien

### Vendre à un client (tâche du caissier)

1. **Connectez-vous** à l'application.
2. Menu **Nouvelle vente**.
3. Renseignez le **nom du client** et le **type de paiement** (Espèces / Crédit).
4. Choisissez le **produit**, la **fraction** du casier (1.00 = casier complet, 0.50 = demi-casier, etc.) et la **quantité**.
   - Le stock disponible s'affiche sous le produit. Une vente qui dépasse le stock est bloquée.
5. Renseignez les **casiers emportés** : le nombre de casiers (vides) que le client emporte avec lui. Laissez **0** s'il n'emporte rien. Ils seront à rendre sous **3 jours** (voir rubrique [Casiers emportés](#casiers-emportés)).
6. Cliquez sur **Ajouter une ligne** pour plusieurs articles.
7. Vérifiez le **total estimé**, puis **Créer le bon**.
8. Le bon apparaît dans **Ventes** avec le statut *En cours*. Validez-le pour **déduire le stock** (bouton Valider).
9. Générez la **facture** : voir la rubrique [La facture](#la-facture-aperçu-et-pdf).

> **Seuil d'alerte :** si une vente atteint ou dépasse le seuil du produit (ex. vente de 5 casiers ou plus), seul un **gérant** ou un **admin** peut la valider.

### Suivre les casiers emportés

1. Après avoir **créé le bon de vente**, ouvrez le **détail du bon** : un bouton **Enregistrer des casiers** apparaît si le bon contient une boisson ou une bière.
2. Le **modèle** est rempli automatiquement : **boisson/bière de 50cl ou plus = grand modèle** (GM12 ou GM20), **en dessous de 50cl = petit modèle** (PM24). Il est déduit de la capacité indiquée dans le nom du produit (ex. « 50cl »).
3. Menu **Casiers emportés** : la liste des casiers partis avec les clients. Colonnes utiles : **Date limite** (date d'emport + 3 jours), **Restant**, **Statut** (*En attente*, *En retard*, *Retourné*) et **Sanction** (montant calculé automatiquement dès le dépassement du délai).
4. Quand le client rend des casiers, saisissez la **quantité rendue** et cliquez sur **Retour**. Le retour peut être **partiel** (le restant continue à être suivi) ; un retour complet marque la ligne *Retourné*.
5. **Sanction :** le montant par bouteille non rendue (par défaut 500 FCFA) se règle dans le menu **Paramètres** (gérant/admin). Il est appliqué automatiquement : *bouteilles non rendues × montant* une fois le délai de 3 jours dépassé. Le nombre de bouteilles par casier est celui du produit (12, 20 ou 24).
6. **Eau et sucreries** : pas de casier à suivre, tout est emporté.

### Enregistrer une livraison (tâche du gérant/admin)

1. Menu **Livraisons** → **Créer une livraison**.
2. Choisissez le **fournisseur**, les **produits** et les **quantités**.
3. Validez : les quantités entrent en **stock** (mouvements d'entrée).

### Suivre les ventes et les bénéfices

- Menu **Ventes** : liste de tous les bons, filtres par statut, vendeur ou période.
- Menu **Rapports** : chiffre d'affaires, coûts, bénéfices, produits les plus vendus, export Excel.

### Gérer les comptes des employés (admin uniquement)

- Menu **Créer un compte** : nouvel employé avec son rôle (Caissier, Gérant, Admin).
- Menu **Gérer les comptes** : modifier les rôles existants.
- Menu **Journal d'activité** : trace des actions des utilisateurs.

---

## Guide des fonctionnalités

### Dashboard (accueil)
- Chiffres clés : ventes du jour, montants, produits en alerte de stock.
- Accès rapide à toutes les sections.

### Produits
- Ajouter, modifier, supprimer un produit.
- Champs : nom (avec la capacité, ex. « Coca-Cola 50cl »), catégorie (boisson, bière, eau, sucrerie), nombre de bouteilles par casier, prix d'achat, prix de vente, seuil d'alerte.
- Le **modèle de casier** est déduit automatiquement : boisson/bière de 50cl ou plus = grand modèle (GM12/GM20), en dessous = petit modèle (PM24) ; eau et sucrerie = pas de casier.
- Le stock est calculé automatiquement à partir des mouvements (entrées – sorties).

### Ventes
- **Nouvelle vente** : création d'un bon avec plusieurs lignes, fractions de casier, vérification du stock en temps réel, alerte de seuil.
- **Liste des ventes** : filtres et total par bon.
- **Détail d'un bon** : lignes, total, actions *Valider* (déduit le stock), *Annuler* (restaure le stock), *Aperçu de la facture*, et enregistrement des **casiers à retourner** après la vente.

### Casiers emportés
- Enregistrés **après la création du bon**, depuis le **détail du bon** (bouton *Enregistrer des casiers*), puis suivis dans le menu **Casiers emportés**.
- Modèle déterminé automatiquement par le produit (grand modèle = 50cl ou plus, petit modèle = en dessous) ; seules les **boissons et bières** sont concernées.
- Retour **partiel ou total** enregistré par le caissier ; délai de retour de **3 jours**.
- **Sanction automatique** en cas de retard : montant par bouteille configurable (menu **Paramètres**), calculé et affiché sans action manuelle.
- Le suivi est purement comptable : les retours **ne modifient pas** le stock de produits.

### Livraisons
- Création et liste des bons de livraison des fournisseurs ; chaque livraison alimente le stock.

### Factures
- **Aperçu à l'écran** : page interne de l'application, format A5, prête à imprimer (bouton Imprimer).
- **PDF** : téléchargement du document officiel (nécessite pdflatex ; fourni dans Docker).

### Rapports
- Période au choix, statistiques jour par jour, graphiques, classement des produits, export vers Excel.

### Comptes & sécurité
- Rôles Caissier / Gérant / Admin, journal des actions, photos de profil et cartes d'identité (documents protégés).

---

## La facture (aperçu et PDF)

Depuis le **détail d'un bon de vente**, deux boutons :

1. **Aperçu de la facture** — ouvre la facture **dans l'application** (même onglet, format A5). Cliquez sur **Imprimer** pour l'imprimer (la barre de navigation disparaît automatiquement à l'impression). Un bouton **Télécharger le PDF** y est aussi disponible.
2. **Télécharger le PDF** — génère et télécharge directement le PDF officiel.

**En local, si le PDF ne se génère pas**, c'est que LaTeX (pdflatex) n'est pas installé :
- Windows : installez MiKTeX (https://miktex.org) ou TeX Live.
- Linux : `sudo apt install texlive-latex-base texlive-latex-recommended texlive-fonts-recommended texlive-lang-french`
- macOS : installez MacTeX.

Dans Docker, tout est déjà installé.

---

## Commandes utiles

| Commande | Rôle |
|---|---|
| `python manage.py migrate` | Applique les migrations (structure de la base de données). |
| `python manage.py makemigrations` | Prépare une migration après une modification des modèles. |
| `python manage.py createsuperuser` | Crée un compte administrateur. |
| `python manage.py seed_data` | Charge des données de test (supprime d'abord les données existantes). |
| `python manage.py create_groups` | Crée les rôles (Caissier, Gérant, Admin) sans les données de test. |
| `python manage.py runserver` | Démarre le serveur local. |
| `python manage.py test gestion_depot` | Lance les tests automatisés (24 tests). |
| `python manage.py check` | Vérifie que le projet est cohérent. |
| `python manage.py collectstatic` | Regroupe les fichiers statiques (CSS/JS) dans `staticfiles/`. |
| `npm run build:css` | Reconstruit le CSS Tailwind (après modification de `tailwind/input.css` ou des templates). |
| `python manage.py generer_rapport_quotidien` | Génère le rapport quotidien manuellement. |

---

## Problèmes fréquents et solutions

### L'application refuse de démarrer : « EMAIL_HOST_USER ... non défini »
Le fichier `.env` doit contenir `EMAIL_HOST_USER` et `EMAIL_HOST_PASSWORD` (même avec de fausses valeurs).

### La page s'affiche sans style (CSS manquant)
- En local, mettez `DEBUG=True` dans `.env`.
- Après un changement de CSS, reconstruisez : `npm run build:css` puis `python manage.py collectstatic`.

### « DisallowedHost » (erreur 400) en ouvrant l'application
Ajoutez l'adresse utilisée (ex. `192.168.43.25`) dans `ALLOWED_HOSTS` du fichier `.env`, puis redémarrez.

### Le PDF de facture ne se génère pas
Installez LaTeX/pdflatex (voir rubrique facture) ou utilisez Docker.

### « Bad Request » à cause du mot de passe de base en Docker
Vérifiez que `DB_PASSWORD` dans `.env` est bien utilisé à la fois par le service `db` et l'application (même valeur).

### Docker Compose affiche « The "a" variable is not set »
C'est le `SECRET_KEY` qui contient un `$`. Remplacez la valeur par une chaîne sans caractère `$`, ou échappez-le (`\$`).

### J'ai oublié le mot de passe administrateur
```bash
python manage.py createsuperuser
```
Créez-en un nouveau, ou réinitialisez en console :
```bash
python manage.py shell -c "from django.contrib.auth.models import User; u=User.objects.get(username='admin'); u.set_password('nouveau_mdp'); u.save()"
```

### Envoi d'email Gmail échoue
Gmail exige un **mot de passe d'application** (compte Google → Sécurité → Vérification en 2 étapes → Mots de passe des applications). Utilisez-le dans `EMAIL_HOST_PASSWORD`.

---

## Structure du projet

```
devia_gestion/
├── manage.py                  # Point d'entrée des commandes Django
├── requirements.txt           # Dépendances Python
├── .env                       # Configuration locale (secret, jamais commité)
├── docker-compose.yml         # Orchestration Docker (web + cron + db)
├── Dockerfile                 # Image Docker de l'application
├── start.sh                   # Démarrage Docker : collectstatic + migrate + gunicorn
├── cron_rapport.sh            # Générateur du rapport quotidien (Docker)
├── package.json               # Scripts npm (Tailwind)
├── tailwind/
│   ├── input.css              # Feuille de style source (classes personnalisées)
│   └── tailwind.config.js     # Configuration Tailwind
├── deiva_gestion/             # Configuration du projet Django
│   ├── settings.py            # Tous les réglages (base de données, etc.)
│   ├── urls.py                # Routes principales
│   ├── wsgi.py / asgi.py      # Points d'entrée serveur
│   └── ...
├── gestion_depot/             # Le cœur de l'application
│   ├── models/                # Structures de données (Produit, BonVente, ...)
│   ├── views/                 # Logique des pages
│   ├── forms/                 # Formulaires
│   ├── urls.py                # Routes internes
│   ├── admin.py               # Interface d'administration Django
│   ├── tests.py               # Tests automatisés
│   ├── management/commands/   # Commandes (seed_data, rapports, ...)
│   └── templates/             # Pages HTML (aperçu de facture, création de vente...)
├── static/                    # Fichiers statiques (CSS, JS, images) — servis en local
├── staticfiles/               # Fichiers statiques regroupés (généré par collectstatic)
├── media/                     # Fichiers téléversés (photos, cartes, factures PDF)
└── db.sqlite3                 # Base de données locale (générée à la première utilisation)
```

---

## Technologies utilisées

- **Django 5.2** — framework web Python.
- **PostgreSQL 16** (production) / **SQLite** (développement).
- **Bootstrap de style** remplacé par **Tailwind CSS 3** (interface moderne, mode sombre).
- **django-crispy-forms + crispy-tailwind** — formulaires.
- **SweetAlert2** — fenêtres de confirmation modernes.
- **Jinja2 + LaTeX (pdflatex)** — génération des factures PDF.
- **Whitenoise** — service des fichiers statiques en production.
- **Gunicorn** — serveur web en production.
- **Docker / Docker Compose** — déploiement complet (application + base + cron).
- Toutes les bibliothèques sont **servies localement** (aucun accès internet requis une fois installé).
