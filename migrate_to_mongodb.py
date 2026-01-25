"""
Script de migration des données CSV vers MongoDB
Ce script transfère les données du fichier healthcare_dataset.csv dans MongoDB
avec validation et gestion des erreurs.
Avec authentification utilisateur et gestion des permissions.
"""

import pandas as pd
from pymongo import MongoClient
from datetime import datetime
import sys
import os
from dotenv import load_dotenv
from auth_helper import get_authenticated_connection, require_permission
from batch_processor import BatchProcessor

# Charger les variables d'environnement
load_dotenv()

# Configuration MongoDB
MONGO_HOST = os.getenv('MONGO_HOST', 'localhost')
MONGO_PORT = int(os.getenv('MONGO_PORT', 27017))
MONGO_USERNAME = os.getenv('MONGO_USERNAME', 'admin')
MONGO_PASSWORD = os.getenv('MONGO_PASSWORD', 'admin123')
DATABASE_NAME = 'healthcare_db'
COLLECTION_NAME = 'patients'

def connect_mongodb():
    """Établit la connexion à MongoDB avec authentification"""
    client, user_info = get_authenticated_connection()
    if not client or not user_info:
        print("✗ Échec de l'authentification")
        sys.exit(1)
    
    # Vérifier la permission de création
    require_permission(user_info, 'create', 'effectuer une migration')
    
    print(f"✓ Connexion à MongoDB réussie pour {user_info['username']} (rôle: {user_info['role']})")
    return client, user_info

def validate_data(df):
    """Valide l'intégrité des données avant la migration"""
    print("\n=== Validation des données ===")
    
    issues = []
    
    # Vérifier les colonnes requises
    required_columns = ['Name', 'Age', 'Gender', 'Blood Type', 'Medical Condition', 
                       'Date of Admission', 'Doctor', 'Hospital', 'Insurance Provider',
                       'Billing Amount', 'Room Number', 'Admission Type', 
                       'Discharge Date', 'Medication', 'Test Results']
    
    missing_columns = [col for col in required_columns if col not in df.columns]
    if missing_columns:
        issues.append(f"Colonnes manquantes: {missing_columns}")
    
    # Vérifier les valeurs manquantes
    missing_values = df.isnull().sum()
    if missing_values.any():
        issues.append(f"Valeurs manquantes:\n{missing_values[missing_values > 0]}")
    
    # Vérifier les types de données
    if df['Age'].dtype != 'int64':
        issues.append("La colonne 'Age' doit être de type entier")
    
    if df['Billing Amount'].dtype != 'float64':
        issues.append("La colonne 'Billing Amount' doit être de type float")
    
    # Vérifier les doublons
    duplicates = df.duplicated().sum()
    if duplicates > 0:
        issues.append(f"Nombre de doublons trouvés: {duplicates}")
    
    # Vérifier les valeurs aberrantes
    if (df['Age'] < 0).any() or (df['Age'] > 150).any():
        issues.append("Valeurs d'âge aberrantes détectées")
    
    if (df['Billing Amount'] < 0).any():
        issues.append("Montants de facturation négatifs détectés")
    
    if issues:
        print("⚠ Problèmes détectés:")
        for issue in issues:
            print(f"  - {issue}")
        return False
    else:
        print("✓ Toutes les validations sont passées")
        print(f"  - Nombre de lignes: {len(df)}")
        print(f"  - Colonnes: {len(df.columns)}")
        print(f"  - Doublons: {duplicates}")
        return True

def convert_to_documents(df):
    """Convertit le DataFrame pandas en documents MongoDB"""
    documents = []
    
    for _, row in df.iterrows():
        # Convertir les dates
        try:
            date_admission = datetime.strptime(row['Date of Admission'], '%Y-%m-%d')
        except:
            date_admission = row['Date of Admission']
        
        try:
            date_discharge = datetime.strptime(row['Discharge Date'], '%Y-%m-%d')
        except:
            date_discharge = row['Discharge Date']
        
        document = {
            'name': row['Name'],
            'age': int(row['Age']),
            'gender': row['Gender'],
            'blood_type': row['Blood Type'],
            'medical_condition': row['Medical Condition'],
            'date_of_admission': date_admission,
            'doctor': row['Doctor'],
            'hospital': row['Hospital'],
            'insurance_provider': row['Insurance Provider'],
            'billing_amount': float(row['Billing Amount']),
            'room_number': int(row['Room Number']),
            'admission_type': row['Admission Type'],
            'discharge_date': date_discharge,
            'medication': row['Medication'],
            'test_results': row['Test Results'],
            'created_at': datetime.now()
        }
        documents.append(document)
    
    return documents

def migrate_data():
    """Fonction principale de migration"""
    print("=== Migration CSV vers MongoDB ===\n")
    
    # Lire le fichier CSV
    # Chercher dans plusieurs emplacements possibles (local ou Docker)
    possible_paths = [
        'csv/healthcare_dataset.csv',  # Local
        '/data/csv/healthcare_dataset.csv',  # Docker
        './csv/healthcare_dataset.csv'  # Local avec chemin relatif
    ]
    
    csv_path = None
    for path in possible_paths:
        if os.path.exists(path):
            csv_path = path
            break
    
    if not csv_path:
        print(f"✗ Fichier CSV non trouvé dans les emplacements suivants:")
        for path in possible_paths:
            print(f"  - {path}")
        sys.exit(1)
    
    print(f"Lecture du fichier CSV: {csv_path}")
    df = pd.read_csv(csv_path)
    print(f"✓ {len(df)} lignes chargées\n")
    
    # Valider les données
    if not validate_data(df):
        print("\n✗ La validation a échoué. Migration annulée.")
        sys.exit(1)
    
    # Se connecter à MongoDB
    client, user_info = connect_mongodb()
    db = client[DATABASE_NAME]
    collection = db[COLLECTION_NAME]
    
    # Vérifier si la collection existe déjà
    if collection.count_documents({}) > 0:
        response = input(f"\n⚠ La collection '{COLLECTION_NAME}' contient déjà des données. Voulez-vous la vider? (o/n): ")
        if response.lower() == 'o':
            collection.delete_many({})
            print("✓ Collection vidée")
        else:
            print("Migration annulée")
            client.close()
            sys.exit(0)
    
    # Convertir en documents MongoDB
    print("\n=== Conversion des données ===")
    documents = convert_to_documents(df)
    print(f"✓ {len(documents)} documents préparés")
    
    # Insérer les documents par lots
    print("\n=== Insertion dans MongoDB (traitement par lots) ===")
    try:
        # Créer le processeur de lots
        batch_processor = BatchProcessor(
            collection=collection,
            batch_size=5000,  # Taille de lot configurable (défaut: 5000)
            state_file="batch_state_migration.json",
            operation_name="migration"
        )
        
        # Fonction de validation finale
        def validate_migration(col):
            """Valide la migration après insertion"""
            total_inserted = col.count_documents({})
            expected = len(documents)
            if total_inserted == expected:
                print(f"✓ Validation: {total_inserted} documents dans la collection (attendu: {expected})")
                return True
            else:
                print(f"⚠ Validation: {total_inserted} documents trouvés (attendu: {expected})")
                return False
        
        # Traiter par lots avec reprise automatique
        stats = batch_processor.process_batches(
            items=documents,
            operation='insert',
            resume=True,  # Permet la reprise en cas d'erreur
            validate_callback=validate_migration
        )
        
        # Afficher quelques statistiques
        print("\n=== Statistiques finales ===")
        print(f"Base de données: {DATABASE_NAME}")
        print(f"Collection: {COLLECTION_NAME}")
        print(f"Nombre total de documents: {collection.count_documents({})}")
        
        # Afficher un exemple de document
        sample = collection.find_one()
        if sample:
            print(f"\nExemple de document:")
            for key, value in sample.items():
                if key != '_id':
                    print(f"  {key}: {value}")
        
        # Vérifier s'il y a eu des erreurs
        if stats['failed_batches'] > 0:
            print(f"\n⚠ Attention: {stats['failed_batches']} lot(s) ont échoué")
            print(f"  Vous pouvez relancer le script pour reprendre depuis le dernier état sauvegardé")
        
    except KeyboardInterrupt:
        print("\n\n⚠ Migration interrompue par l'utilisateur")
        print("  L'état a été sauvegardé. Vous pouvez relancer le script pour reprendre.")
        sys.exit(1)
    except Exception as e:
        print(f"\n✗ Erreur lors de l'insertion: {e}")
        print("  L'état a été sauvegardé. Vous pouvez relancer le script pour reprendre.")
        sys.exit(1)
    finally:
        client.close()
        print("\n✓ Connexion fermée")

if __name__ == "__main__":
    migrate_data()

