"""
Script CRUD (Create, Read, Update, Delete) pour MongoDB
Ce script démontre les opérations de base sur les collections et documents MongoDB.
Avec authentification utilisateur et gestion des permissions.
"""

from pymongo import MongoClient
from datetime import datetime
import sys
import os
from dotenv import load_dotenv
from auth_helper import authenticate_and_get_user, require_permission, get_authenticated_connection
from batch_processor import BatchProcessor

load_dotenv()

# Configuration MongoDB
MONGO_HOST = os.getenv('MONGO_HOST', 'localhost')
MONGO_PORT = int(os.getenv('MONGO_PORT', 27017))
MONGO_USERNAME = os.getenv('MONGO_USERNAME', 'admin')
MONGO_PASSWORD = os.getenv('MONGO_PASSWORD', 'admin123')
DATABASE_NAME = 'healthcare_db'
COLLECTION_NAME = 'patients'

def get_connection():
    """Établit la connexion à MongoDB avec authentification"""
    client, user_info = get_authenticated_connection()
    if not client or not user_info:
        print("✗ Échec de l'authentification")
        sys.exit(1)
    return client, user_info

def create_document(client, user_info):
    """CREATE - Créer un nouveau document"""
    require_permission(user_info, 'create', 'créer un document')
    print("\n=== CREATE - Création d'un document ===")
    
    db = client[DATABASE_NAME]
    collection = db[COLLECTION_NAME]
    
    new_patient = {
        'name': 'Jean Dupont',
        'age': 45,
        'gender': 'Male',
        'blood_type': 'O+',
        'medical_condition': 'Hypertension',
        'date_of_admission': datetime(2024, 1, 15),
        'doctor': 'Dr. Martin',
        'hospital': 'Hôpital Central',
        'insurance_provider': 'Blue Cross',
        'billing_amount': 15000.50,
        'room_number': 101,
        'admission_type': 'Elective',
        'discharge_date': datetime(2024, 1, 20),
        'medication': 'Aspirin',
        'test_results': 'Normal',
        'created_at': datetime.now()
    }
    
    result = collection.insert_one(new_patient)
    print(f"✓ Document créé avec l'ID: {result.inserted_id}")
    return result.inserted_id

def read_documents(client, user_info):
    """READ - Lire des documents"""
    require_permission(user_info, 'read', 'lire des documents')
    print("\n=== READ - Lecture de documents ===")
    
    db = client[DATABASE_NAME]
    collection = db[COLLECTION_NAME]
    
    # Lire tous les documents (limité à 5 pour l'exemple)
    print("\n1. Les 5 premiers patients:")
    patients = collection.find().limit(5)
    for i, patient in enumerate(patients, 1):
        print(f"   {i}. {patient['name']} - {patient['medical_condition']} - {patient['age']} ans")
    
    # Lire avec un filtre
    print("\n2. Patients avec Hypertension:")
    hypertension_patients = collection.find({'medical_condition': 'Hypertension'}).limit(3)
    for patient in hypertension_patients:
        print(f"   - {patient['name']} ({patient['age']} ans)")
    
    # Lire un document spécifique
    print("\n3. Recherche par nom (exemple):")
    patient = collection.find_one({'name': {'$regex': 'Jean', '$options': 'i'}})
    if patient:
        print(f"   Trouvé: {patient['name']} - {patient['medical_condition']}")
    else:
        print("   Aucun patient trouvé")
    
    # Compter les documents
    total = collection.count_documents({})
    print(f"\n4. Nombre total de documents: {total}")

def update_document(client, user_info, document_id):
    """UPDATE - Mettre à jour un document"""
    require_permission(user_info, 'update', 'mettre à jour un document')
    print("\n=== UPDATE - Mise à jour d'un document ===")
    
    db = client[DATABASE_NAME]
    collection = db[COLLECTION_NAME]
    
    # Mettre à jour un document spécifique
    if document_id:
        result = collection.update_one(
            {'_id': document_id},
            {'$set': {
                'age': 46,
                'billing_amount': 16000.00,
                'updated_at': datetime.now()
            }}
        )
        print(f"✓ {result.modified_count} document(s) modifié(s)")
    
    # Mettre à jour plusieurs documents
    print("\nMise à jour de plusieurs documents (exemple: augmenter l'âge de 1 an pour les patients de 30 ans):")
    result = collection.update_many(
        {'age': 30},
        {'$inc': {'age': 1}}
    )
    print(f"✓ {result.modified_count} document(s) modifié(s)")

def delete_document(client, user_info, document_id):
    """DELETE - Supprimer un document"""
    require_permission(user_info, 'delete', 'supprimer un document')
    print("\n=== DELETE - Suppression d'un document ===")
    
    db = client[DATABASE_NAME]
    collection = db[COLLECTION_NAME]
    
    if document_id:
        # Supprimer un document spécifique
        result = collection.delete_one({'_id': document_id})
        print(f"✓ {result.deleted_count} document(s) supprimé(s)")
    
    # Exemple: supprimer des documents avec un filtre (commenté pour sécurité)
    # print("\nSuppression de documents par filtre (exemple):")
    # result = collection.delete_many({'age': {'$lt': 18}})
    # print(f"✓ {result.deleted_count} document(s) supprimé(s)")

def batch_create_documents(client, user_info, documents: list, batch_size: int = 5000):
    """CREATE - Créer plusieurs documents par lots"""
    require_permission(user_info, 'create', 'créer des documents')
    print(f"\n=== CREATE - Création de {len(documents)} documents par lots ===")
    
    db = client[DATABASE_NAME]
    collection = db[COLLECTION_NAME]
    
    # Créer le processeur de lots
    batch_processor = BatchProcessor(
        collection=collection,
        batch_size=batch_size,
        state_file="batch_state_crud_create.json",
        operation_name="crud_create"
    )
    
    # Traiter par lots
    stats = batch_processor.process_batches(
        items=documents,
        operation='insert',
        resume=True
    )
    
    print(f"\n✓ {stats['processed_items']} documents créés avec succès")
    return stats

def demonstrate_queries(client, user_info):
    """Démontre des requêtes avancées"""
    require_permission(user_info, 'read', 'exécuter des requêtes')
    print("\n=== Requêtes avancées ===")
    
    db = client[DATABASE_NAME]
    collection = db[COLLECTION_NAME]
    
    # Agrégation: compter par condition médicale
    print("\n1. Nombre de patients par condition médicale:")
    pipeline = [
        {'$group': {'_id': '$medical_condition', 'count': {'$sum': 1}}},
        {'$sort': {'count': -1}},
        {'$limit': 5}
    ]
    results = collection.aggregate(pipeline)
    for result in results:
        print(f"   {result['_id']}: {result['count']} patients")
    
    # Recherche avec opérateurs
    print("\n2. Patients de plus de 60 ans:")
    elderly = collection.find({'age': {'$gt': 60}}).limit(5)
    for patient in elderly:
        print(f"   - {patient['name']} ({patient['age']} ans)")
    
    # Tri et limite
    print("\n3. Top 3 factures les plus élevées:")
    top_bills = collection.find().sort('billing_amount', -1).limit(3)
    for patient in top_bills:
        print(f"   - {patient['name']}: ${patient['billing_amount']:.2f}")

def main():
    """Fonction principale"""
    print("=== Opérations CRUD MongoDB ===\n")
    
    client, user_info = get_connection()
    print(f"✓ Connexion établie pour l'utilisateur: {user_info['username']} (rôle: {user_info['role']})\n")
    
    try:
        # CREATE
        document_id = create_document(client, user_info)
        
        # READ
        read_documents(client, user_info)
        
        # UPDATE
        update_document(client, user_info, document_id)
        
        # DELETE
        delete_document(client, user_info, document_id)
        
        # Requêtes avancées
        demonstrate_queries(client, user_info)
        
    except Exception as e:
        print(f"✗ Erreur: {e}")
    finally:
        client.close()
        print("\n✓ Connexion fermée")

if __name__ == "__main__":
    main()

