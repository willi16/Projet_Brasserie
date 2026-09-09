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

- **Un ordinateur** sous **Windows 10/11**, **Linux** (Debian/Ubuntu recommandé) ou **macOS**.
- **Python 3.10, 3.11 ou 3.12** : le langage de l'application. Vérifiez en ouvrant un terminal : `python --version` (Windows) ou `python3 --version` (Linux/macOS).
- **(Optionnel) Node.js et npm** : uniquement pour modifier les styles (Tailwind CSS). Le CSS final est **déjà fourni** dans `static/` : pas besoin de Node pour installer et démarrer.
- **(Optionnel) Docker Desktop / Docker Engine** : pour démarrer tout le système (application + base PostgreSQL + rapport automatique du soir) en une seule commande, comme en production.
- **(Optionnel) LaTeX (pdflatex)** : uniquement pour télécharger les factures en **PDF**. Docker l'installe automatiquement ; en local la commande à installer dépend de votre système (voir plus bas).
- **Connexion internet** uniquement au premier téléchargement des dépendances : une fois installées, l'application et toutes ses bibliothèques sont servies **localement**.

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

### Lancement en une seule commande (recommandé)

Un script est fourni pour faire **tout automatiquement** : vérifier Python, créer l'environnement virtuel, installer les dépendances, créer le fichier `.env` (avec une clé `SECRET_KEY` générée aléatoirement), appliquer les migrations, créer un compte administrateur (au choix) et démarrer le serveur.

- **Windows** : double-cliquez sur `setup_local.bat` (ou dans l'invite de commandes : `setup_local.bat`).
- **Linux / macOS** : dans un terminal, à la racine du projet : `bash setup_local.sh`

Le script vous pose 2 questions (compte administrateur, serveur local ou réseau) puis lance l'application. **Si un fichier `.env` existe déjà, il est conservé intact** (le script ne l'écrase jamais).

> Les instructions détaillées étape par étape (si vous préférez tout faire à la main) sont données ci-dessous.

Les étapes sont **les mêmes sur tous les systèmes** ; seule la **commande à taper** change selon que vous êtes sous **Windows**, **Linux** ou **macOS**. Pour chaque étape, utilisez le bloc de votre système.

> **Au choix : Windows avec `py`/`venv\Scripts`, Linux/macOS avec `python3`/`venv/bin`.** Les deux autres commandes (`pip`, `python manage.py`) sont identiques partout une fois l'environnement activé.

### Étape 1 — Récupérer le code et entrer dans le dossier

```bash
git clone <adresse-du-dépôt>
cd devia_gestion
```

(ou copiez simplement le dossier du projet, puis `cd devia_gestion`).

### Étape 2 — Vérifier (ou installer) Python

Ouvrez un terminal et vérifiez la version de votre système :

| Système | Vérifier | Si absent, installer |
|---|---|---|
| **Windows** | `py --version` (ou `python --version`) | https://www.python.org/downloads/ — pendant l'installation, **cochez « Add Python to PATH »** |
| **Linux** (Debian/Ubuntu) | `python3 --version` | `sudo apt update && sudo apt install -y python3 python3-venv python3-pip git` |
| **macOS** | `python3 --version` | `xcode-select --install` puis Python depuis https://www.python.org/downloads/ ou `brew install python@3.12` |

La version affichée doit être **3.10, 3.11 ou 3.12** (le projet est développé et testé avec Django 5.2).

### Étape 3 — Créer un environnement Python isolé (recommandé)

Cela évite de mélanger les dépendances du projet avec celles de votre ordinateur.

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

Une fois activé, le terminal affiche `(venv)` au début de la ligne.

> **Linux** : si la commande échoue avec « ensurepip is not available », installez d'abord `sudo apt install python3-venv`.

### Étape 4 — Installer les dépendances Python

**Toujours dans l'environnement activé** :

```bash
pip install -r requirements.txt
```

ou, si `pip` n'est pas reconnu :

```bash
python -m pip install -r requirements.txt
```

> Le fichier `requirements.txt` contient tout le nécessaire (Django 5.2, API REST, rapports Excel, traitement des images…). Tous ces paquets sont distribués en **fichiers binaires précompilés** : aucune compilation n'est nécessaire sur aucun système.

### Étape 5 — Créer le fichier de configuration (.env)

Le projet lit ses réglages dans un fichier nommé **`.env`** à la racine du projet (`devia_gestion/.env`). **Il n'est pas fourni par défaut** car il contient des secrets. Créez-le et copiez-y le contenu ci-dessous.

- **Windows** : dans l'Explorateur créez un fichier nommé `env` puis renommez-le en `.env`, ou lancez `notepad .env` dans le terminal.
- **Linux / macOS** : lancez `nano .env` (ou `code .env`) dans le terminal.

```env
# ===== Django =====
DEBUG=True
SECRET_KEY=changez-moi-par-une-longue-chaine-aléatoire
ALLOWED_HOSTS=localhost,127.0.0.1
USE_HTTPS=False

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

> **Important :** les lignes `EMAIL_HOST_USER` et `EMAIL_HOST_PASSWORD` sont **obligatoires** pour que l'application démarre, même si vous n'envoyez jamais d'email. Avec Gmail, utilisez un **mot de passe d'application** (voir « Problèmes fréquents »).
>
> `DEBUG=True` est le bon réglage **en local** (erreurs détaillées + fichiers statiques servis automatiquement). Gardez `False` en production.

### Étape 6 — Créer la base de données

```bash
python manage.py migrate
```

### Étape 7 — Créer un compte administrateur

**Option A — données de démonstration (rapide)** : crée produits, clients, fournisseurs, livraisons, ventes et 3 comptes de test.
> Attention : cette commande **supprime toutes les données existantes** avant de générer les données de test.

```bash
python manage.py seed_data
```

**Option B — créer seulement les rôles (sans données, sans compte)** :

```bash
python manage.py create_groups
```

**Option C — compte vide, sans données** :

```bash
python manage.py createsuperuser
```

Suivez les questions (nom d'utilisateur, email, mot de passe).

### Étape 8 — Démarrer l'application

```bash
python manage.py runserver
```

Ouvrez votre navigateur à l'adresse : **http://127.0.0.1:8000**

Vous arrivez sur la page de connexion. Connectez-vous avec le compte créé à l'étape 7 (ex. `admin` / `admin123` avec `seed_data`).

> **Accès depuis un autre appareil sur le même réseau** (tablette, téléphone du caissier) :
> 1. Démarrez avec : `python manage.py runserver 0.0.0.0:8000`
> 2. Ajoutez l'adresse IP de l'ordinateur (ex. `192.168.43.25`) dans `ALLOWED_HOSTS` du fichier `.env`.
> 3. Autorisez le port **8000** dans le **pare-feu** (nécessaire pour être visible des autres appareils) :
>    - **Windows** : Pare-feu Windows Defender → « Autoriser une application » → autoriser Python (réseaux privés).
>    - **Linux** : `sudo ufw allow 8000/tcp` (ou `sudo firewall-cmd --permanent --add-port=8000/tcp && sudo firewall-cmd --reload`).
>    - **macOS** : Réglages Système → Réseau → Pare-feu → autoriser les connexions entrantes pour Python.
> 4. Depuis l'autre appareil, ouvrez : `http://IP-DE-LORDINATEUR:8000`

---

### (Optionnel) Reconstruire le CSS Tailwind

Le fichier `static/css/tailwind.css` est **déjà fourni** : rien à faire pour démarrer. Si vous modifiez les styles (`tailwind/input.css` ou les templates), reconstruisez (les mêmes commandes sous Windows, Linux et macOS, avec Node.js et npm installés) :

```bash
npm install
npm run build:css
python manage.py collectstatic
```

---

### (Optionnel) Utiliser PostgreSQL en local

Par défaut, l'application utilise **SQLite** (un simple fichier `db.sqlite3`, zéro configuration) — parfait pour démarrer. Pour travailler **comme en production** avec PostgreSQL :

| Système | Installation |
|---|---|
| **Windows** | Installez PostgreSQL depuis https://www.postgresql.org/download/windows/ (assistant EDB, port 5432) |
| **Linux** (Debian/Ubuntu) | `sudo apt install -y postgresql && sudo systemctl start postgresql` |
| **macOS** | `brew install postgresql@16 && brew services start postgresql@16` |

Créez ensuite un utilisateur et une base (une seule fois) :

**Linux :**
```bash
sudo -u postgres createuser --pwprompt gestion_user
sudo -u postgres createdb -O gestion_user gestion_db
```

**Windows / macOS** : faites de même via **pgAdmin** (ou `psql`) : rôle `gestion_user` avec mot de passe, base `gestion_db` possédée par ce rôle.

Puis basculez la configuration dans `.env` :

```env
DB_ENGINE=postgres
DB_NAME=gestion_db
DB_USER=gestion_user
DB_PASSWORD=un-mot-de-passe-ici
DB_HOST=127.0.0.1
DB_PORT=5432
```

Et rejouez : `python manage.py migrate`.

---

### (Optionnel) Générer les factures PDF (LaTeX)

Le téléchargement PDF utilise **pdflatex**. Tant qu'il n'est pas installé, **l'aperçu à l'écran et l'impression** fonctionnent toujours ; seul le fichier PDF ne se télécharge pas.

- **Windows** : installez **MiKTeX** (https://miktex.org).
- **Linux** (Debian/Ubuntu) : `sudo apt install -y texlive-latex-base texlive-latex-recommended texlive-fonts-recommended texlive-lang-french texlive-latex-extra`
- **macOS** : installez **MacTeX** (`brew install --cask mactex`).

Vérifiez avec `pdflatex --version`. Dans Docker, tout est déjà installé.

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
| `USE_HTTPS` | `True` uniquement si un proxy terminant le TLS (nginx/traefik/caddy) est en place. En HTTP direct (local, LAN) laisser `False`. | `False` |
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

1. Après avoir **créé le bon de vente**, ouvrez le **détail du bon** : un bouton **Enregistrer des casiers** apparaît si le bon contient une bière ou une sucrerie.
2. Le **modèle** est rempli automatiquement **selon la contenance** : **produit de moins de 50cl = 24 bouteilles** (PM24, imposé), **50cl et plus = casier de 12 ou 20 bouteilles** (GM12/GM20) à choisir à la vente. Il est déduit de la capacité indiquée dans le nom du produit (ex. « 50cl »). Le nombre de bouteilles du casier enregistré suit le modèle choisi.
3. Menu **Casiers emportés** : la liste des casiers partis avec les clients. Colonnes utiles : **Date limite** (date d'emport + 3 jours), **Restant**, **Statut** (*En attente*, *En retard*, *Retourné*) et **Sanction** (montant calculé automatiquement dès le dépassement du délai).
4. Quand le client rend des casiers, saisissez la **quantité rendue** et cliquez sur **Retour**. Le retour peut être **partiel** (le restant continue à être suivi) ; un retour complet marque la ligne *Retourné*.
5. **Sanction :** le montant par bouteille non rendue (par défaut 500 FCFA) se règle dans le menu **Paramètres** (gérant/admin). Il est appliqué automatiquement : *bouteilles non rendues × montant* une fois le délai de 3 jours dépassé. Le nombre de bouteilles par casier est celui du modèle choisi (12, 20 ou 24).
6. **Boisson gazeuse, eau et canettes** : pas de casier à suivre ; l'eau et la boisson gazeuse affichent un modèle **« Emballage »** avec leur contenu.

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
- Le **modèle de casier** est déduit automatiquement : **moins de 50cl = 24 bouteilles** (imposé), **50cl et plus = 12 ou 20 bouteilles** au choix ; l'eau et la boisson gazeuse affichent un modèle **« Emballage »** et la canette « Pas de casier ».
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

**En local, si le PDF ne se génère pas**, c'est que LaTeX (pdflatex) n'est pas installé — voir la section « (Optionnel) Générer les factures PDF (LaTeX) » de l'[installation locale](#installation-en-local-sans-docker) pour la commande selon votre système. Dans Docker, tout est déjà installé.

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
| `python manage.py test gestion_depot` | Lance les tests automatisés (55 tests). |
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

### Problèmes selon le système d'exploitation

**Windows**
- **`py` ou `python` n'est pas reconnu** : relancez l'installateur Python et cochez **« Add Python to PATH »**, puis ouvrez un **nouveau** terminal.
- **Activation impossible** `venv\Scripts\activate` : vérifiez que vous êtes dans le dossier du projet. Si la politique d'exécution PowerShell bloque le script, tapez `Set-ExecutionPolicy -Scope Process RemoteSigned` puis réessayez.

**Linux**
- **« ensurepip is not available »** lors de la création du venv : `sudo apt install python3-venv`.
- **`pip` ou `pip3` introuvable** : `sudo apt install python3-pip`, puis utilisez `python3 -m pip`.
- **« Command 'python' not found »** : sur la plupart des distributions, la commande est `python3`.

**macOS**
- **`xcrun: error: invalid active developer path`** : lancez `xcode-select --install`.
- **`python3` non installé** : `xcode-select --install` puis installez Python depuis https://www.python.org/downloads/ ou `brew install python@3.12`.

---

## Structure du projet

```
devia_gestion/
├── manage.py                  # Point d'entrée des commandes Django
├── requirements.txt           # Dépendances Python
├── setup_local.sh             # Lancement local automatique (Linux/macOS)
├── setup_local.bat            # Lancement local automatique (Windows)
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
