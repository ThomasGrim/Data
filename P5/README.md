# Projet MongoDB - Migration de données Healthcare

Ce projet démontre comment migrer des données CSV vers MongoDB, effectuer des opérations CRUD, et tester l'intégrité des données.

## 📋 Table des matières

1. [Concepts MongoDB](#concepts-mongodb)
2. [Prérequis](#prérequis)
3. [Installation](#installation)
4. [Système d'authentification](#système-dauthentification)
5. [Structure du projet](#structure-du-projet)
6. [Utilisation](#utilisation)
7. [Scripts disponibles](#scripts-disponibles)
8. [Tests d&#39;intégrité](#tests-dintégrité)
9. [Export/Import](#exportimport)

## 🎓 Concepts MongoDB

### Documents

Un **document** est l'unité de base de données dans MongoDB, équivalent à une ligne dans une base de données relationnelle. C'est un objet JSON (BSON) qui contient des paires clé-valeur.

**Exemple de document :**

```json
{
  "_id": ObjectId("..."),
  "name": "Jean Dupont",
  "age": 45,
  "gender": "Male",
  "medical_condition": "Hypertension"
}
```

### Collections

Une **collection** est un groupe de documents MongoDB, équivalent à une table dans une base de données relationnelle. Les collections n'ont pas de schéma fixe, ce qui permet une grande flexibilité.

**Exemple :** La collection `patients` contient tous les documents de patients.

### Bases de données

Une **base de données** est un conteneur physique pour les collections. Une instance MongoDB peut héberger plusieurs bases de données.

**Exemple :** La base de données `healthcare_db` contient la collection `patients`.

## 📦 Prérequis

- Python 3.8 ou supérieur
- Docker et Docker Compose
- pip (gestionnaire de paquets Python)

## 🚀 Installation

### 1. Cloner ou télécharger le projet

Assurez-vous d'être dans le répertoire du projet :

```bash
cd P5
```

### 2. Créer un environnement virtuel (recommandé)

```bash
python -m venv venv
```

**Windows :**

```bash
venv\Scripts\activate
```

**Linux/Mac :**

```bash
source venv/bin/activate
```

### 3. Installer les dépendances

```bash
pip install -r requirements.txt
```

### 4. Démarrer MongoDB avec Docker

#### Option A : Utilisation simple (MongoDB uniquement)

```bash
docker-compose up -d mongodb
```

Cette commande va :

- Télécharger l'image MongoDB 7.0
- Créer un conteneur nommé `mongodb-healthcare`
- Exposer MongoDB sur le port 27017
- Créer un utilisateur admin avec le mot de passe `admin123`
- Créer des volumes pour persister les données

**Vérifier que MongoDB est démarré :**

```bash
docker ps
```

Vous devriez voir le conteneur `mongodb-healthcare` en cours d'exécution.

#### Option B : Utilisation avec scripts d'initialisation

**Windows :**
```bash
init.bat
```

**Linux/Mac :**
```bash
chmod +x init.sh
./init.sh
```

Ces scripts vont automatiquement :
1. Vérifier que Docker est installé
2. Télécharger le dataset si nécessaire
3. Démarrer MongoDB
4. Initialiser le système d'authentification (rôles et utilisateur admin)

#### Option C : Migration dans un conteneur Docker

Pour exécuter la migration dans un conteneur isolé :

```bash
# Démarrer MongoDB
docker-compose up -d mongodb

# Attendre que MongoDB soit prêt (10 secondes)
sleep 10

# Exécuter la migration dans un conteneur (utilisez -it pour l'authentification interactive)
docker-compose run --rm -it migration
```

Cette approche garantit que la migration s'exécute dans un environnement isolé et reproductible. **Note :** utilisez `-it` pour pouvoir saisir identifiant et mot de passe lors de l'authentification.

## 📁 Structure du projet

```
P5/
├── csv/
│   └── healthcare_dataset.csv          # Fichier CSV source
├── docker-compose.yml                  # Configuration Docker (MongoDB + migration)
├── Dockerfile                          # Image Docker pour l'environnement Python
├── requirements.txt                    # Dépendances Python
├── user_management.py                  # Gestion des utilisateurs et authentification
├── auth_helper.py                      # Module d'aide pour l'authentification
├── init_users.py                       # Script d'initialisation des utilisateurs
├── batch_processor.py                  # Module de traitement par lots (batch)
├── migrate_to_mongodb.py               # Script de migration CSV → MongoDB
├── crud_operations.py                  # Script d'opérations CRUD
├── test_data_integrity.py              # Script de test d'intégrité
├── export_import_mongodb.py            # Script d'export/import
├── download_dataset.py                 # Script de téléchargement du dataset
├── init.sh / init.bat                  # Scripts d'initialisation
├── demo_migration.sh / demo_migration.bat  # Scripts de démonstration
├── DOCKER.md                           # Guide détaillé Docker
└── README.md                           # Ce fichier
```

## 🔧 Utilisation

### Étape 0 : Initialiser le système d'authentification

**Important** : Avant d'utiliser les scripts, initialisez le système d'utilisateurs :

```bash
python init_users.py
```

Cela créera les rôles et un utilisateur admin par défaut.

### Méthode 1 : Utilisation locale (sans Docker pour Python)

### Étape 1 : Télécharger le dataset (si nécessaire)

Si le fichier CSV n'existe pas encore :

```bash
python download_dataset.py
```

### Étape 2 : Migrer les données vers MongoDB

Assurez-vous que MongoDB est démarré :

```bash
docker-compose up -d mongodb
```

Puis exécutez la migration (vous serez invité à vous authentifier) :

```bash
python migrate_to_mongodb.py
```

### Méthode 2 : Utilisation complète avec Docker

### Étape 1 : Initialisation automatique

Utilisez les scripts d'initialisation qui gèrent tout automatiquement :

**Windows :**
```bash
init.bat
```

**Linux/Mac :**
```bash
./init.sh
```

### Étape 2 : Migration manuelle dans un conteneur

Si vous préférez exécuter la migration manuellement dans un conteneur :

```bash
# Démarrer MongoDB
docker-compose up -d mongodb

# Attendre que MongoDB soit prêt
sleep 10  # ou timeout /t 10 sur Windows

# Exécuter la migration (utilisez -it pour l'authentification interactive)
docker-compose run --rm -it migration
```

Ce script va :

1. Lire le fichier CSV
2. Valider l'intégrité des données
3. Convertir les données en documents MongoDB
4. Insérer les documents dans la collection `patients`

**Logique de migration :**

- **Validation** : Vérifie les colonnes, types, doublons, valeurs manquantes
- **Transformation** : Convertit les noms de colonnes (snake_case), les dates en objets datetime
- **Insertion** : Utilise `insert_many()` pour une insertion efficace
- **Vérification** : Affiche des statistiques après l'insertion

### Étape 3 : Tester l'intégrité des données

**Localement :**
```bash
python test_data_integrity.py
```

**Dans un conteneur Docker :** (utilisez `-it` pour l'authentification interactive)
```bash
docker-compose run --rm -it test
```

Ce script teste :

- Les données CSV (avant migration)
- Les données MongoDB (après migration)
- Compare les deux pour s'assurer de la cohérence

### Étape 4 : Explorer les opérations CRUD

```bash
python crud_operations.py
```

## 📝 Scripts disponibles

### 1. `batch_processor.py`

**Fonction :** Module de traitement par lots (batch processing) pour MongoDB

**Fonctionnalités :**

- Traitement par lots configurable (taille par défaut: 5000)
- Sauvegarde automatique de l'état pour reprise en cas d'erreur
- Retry automatique (1 tentative) en cas d'échec
- Affichage de la progression en temps réel
- Statistiques détaillées (vitesse, durée, etc.)
- Support pour insert, update, delete
- Validation optionnelle après traitement

**Exemple d'utilisation :**

```python
from batch_processor import BatchProcessor

processor = BatchProcessor(collection, batch_size=5000)
stats = processor.process_batches(documents, operation='insert', resume=True)
```

### 2. `migrate_to_mongodb.py`

**Fonction :** Migre les données CSV vers MongoDB

**Fonctionnalités :**

- Validation complète des données avant migration
- Conversion automatique des types de données
- **Traitement par lots** (batch processing) pour performance et fiabilité
- **Reprise automatique** en cas d'erreur (état sauvegardé)
- Gestion des erreurs avec retry automatique
- Option de vider la collection existante
- **Authentification requise** (permission `create`)

**Exemple d'utilisation :**

```bash
python migrate_to_mongodb.py
# Vous serez invité à vous authentifier
# Les documents sont traités par lots de 5000
# En cas d'erreur, relancez pour reprendre automatiquement
```

### 3. `crud_operations.py`

**Fonction :** Démontre les opérations CRUD de base

**Opérations :**

- **CREATE** : Créer un nouveau document (permission `create`)
- **READ** : Lire des documents (permission `read`)
- **UPDATE** : Mettre à jour un ou plusieurs documents (permission `update`)
- **DELETE** : Supprimer des documents (permission `delete`)

**Exemple d'utilisation :**

```bash
python crud_operations.py
# Vous serez invité à vous authentifier
```

**Exemples de requêtes :**

```python
# Lire tous les documents
collection.find()

# Lire avec filtre
collection.find({'medical_condition': 'Hypertension'})

# Mettre à jour
collection.update_one({'_id': id}, {'$set': {'age': 46}})

# Supprimer
collection.delete_one({'_id': id})
```

### 4. `test_data_integrity.py`

**Fonction :** Teste l'intégrité des données avant et après migration

**Tests effectués :**

1. Colonnes disponibles
2. Types de variables
3. Doublons
4. Valeurs manquantes
5. Valeurs aberrantes
6. Comparaison CSV vs MongoDB

**Authentification requise** (permission `read`)

**Exemple d'utilisation :**

```bash
python test_data_integrity.py
# Vous serez invité à vous authentifier
```

### 5. `export_import_mongodb.py`

**Fonction :** Exporte et importe des données MongoDB

**Export** (permission `export` requise) :

```bash
python export_import_mongodb.py export --file exported_data.json
# Vous serez invité à vous authentifier
```

**Import** (permission `import` requise) :

```bash
python export_import_mongodb.py import --file exported_data.json --collection patients_backup
# Vous serez invité à vous authentifier
# Les documents sont importés par lots de 5000
# En cas d'erreur, relancez pour reprendre automatiquement
```

**Fonctionnalités :**
- **Traitement par lots** pour l'import (batch processing)
- **Reprise automatique** en cas d'erreur
- Gestion des types BSON (ObjectId, datetime)
- Conversion automatique des dates

## 🧪 Tests

### Tests unitaires

Le projet inclut une suite complète de tests unitaires utilisant **pytest** :

```bash
# Installer les dépendances de test
pip install -r requirements.txt

# Exécuter tous les tests
pytest

# Exécuter avec couverture de code
pytest --cov=. --cov-report=html

# Exécuter un fichier de test spécifique
pytest tests/test_user_management.py
```

**Couverture des tests** :
- ✅ `user_management.py` : Tests complets (hachage, authentification, permissions)
- ✅ `auth_helper.py` : Tests d'authentification et permissions
- ✅ `migrate_to_mongodb.py` : Tests de validation et conversion
- ✅ `crud_operations.py` : Tests des opérations CRUD
- ✅ `export_import_mongodb.py` : Tests d'export/import
- ✅ `test_data_integrity.py` : Tests d'intégrité

Pour plus de détails, consultez [tests/README.md](tests/README.md).

### Tests d'intégrité

Le script `test_data_integrity.py` automatise les tests d'intégrité :

### Tests sur les données CSV :

- ✅ Vérification des colonnes requises
- ✅ Validation des types de données
- ✅ Détection des doublons
- ✅ Identification des valeurs manquantes
- ✅ Détection des valeurs aberrantes (âge, montants négatifs, etc.)

### Tests sur les données MongoDB :

- ✅ Vérification de la connexion et de la collection
- ✅ Validation de la structure des documents
- ✅ Vérification des types de données
- ✅ Détection des doublons
- ✅ Vérification des valeurs nulles
- ✅ Comparaison du nombre de documents CSV vs MongoDB

### Exécution automatique :

```bash
python test_data_integrity.py
```

Le script affiche un rapport détaillé avec :

- Le statut de chaque test (✓ ou ✗)
- Les problèmes détectés
- Des statistiques sur les données
- Un résumé global

## 📤 Export/Import

### Export des données

Pour sauvegarder toutes les données MongoDB dans un fichier JSON :

```bash
python export_import_mongodb.py export
```

Ou avec un nom de fichier personnalisé :

```bash
python export_import_mongodb.py export --file backup_2024.json
```

### Import des données

Pour réimporter des données depuis un fichier JSON :

```bash
python export_import_mongodb.py import --file exported_data.json --collection patients_backup
```

## 🎯 Démontrer que la migration fonctionne

Pour prouver que la migration fonctionne correctement, utilisez les scripts de démonstration.

**Important :** Exécutez `init.bat` ou `init.sh` au préalable si ce n'est pas déjà fait (création des utilisateurs et rôles).

**Windows :**
```bash
demo_migration.bat
```

**Linux/Mac :**
```bash
chmod +x demo_migration.sh
./demo_migration.sh
```

Ces scripts exécutent la migration et les tests **localement** (pas dans un conteneur) :
1. ✅ Vérifier que Docker et MongoDB sont opérationnels
2. ✅ Vérifier la présence du fichier CSV
3. ✅ Initialiser le système d'authentification si nécessaire
4. ✅ Exécuter la migration (vous serez invité à vous authentifier)
5. ✅ Exécuter les tests d'intégrité

## 🔍 Commandes MongoDB utiles

### Se connecter à MongoDB via le shell

```bash
docker exec -it mongodb-healthcare mongosh -u admin -p admin123
```

### Commandes MongoDB Shell

```javascript
// Utiliser la base de données
use healthcare_db

// Afficher les collections
show collections

// Compter les documents
db.patients.countDocuments()

// Trouver des documents
db.patients.find().limit(5)

// Trouver avec filtre
db.patients.find({age: {$gt: 60}})

// Agrégation
db.patients.aggregate([
  {$group: {_id: "$medical_condition", count: {$sum: 1}}},
  {$sort: {count: -1}}
])
```

## 🛠️ Configuration

Les paramètres de connexion MongoDB peuvent être modifiés via des variables d'environnement. Créez un fichier `.env` :

```env
MONGO_HOST=localhost
MONGO_PORT=27017
MONGO_USERNAME=admin
MONGO_PASSWORD=admin123
```

Par défaut, les scripts utilisent ces valeurs si le fichier `.env` n'existe pas.

## 📊 Structure des données

Le dataset contient les informations suivantes pour chaque patient :

- **name** : Nom du patient
- **age** : Âge (entier)
- **gender** : Genre (Male/Female)
- **blood_type** : Groupe sanguin
- **medical_condition** : Condition médicale
- **date_of_admission** : Date d'admission
- **doctor** : Nom du médecin
- **hospital** : Nom de l'hôpital
- **insurance_provider** : Assureur
- **billing_amount** : Montant de la facture (float)
- **room_number** : Numéro de chambre (entier)
- **admission_type** : Type d'admission (Emergency/Urgent/Elective)
- **discharge_date** : Date de sortie
- **medication** : Médicament prescrit
- **test_results** : Résultats des tests

## 🐛 Dépannage

### MongoDB ne démarre pas

```bash
# Vérifier les logs
docker-compose logs mongodb

# Redémarrer
docker-compose restart mongodb
```

### Erreur de connexion

- Vérifiez que MongoDB est démarré : `docker ps`
- Vérifiez les identifiants dans `.env` ou dans le script
- Vérifiez que le port 27017 n'est pas utilisé par un autre service

### Erreur lors de la migration

- Vérifiez que le fichier CSV existe dans `csv/healthcare_dataset.csv`
- Vérifiez les permissions d'écriture
- Consultez les messages d'erreur détaillés dans le script

## 📚 Guide d'apprentissage

Un guide pédagogique complet pour débutants est disponible dans [Prez/GUIDE_APPRENTISSAGE.md](../Prez/GUIDE_APPRENTISSAGE.md).

Ce guide explique :
- ✅ Tous les concepts fondamentaux (MongoDB, Docker, Python)
- ✅ L'architecture du projet en détail
- ✅ Le code expliqué ligne par ligne
- ✅ Des exercices pratiques
- ✅ Un glossaire complet
- ✅ Des ressources pour aller plus loin

**Idéal pour** : Apprendre et comprendre tous les aspects du projet

## ☁️ Migration vers le Cloud AWS

Une documentation complète sur la migration MongoDB vers AWS est disponible dans [Prez/AWS_CLOUD_MIGRATION.md](../Prez/AWS_CLOUD_MIGRATION.md).

Cette documentation couvre :
- ✅ Pourquoi migrer vers le cloud AWS
- ✅ Création d'un compte AWS
- ✅ Tarification et estimation des coûts
- ✅ Amazon DocumentDB (compatible MongoDB)
- ✅ Déploiement sur Amazon ECS
- ✅ Configuration des sauvegardes et surveillance
- ✅ Comparaison des solutions et recommandations

## 📚 Ressources

- [Documentation MongoDB](https://docs.mongodb.com/)
- [PyMongo Documentation](https://pymongo.readthedocs.io/)
- [Docker Documentation](https://docs.docker.com/)
- [AWS Documentation](https://docs.aws.amazon.com/)

## 🐳 Architecture Docker

### Volumes Docker

Le projet utilise deux types de volumes :

1. **Volumes nommés** (pour MongoDB) :
   - `mongodb_data` : Persiste les données MongoDB
   - `mongodb_config` : Persiste la configuration MongoDB
   - Ces volumes persistent même si le conteneur est supprimé

2. **Bind mount** (pour les fichiers CSV) :
   - `./csv` → `/data/csv` : Accès aux fichiers CSV locaux
   - Monté en lecture seule dans les conteneurs

### Services Docker

- **mongodb** : Service principal MongoDB (démarre automatiquement)
- **migration** : Service optionnel pour exécuter la migration dans un conteneur
- **test** : Service optionnel pour exécuter les tests dans un conteneur

### Conteneurs vs Machines Virtuelles

**Conteneurs Docker** :
- Légers et rapides (démarrage en secondes)
- Partagent le noyau OS de l'hôte
- Utilisation optimale des ressources
- Isolation au niveau processus

**Machines Virtuelles** :
- Lourdes (plusieurs GB)
- Chaque VM a son propre OS complet
- Démarrage en minutes
- Isolation complète au niveau machine

Pour plus de détails, consultez [DOCKER.md](DOCKER.md).

## 📝 Notes

- Les données sont stockées dans des volumes Docker, elles persistent même si le conteneur est arrêté
- Pour supprimer toutes les données : `docker-compose down -v`
- Les scripts incluent une gestion d'erreurs complète avec des messages informatifs
- Le projet supporte l'exécution locale ET dans des conteneurs Docker
- **Traitement par lots** : Les migrations et imports utilisent un traitement par lots (5000 documents par lot)
- **Reprise automatique** : En cas d'erreur, les scripts sauvegardent l'état et peuvent reprendre automatiquement
- Les fichiers d'état de reprise sont sauvegardés dans `batch_state_*.json` (peuvent être supprimés après migration réussie)

## ✅ Checklist du projet

- [X] Installation de MongoDB en local avec Docker
- [X] Définition des concepts MongoDB (Documents, Collections, Bases de données)
- [X] Création et manipulation de collections et documents
- [X] Opérations CRUD (Create, Read, Update, Delete)
- [X] Test d'intégrité des données avant et après migration
- [X] Automatisation du processus de test
- [X] Import et export des données MongoDB
- [X] Docker Compose avec volumes (CSV et base de données)
- [X] Scripts d'initialisation automatisés
- [X] Migration exécutable dans des conteneurs Docker
- [X] Documentation complète (README + DOCKER.md)
- [X] Documentation migration cloud AWS (AWS_CLOUD_MIGRATION.md)
  - [X] Méthode pour créer un compte AWS
  - [X] Tarifications AWS
  - [X] Amazon DocumentDB et RDS pour MongoDB
  - [X] Déploiement sur Amazon ECS
  - [X] Configuration sauvegardes et surveillance
- [X] Système d'authentification utilisateur
  - [X] Gestion des utilisateurs (création, authentification, modification)
  - [X] Système de rôles et permissions
  - [X] Intégration de l'authentification dans tous les scripts
  - [X] Collection MongoDB pour stocker les utilisateurs
  - [X] Script d'initialisation des utilisateurs
- [X] Tests unitaires complets
  - [X] Suite de tests avec pytest
  - [X] Tests pour tous les modules principaux
  - [X] Fixtures et mocks pour isolation
  - [X] Documentation des tests
  - [X] Configuration pytest.ini

---
