# Guide Docker - Projet MongoDB

Ce document explique l'architecture Docker du projet et les concepts clés.

## 🐳 Architecture Docker

Le projet utilise Docker Compose pour orchestrer plusieurs conteneurs :

1. **mongodb** : Conteneur MongoDB pour la base de données
2. **migration** : Conteneur Python pour exécuter la migration (service optionnel)
3. **test** : Conteneur Python pour exécuter les tests (service optionnel)

## 📦 Conteneurs vs Machines Virtuelles

### Conteneurs Docker

Un **conteneur** est une instance légère et portable d'une application qui s'exécute de manière isolée sur le système hôte. Les conteneurs partagent le noyau du système d'exploitation hôte mais ont leur propre système de fichiers isolé.

**Caractéristiques des conteneurs :**
- ✅ **Légers** : Partagent le noyau OS, donc beaucoup plus petits que les VM
- ✅ **Rapides** : Démarrage en quelques secondes
- ✅ **Portables** : Fonctionnent de la même manière sur différents environnements
- ✅ **Isolés** : Chaque conteneur a son propre espace de noms
- ✅ **Efficaces** : Utilisation optimale des ressources système

**Limites des conteneurs :**
- ⚠️ **Sécurité** : Moins isolés qu'une VM (partagent le noyau)
- ⚠️ **OS** : Doivent utiliser le même type de noyau que l'hôte (Linux sur Linux)
- ⚠️ **Persistance** : Les données sont perdues si le conteneur est supprimé (sauf avec volumes)

### Machines Virtuelles (VM)

Une **machine virtuelle** est une émulation complète d'un système informatique avec son propre OS, exécutée sur un hyperviseur.

**Caractéristiques des VM :**
- ✅ **Isolation complète** : OS complet isolé
- ✅ **Sécurité** : Meilleure isolation entre les environnements
- ✅ **Flexibilité** : Peut exécuter n'importe quel OS
- ❌ **Lourdes** : Nécessitent beaucoup de ressources (RAM, CPU, disque)
- ❌ **Lentes** : Démarrage en plusieurs minutes
- ❌ **Moins efficaces** : Chaque VM a son propre OS complet

### Comparaison

| Aspect | Conteneurs | Machines Virtuelles |
|--------|-----------|---------------------|
| Taille | Quelques MB à quelques GB | Plusieurs GB à dizaines de GB |
| Démarrage | Secondes | Minutes |
| Isolation | Processus | Machine complète |
| Performance | Proche du natif | Légèrement plus lent |
| Utilisation RAM | Faible | Élevée |
| Portabilité | Excellente | Bonne |

## 📁 Volumes Docker

### Types de volumes

#### 1. Volumes nommés (Named Volumes)

Les volumes nommés sont gérés par Docker et stockés dans un emplacement géré par Docker.

**Dans notre projet :**
```yaml
volumes:
  mongodb_data:      # Volume pour les données MongoDB
  mongodb_config:    # Volume pour la configuration MongoDB
```

**Avantages :**
- ✅ Gérés par Docker (backup, migration faciles)
- ✅ Persistance garantie même si le conteneur est supprimé
- ✅ Meilleures performances que les bind mounts
- ✅ Fonctionnent sur tous les systèmes

**Utilisation :**
```bash
# Lister les volumes
docker volume ls

# Inspecter un volume
docker volume inspect mongodb_data

# Supprimer un volume
docker volume rm mongodb_data
```

#### 2. Bind Mounts

Les bind mounts lient un répertoire du système hôte directement dans le conteneur.

**Dans notre projet :**
```yaml
volumes:
  - ./csv:/data/csv:ro  # Montage du dossier CSV local en lecture seule
```

**Avantages :**
- ✅ Accès direct aux fichiers de l'hôte
- ✅ Modifications visibles immédiatement
- ✅ Utile pour le développement

**Inconvénients :**
- ⚠️ Dépendant du système de fichiers de l'hôte
- ⚠️ Peut avoir des problèmes de permissions
- ⚠️ Moins portable que les volumes nommés

### Volumes dans notre projet

1. **mongodb_data** : Volume nommé pour persister les données MongoDB
   - Emplacement : `/data/db` dans le conteneur
   - Persiste même si le conteneur MongoDB est supprimé

2. **mongodb_config** : Volume nommé pour la configuration MongoDB
   - Emplacement : `/data/configdb` dans le conteneur

3. **./csv** : Bind mount pour accéder aux fichiers CSV locaux
   - Monté en lecture seule (`:ro`) dans `/data/csv`
   - Permet au conteneur de migration d'accéder aux CSV

## 🚀 Utilisation

### Démarrer uniquement MongoDB

```bash
docker-compose up -d mongodb
```

### Exécuter la migration dans un conteneur

```bash
docker-compose run --rm migration
```

Cette commande :
- Crée un conteneur temporaire à partir du service `migration`
- Exécute le script de migration
- Supprime le conteneur après exécution (`--rm`)

### Exécuter les tests dans un conteneur

```bash
docker-compose run --rm test
```

### Voir les logs

```bash
# Logs de MongoDB
docker-compose logs mongodb

# Logs en temps réel
docker-compose logs -f mongodb
```

### Arrêter les services

```bash
# Arrêter sans supprimer les volumes
docker-compose down

# Arrêter et supprimer les volumes (⚠️ supprime les données)
docker-compose down -v
```

## 🔧 Le démon Docker (Docker Daemon)

### Qu'est-ce que le démon Docker ?

Le **démon Docker** (`dockerd`) est un processus en arrière-plan qui gère les conteneurs, images, volumes et réseaux Docker. Il écoute les commandes via l'API Docker.

### Fonctions du démon

1. **Gestion des conteneurs** : Création, démarrage, arrêt, suppression
2. **Gestion des images** : Téléchargement, construction, stockage
3. **Gestion des volumes** : Création, montage, sauvegarde
4. **Gestion des réseaux** : Création de réseaux isolés
5. **API REST** : Expose une API pour communiquer avec Docker

### Limitations du démon Docker

1. **Sécurité** : 
   - Le démon s'exécute avec des privilèges root
   - Un accès au démon = contrôle total du système
   - ⚠️ Ne jamais exposer le démon Docker sur Internet sans authentification

2. **Performance** :
   - Surveillance continue des conteneurs
   - Consommation de ressources système
   - Peut ralentir sur des machines avec peu de ressources

3. **Dépendances** :
   - Nécessite un noyau Linux moderne
   - Sur Windows/Mac, utilise une VM Linux légère (Docker Desktop)

4. **Isolation** :
   - Les conteneurs partagent le noyau
   - Une faille dans le noyau peut affecter tous les conteneurs

### Vérifier le statut du démon

```bash
# Vérifier que Docker est en cours d'exécution
docker info

# Vérifier les conteneurs en cours d'exécution
docker ps

# Vérifier l'utilisation des ressources
docker stats
```

## 📊 Structure des volumes

```
Volumes Docker:
├── mongodb_data (nommé)
│   └── /data/db (dans le conteneur)
│       └── Fichiers de données MongoDB
│
├── mongodb_config (nommé)
│   └── /data/configdb (dans le conteneur)
│       └── Configuration MongoDB
│
└── ./csv (bind mount)
    └── /data/csv (dans le conteneur, lecture seule)
        └── healthcare_dataset.csv
```

## 🔍 Commandes utiles

### Inspecter les volumes

```bash
# Lister tous les volumes
docker volume ls

# Détails d'un volume
docker volume inspect mongodb_data

# Voir l'utilisation de l'espace disque
docker system df -v
```

### Nettoyer l'environnement

```bash
# Supprimer les conteneurs arrêtés
docker container prune

# Supprimer les volumes non utilisés
docker volume prune

# Nettoyage complet (⚠️ attention)
docker system prune -a --volumes
```

### Accéder au conteneur MongoDB

```bash
# Shell interactif
docker exec -it mongodb-healthcare mongosh -u admin -p admin123

# Exécuter une commande
docker exec mongodb-healthcare mongosh --eval "db.version()"
```

## 🛠️ Dépannage

### Le conteneur ne démarre pas

```bash
# Vérifier les logs
docker-compose logs mongodb

# Vérifier le statut
docker-compose ps

# Redémarrer
docker-compose restart mongodb
```

### Problèmes de permissions avec les volumes

```bash
# Sur Linux, ajuster les permissions
sudo chown -R $USER:$USER ./csv

# Vérifier les permissions du volume
docker volume inspect mongodb_data
```

### Le démon Docker ne répond pas

```bash
# Redémarrer Docker (selon l'OS)
# Linux
sudo systemctl restart docker

# Windows/Mac (Docker Desktop)
# Redémarrer Docker Desktop depuis l'interface
```

## 📝 Bonnes pratiques

1. **Utiliser des volumes nommés** pour les données importantes
2. **Utiliser des bind mounts** uniquement pour le développement
3. **Ne jamais exposer le démon Docker** sur Internet
4. **Faire des sauvegardes régulières** des volumes importants
5. **Utiliser `.dockerignore`** pour exclure les fichiers inutiles
6. **Limiter les ressources** des conteneurs si nécessaire

## 🔐 Sécurité

- Le démon Docker nécessite des privilèges root
- Ne jamais partager l'accès au socket Docker
- Utiliser des images officielles et à jour
- Scanner les images pour les vulnérabilités
- Limiter les capacités des conteneurs avec `--cap-drop`

---

Pour plus d'informations, consultez la [documentation officielle Docker](https://docs.docker.com/).

