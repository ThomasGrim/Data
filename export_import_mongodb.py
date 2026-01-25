"""
Script d'export et d'import de données MongoDB
Permet d'exporter les données vers JSON et de les réimporter
Avec authentification utilisateur et gestion des permissions.
"""

import json
from pymongo import MongoClient
from bson import json_util
from datetime import datetime
import sys
import os
from dotenv import load_dotenv
from auth_helper import get_authenticated_connection, require_permission
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

def export_to_json(output_file='exported_data.json'):
    """Exporte les données MongoDB vers un fichier JSON"""
    print(f"\n=== Export vers {output_file} ===")
    
    client, user_info = get_connection()
    require_permission(user_info, 'export', 'exporter des données')
    
    db = client[DATABASE_NAME]
    collection = db[COLLECTION_NAME]
    
    try:
        # Récupérer tous les documents
        documents = list(collection.find())
        print(f"✓ {len(documents)} documents récupérés")
        
        # Convertir en JSON (gérer les types BSON comme ObjectId et datetime)
        json_data = json.loads(json_util.dumps(documents))
        
        # Sauvegarder dans un fichier
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(json_data, f, indent=2, ensure_ascii=False, default=str)
        
        print(f"✓ Données exportées vers {output_file}")
        print(f"  Taille du fichier: {os.path.getsize(output_file) / 1024 / 1024:.2f} MB")
        
    except Exception as e:
        print(f"✗ Erreur lors de l'export: {e}")
    finally:
        client.close()

def import_from_json(input_file='exported_data.json', target_collection='patients_backup'):
    """Importe les données depuis un fichier JSON vers MongoDB"""
    print(f"\n=== Import depuis {input_file} ===")
    
    if not os.path.exists(input_file):
        print(f"✗ Fichier non trouvé: {input_file}")
        return
    
    client, user_info = get_connection()
    require_permission(user_info, 'import', 'importer des données')
    
    db = client[DATABASE_NAME]
    collection = db[target_collection]
    
    try:
        # Lire le fichier JSON
        with open(input_file, 'r', encoding='utf-8') as f:
            json_data = json.load(f)
        
        print(f"✓ {len(json_data)} documents chargés depuis {input_file}")
        
        # Convertir les données JSON en format BSON
        documents = []
        for doc in json_data:
            # Convertir les dates string en datetime
            if 'date_of_admission' in doc and isinstance(doc['date_of_admission'], str):
                try:
                    doc['date_of_admission'] = datetime.fromisoformat(doc['date_of_admission'].replace('Z', '+00:00'))
                except:
                    pass
            if 'discharge_date' in doc and isinstance(doc['discharge_date'], str):
                try:
                    doc['discharge_date'] = datetime.fromisoformat(doc['discharge_date'].replace('Z', '+00:00'))
                except:
                    pass
            if 'created_at' in doc and isinstance(doc['created_at'], str):
                try:
                    doc['created_at'] = datetime.fromisoformat(doc['created_at'].replace('Z', '+00:00'))
                except:
                    pass
            
            # Supprimer le champ _id pour permettre la création de nouveaux IDs
            if '_id' in doc:
                del doc['_id']
            
            documents.append(doc)
        
        # Insérer dans MongoDB par lots
        if documents:
            print(f"\n=== Import par lots ===")
            
            # Créer le processeur de lots
            batch_processor = BatchProcessor(
                collection=collection,
                batch_size=5000,  # Taille de lot configurable (défaut: 5000)
                state_file=f"batch_state_import_{target_collection}.json",
                operation_name=f"import_{target_collection}"
            )
            
            # Fonction de validation finale
            def validate_import(col):
                """Valide l'import après insertion"""
                total_imported = col.count_documents({})
                expected = len(documents)
                if total_imported >= expected:
                    print(f"✓ Validation: {total_imported} documents dans la collection '{target_collection}'")
                    return True
                else:
                    print(f"⚠ Validation: {total_imported} documents trouvés (attendu: {expected})")
                    return False
            
            # Traiter par lots avec reprise automatique
            stats = batch_processor.process_batches(
                items=documents,
                operation='insert',
                resume=True,  # Permet la reprise en cas d'erreur
                validate_callback=validate_import
            )
            
            print(f"\n✓ Import terminé dans la collection '{target_collection}'")
            print(f"  Nombre total de documents: {collection.count_documents({})}")
            
            # Vérifier s'il y a eu des erreurs
            if stats['failed_batches'] > 0:
                print(f"\n⚠ Attention: {stats['failed_batches']} lot(s) ont échoué")
                print(f"  Vous pouvez relancer l'import pour reprendre depuis le dernier état sauvegardé")
        else:
            print("✗ Aucun document à importer")
        
    except KeyboardInterrupt:
        print("\n\n⚠ Import interrompu par l'utilisateur")
        print("  L'état a été sauvegardé. Vous pouvez relancer l'import pour reprendre.")
    except Exception as e:
        print(f"\n✗ Erreur lors de l'import: {e}")
        print("  L'état a été sauvegardé. Vous pouvez relancer l'import pour reprendre.")
    finally:
        client.close()

def main():
    """Fonction principale"""
    import argparse
    
    parser = argparse.ArgumentParser(description='Export/Import de données MongoDB')
    parser.add_argument('action', choices=['export', 'import'], help='Action à effectuer')
    parser.add_argument('--file', '-f', default='exported_data.json', help='Fichier JSON')
    parser.add_argument('--collection', '-c', default='patients_backup', help='Collection cible (pour import)')
    
    args = parser.parse_args()
    
    if args.action == 'export':
        export_to_json(args.file)
    elif args.action == 'import':
        import_from_json(args.file, args.collection)

if __name__ == "__main__":
    main()

