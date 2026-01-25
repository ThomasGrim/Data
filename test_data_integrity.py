"""
Script de test d'intégrité des données
Teste les données avant et après la migration vers MongoDB
Avec authentification utilisateur et gestion des permissions.
"""

import pandas as pd
from pymongo import MongoClient
from datetime import datetime
import sys
import os
from dotenv import load_dotenv
from auth_helper import get_authenticated_connection, require_permission

load_dotenv()

# Configuration MongoDB
MONGO_HOST = os.getenv('MONGO_HOST', 'localhost')
MONGO_PORT = int(os.getenv('MONGO_PORT', 27017))
MONGO_USERNAME = os.getenv('MONGO_USERNAME', 'admin')
MONGO_PASSWORD = os.getenv('MONGO_PASSWORD', 'admin123')
DATABASE_NAME = 'healthcare_db'
COLLECTION_NAME = 'patients'

class DataIntegrityTester:
    """Classe pour tester l'intégrité des données"""
    
    def __init__(self):
        # Chercher le CSV dans plusieurs emplacements possibles
        possible_paths = [
            'csv/healthcare_dataset.csv',
            '/data/csv/healthcare_dataset.csv',
            './csv/healthcare_dataset.csv'
        ]
        self.csv_path = None
        for path in possible_paths:
            if os.path.exists(path):
                self.csv_path = path
                break
        if not self.csv_path:
            self.csv_path = 'csv/healthcare_dataset.csv'  # Par défaut
        self.client = None
        self.db = None
        self.collection = None
    
    def connect_mongodb(self):
        """Établit la connexion à MongoDB avec authentification"""
        try:
            client, user_info = get_authenticated_connection()
            if not client or not user_info:
                return False
            
            # Vérifier la permission de lecture
            require_permission(user_info, 'read', 'tester l\'intégrité des données')
            
            self.client = client
            self.db = self.client[DATABASE_NAME]
            self.collection = self.db[COLLECTION_NAME]
            print(f"✓ Connexion établie pour {user_info['username']} (rôle: {user_info['role']})")
            return True
        except Exception as e:
            print(f"✗ Erreur de connexion: {e}")
            return False
    
    def test_csv_data(self):
        """Teste l'intégrité des données CSV"""
        print("\n" + "="*60)
        print("TEST D'INTÉGRITÉ - DONNÉES CSV")
        print("="*60)
        
        if not os.path.exists(self.csv_path):
            print(f"✗ Fichier CSV non trouvé: {self.csv_path}")
            return False
        
        df = pd.read_csv(self.csv_path)
        results = {'passed': 0, 'failed': 0, 'issues': []}
        
        # Test 1: Colonnes disponibles
        print("\n1. Test des colonnes disponibles:")
        required_columns = ['Name', 'Age', 'Gender', 'Blood Type', 'Medical Condition',
                           'Date of Admission', 'Doctor', 'Hospital', 'Insurance Provider',
                           'Billing Amount', 'Room Number', 'Admission Type',
                           'Discharge Date', 'Medication', 'Test Results']
        missing = [col for col in required_columns if col not in df.columns]
        if missing:
            results['failed'] += 1
            results['issues'].append(f"Colonnes manquantes: {missing}")
            print(f"   ✗ Colonnes manquantes: {missing}")
        else:
            results['passed'] += 1
            print(f"   ✓ Toutes les colonnes requises sont présentes ({len(df.columns)} colonnes)")
        
        # Test 2: Types de variables
        print("\n2. Test des types de variables:")
        type_checks = {
            'Age': 'int64',
            'Billing Amount': 'float64',
            'Room Number': 'int64'
        }
        type_ok = True
        for col, expected_type in type_checks.items():
            if df[col].dtype != expected_type:
                type_ok = False
                results['issues'].append(f"Type incorrect pour {col}: {df[col].dtype} au lieu de {expected_type}")
                print(f"   ✗ {col}: {df[col].dtype} (attendu: {expected_type})")
        if type_ok:
            results['passed'] += 1
            print("   ✓ Types de variables corrects")
        else:
            results['failed'] += 1
        
        # Test 3: Doublons
        print("\n3. Test des doublons:")
        duplicates = df.duplicated().sum()
        if duplicates > 0:
            results['failed'] += 1
            results['issues'].append(f"{duplicates} doublons trouvés")
            print(f"   ✗ {duplicates} doublons trouvés")
        else:
            results['passed'] += 1
            print("   ✓ Aucun doublon détecté")
        
        # Test 4: Valeurs manquantes
        print("\n4. Test des valeurs manquantes:")
        missing_values = df.isnull().sum()
        missing_count = missing_values.sum()
        if missing_count > 0:
            results['failed'] += 1
            missing_cols = missing_values[missing_values > 0]
            results['issues'].append(f"Valeurs manquantes: {missing_cols.to_dict()}")
            print(f"   ✗ {missing_count} valeurs manquantes trouvées:")
            for col, count in missing_cols.items():
                print(f"      - {col}: {count}")
        else:
            results['passed'] += 1
            print("   ✓ Aucune valeur manquante")
        
        # Test 5: Valeurs aberrantes
        print("\n5. Test des valeurs aberrantes:")
        outliers = []
        if (df['Age'] < 0).any() or (df['Age'] > 150).any():
            outliers.append("Âges aberrants (< 0 ou > 150)")
        if (df['Billing Amount'] < 0).any():
            outliers.append("Montants de facturation négatifs")
        if (df['Room Number'] < 0).any():
            outliers.append("Numéros de chambre négatifs")
        
        if outliers:
            results['failed'] += 1
            results['issues'].extend(outliers)
            print("   ✗ Valeurs aberrantes détectées:")
            for outlier in outliers:
                print(f"      - {outlier}")
        else:
            results['passed'] += 1
            print("   ✓ Aucune valeur aberrante")
        
        # Test 6: Statistiques générales
        print("\n6. Statistiques générales:")
        print(f"   - Nombre total de lignes: {len(df)}")
        print(f"   - Âge moyen: {df['Age'].mean():.2f} ans")
        print(f"   - Âge min: {df['Age'].min()} ans")
        print(f"   - Âge max: {df['Age'].max()} ans")
        print(f"   - Montant moyen: ${df['Billing Amount'].mean():.2f}")
        print(f"   - Conditions médicales uniques: {df['Medical Condition'].nunique()}")
        
        # Résumé
        print("\n" + "-"*60)
        print(f"RÉSUMÉ CSV: {results['passed']} tests réussis, {results['failed']} tests échoués")
        print("-"*60)
        
        return results
    
    def test_mongodb_data(self):
        """Teste l'intégrité des données dans MongoDB"""
        print("\n" + "="*60)
        print("TEST D'INTÉGRITÉ - DONNÉES MONGODB")
        print("="*60)
        
        if not self.connect_mongodb():
            return None
        
        results = {'passed': 0, 'failed': 0, 'issues': []}
        
        # Test 1: Connexion et collection
        print("\n1. Test de connexion et collection:")
        try:
            count = self.collection.count_documents({})
            if count == 0:
                results['failed'] += 1
                results['issues'].append("La collection est vide")
                print("   ✗ La collection est vide")
            else:
                results['passed'] += 1
                print(f"   ✓ Collection accessible avec {count} documents")
        except Exception as e:
            results['failed'] += 1
            results['issues'].append(f"Erreur d'accès: {e}")
            print(f"   ✗ Erreur: {e}")
            return results
        
        # Test 2: Structure des documents
        print("\n2. Test de la structure des documents:")
        sample = self.collection.find_one()
        if sample:
            required_fields = ['name', 'age', 'gender', 'blood_type', 'medical_condition',
                             'date_of_admission', 'doctor', 'hospital', 'insurance_provider',
                             'billing_amount', 'room_number', 'admission_type',
                             'discharge_date', 'medication', 'test_results']
            missing_fields = [field for field in required_fields if field not in sample]
            if missing_fields:
                results['failed'] += 1
                results['issues'].append(f"Champs manquants: {missing_fields}")
                print(f"   ✗ Champs manquants: {missing_fields}")
            else:
                results['passed'] += 1
                print(f"   ✓ Tous les champs requis sont présents ({len(required_fields)} champs)")
        
        # Test 3: Types de données
        print("\n3. Test des types de données:")
        type_issues = []
        for doc in self.collection.find().limit(100):
            if not isinstance(doc.get('age'), int):
                type_issues.append("Le champ 'age' n'est pas un entier")
            if not isinstance(doc.get('billing_amount'), (int, float)):
                type_issues.append("Le champ 'billing_amount' n'est pas un nombre")
            if not isinstance(doc.get('room_number'), int):
                type_issues.append("Le champ 'room_number' n'est pas un entier")
        
        if type_issues:
            results['failed'] += 1
            results['issues'].extend(list(set(type_issues)))
            print("   ✗ Problèmes de type détectés:")
            for issue in set(type_issues):
                print(f"      - {issue}")
        else:
            results['passed'] += 1
            print("   ✓ Types de données corrects")
        
        # Test 4: Doublons (basé sur une combinaison de champs)
        print("\n4. Test des doublons potentiels:")
        pipeline = [
            {'$group': {
                '_id': {
                    'name': '$name',
                    'date_of_admission': '$date_of_admission',
                    'hospital': '$hospital'
                },
                'count': {'$sum': 1}
            }},
            {'$match': {'count': {'$gt': 1}}}
        ]
        duplicates = list(self.collection.aggregate(pipeline))
        if duplicates:
            results['failed'] += 1
            results['issues'].append(f"{len(duplicates)} doublons potentiels trouvés")
            print(f"   ✗ {len(duplicates)} doublons potentiels détectés")
        else:
            results['passed'] += 1
            print("   ✓ Aucun doublon détecté")
        
        # Test 5: Valeurs nulles
        print("\n5. Test des valeurs nulles:")
        null_issues = []
        for field in ['name', 'age', 'gender', 'medical_condition']:
            count = self.collection.count_documents({field: None})
            if count > 0:
                null_issues.append(f"{field}: {count} valeurs nulles")
        
        if null_issues:
            results['failed'] += 1
            results['issues'].extend(null_issues)
            print("   ✗ Valeurs nulles trouvées:")
            for issue in null_issues:
                print(f"      - {issue}")
        else:
            results['passed'] += 1
            print("   ✓ Aucune valeur nulle dans les champs critiques")
        
        # Test 6: Comparaison CSV vs MongoDB
        print("\n6. Comparaison CSV vs MongoDB:")
        try:
            df = pd.read_csv(self.csv_path)
            csv_count = len(df)
            mongo_count = self.collection.count_documents({})
            
            if csv_count == mongo_count:
                results['passed'] += 1
                print(f"   ✓ Nombre de documents cohérent: {mongo_count}")
            else:
                results['failed'] += 1
                results['issues'].append(f"Différence de nombre: CSV={csv_count}, MongoDB={mongo_count}")
                print(f"   ✗ Différence de nombre: CSV={csv_count}, MongoDB={mongo_count}")
        except Exception as e:
            results['failed'] += 1
            results['issues'].append(f"Erreur de comparaison: {e}")
            print(f"   ✗ Erreur: {e}")
        
        # Statistiques MongoDB
        print("\n7. Statistiques MongoDB:")
        pipeline = [
            {'$group': {
                '_id': None,
                'avg_age': {'$avg': '$age'},
                'min_age': {'$min': '$age'},
                'max_age': {'$max': '$age'},
                'avg_billing': {'$avg': '$billing_amount'},
                'total_docs': {'$sum': 1}
            }}
        ]
        stats = list(self.collection.aggregate(pipeline))
        if stats:
            s = stats[0]
            print(f"   - Documents: {s['total_docs']}")
            print(f"   - Âge moyen: {s['avg_age']:.2f} ans")
            print(f"   - Âge min: {s['min_age']} ans")
            print(f"   - Âge max: {s['max_age']} ans")
            print(f"   - Montant moyen: ${s['avg_billing']:.2f}")
        
        # Résumé
        print("\n" + "-"*60)
        print(f"RÉSUMÉ MONGODB: {results['passed']} tests réussis, {results['failed']} tests échoués")
        print("-"*60)
        
        self.client.close()
        return results
    
    def run_all_tests(self):
        """Exécute tous les tests"""
        print("\n" + "="*60)
        print("SUITE DE TESTS D'INTÉGRITÉ DES DONNÉES")
        print("="*60)
        
        csv_results = self.test_csv_data()
        mongo_results = self.test_mongodb_data()
        
        print("\n" + "="*60)
        print("RÉSUMÉ GLOBAL")
        print("="*60)
        
        if csv_results:
            print(f"\nCSV: {csv_results['passed']} réussis, {csv_results['failed']} échoués")
        
        if mongo_results:
            print(f"MongoDB: {mongo_results['passed']} réussis, {mongo_results['failed']} échoués")
        
        if csv_results and mongo_results:
            total_passed = csv_results['passed'] + mongo_results['passed']
            total_failed = csv_results['failed'] + mongo_results['failed']
            print(f"\nTOTAL: {total_passed} réussis, {total_failed} échoués")
            
            if total_failed == 0:
                print("\n✓ Tous les tests sont passés avec succès!")
            else:
                print("\n⚠ Certains tests ont échoué. Vérifiez les détails ci-dessus.")

if __name__ == "__main__":
    tester = DataIntegrityTester()
    tester.run_all_tests()

