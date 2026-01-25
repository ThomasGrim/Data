"""
Module de traitement par lots (batch processing) pour MongoDB
Gère l'insertion, la mise à jour et la suppression par lots avec reprise en cas d'erreur
"""

import json
import os
from datetime import datetime
from typing import List, Dict, Optional, Callable, Any
from pymongo.collection import Collection
from pymongo.errors import BulkWriteError, PyMongoError


class BatchProcessor:
    """Processeur de lots pour opérations MongoDB"""
    
    def __init__(self, collection: Collection, batch_size: int = 5000, 
                 state_file: Optional[str] = None, operation_name: str = "operation"):
        """
        Initialise le processeur de lots
        
        Args:
            collection: Collection MongoDB cible
            batch_size: Taille des lots (défaut: 5000)
            state_file: Fichier pour sauvegarder l'état (optionnel)
            operation_name: Nom de l'opération pour les logs
        """
        self.collection = collection
        self.batch_size = batch_size
        self.state_file = state_file or f"batch_state_{operation_name}.json"
        self.operation_name = operation_name
        
        # Statistiques
        self.stats = {
            'total_items': 0,
            'processed_items': 0,
            'successful_batches': 0,
            'failed_batches': 0,
            'retried_batches': 0,
            'start_time': None,
            'end_time': None,
            'batches': []
        }
        
        # État pour reprise
        self.state = {
            'last_processed_index': 0,
            'total_batches': 0,
            'current_batch': 0,
            'operation': operation_name,
            'timestamp': None
        }
    
    def _save_state(self, last_index: int, current_batch: int, total_batches: int):
        """Sauvegarde l'état actuel pour permettre la reprise"""
        self.state['last_processed_index'] = last_index
        self.state['current_batch'] = current_batch
        self.state['total_batches'] = total_batches
        self.state['timestamp'] = datetime.now().isoformat()
        
        try:
            with open(self.state_file, 'w', encoding='utf-8') as f:
                json.dump(self.state, f, indent=2, ensure_ascii=False)
        except Exception as e:
            print(f"⚠ Avertissement: Impossible de sauvegarder l'état: {e}")
    
    def _load_state(self) -> Optional[Dict]:
        """Charge l'état sauvegardé pour reprendre"""
        if not os.path.exists(self.state_file):
            return None
        
        try:
            with open(self.state_file, 'r', encoding='utf-8') as f:
                state = json.load(f)
                print(f"✓ État de reprise trouvé: {state['current_batch']}/{state['total_batches']} lots traités")
                return state
        except Exception as e:
            print(f"⚠ Avertissement: Impossible de charger l'état: {e}")
            return None
    
    def _clear_state(self):
        """Supprime le fichier d'état"""
        if os.path.exists(self.state_file):
            try:
                os.remove(self.state_file)
            except Exception as e:
                print(f"⚠ Avertissement: Impossible de supprimer l'état: {e}")
    
    def _insert_batch(self, batch: List[Dict], batch_number: int, retry: bool = False) -> bool:
        """
        Insère un lot de documents dans MongoDB avec retry
        
        Args:
            batch: Liste de documents à insérer
            batch_number: Numéro du lot
            retry: Indique si c'est un retry
            
        Returns:
            True si succès, False sinon
        """
        try:
            result = self.collection.insert_many(batch, ordered=False)
            
            if retry:
                self.stats['retried_batches'] += 1
                print(f"  ✓ Retry réussi pour le lot {batch_number}")
            
            return True
            
        except BulkWriteError as e:
            # Certains documents peuvent avoir échoué, mais d'autres ont réussi
            inserted = e.details.get('nInserted', 0)
            if inserted > 0:
                print(f"  ⚠ Lot {batch_number}: {inserted}/{len(batch)} documents insérés (certains ont échoué)")
                return True
            else:
                print(f"  ✗ Lot {batch_number}: Échec complet de l'insertion")
                return False
                
        except PyMongoError as e:
            print(f"  ✗ Lot {batch_number}: Erreur MongoDB: {e}")
            return False
        except Exception as e:
            print(f"  ✗ Lot {batch_number}: Erreur inattendue: {e}")
            return False
    
    def process_batches(self, items: List[Dict], operation: str = 'insert', 
                       resume: bool = True, validate_callback: Optional[Callable] = None) -> Dict:
        """
        Traite les items par lots
        
        Args:
            items: Liste d'items à traiter
            operation: Type d'opération ('insert', 'update', 'delete')
            resume: Si True, reprend depuis le dernier état sauvegardé
            validate_callback: Fonction de validation optionnelle (appelée à la fin)
            
        Returns:
            Dictionnaire avec les statistiques de traitement
        """
        self.stats['start_time'] = datetime.now()
        self.stats['total_items'] = len(items)
        
        # Charger l'état si reprise demandée
        start_index = 0
        if resume:
            saved_state = self._load_state()
            if saved_state:
                start_index = saved_state['last_processed_index']
                print(f"🔄 Reprise depuis l'index {start_index}")
        
        # Calculer le nombre total de lots
        total_batches = (len(items) - start_index + self.batch_size - 1) // self.batch_size
        current_batch = (start_index // self.batch_size) + 1
        
        print(f"\n=== Traitement par lots ({self.operation_name}) ===")
        print(f"Total d'items: {len(items)}")
        print(f"Taille des lots: {self.batch_size}")
        print(f"Nombre de lots: {total_batches}")
        if start_index > 0:
            print(f"Reprise depuis: {start_index} items ({current_batch-1} lots déjà traités)")
        print()
        
        # Traiter par lots
        for i in range(start_index, len(items), self.batch_size):
            batch = items[i:i + self.batch_size]
            batch_number = (i // self.batch_size) + 1
            
            print(f"[{batch_number}/{total_batches}] Traitement du lot {batch_number} ({len(batch)} items)...", end=' ')
            
            # Sélectionner la méthode selon l'opération
            if operation == 'insert':
                success = self._insert_batch(batch, batch_number)
            else:
                print(f"✗ Opération '{operation}' non supportée")
                success = False
            
            # Retry en cas d'échec
            if not success:
                print(f"\n  🔄 Tentative de retry pour le lot {batch_number}...", end=' ')
                
                if operation == 'insert':
                    retry_success = self._insert_batch(batch, batch_number, retry=True)
                else:
                    retry_success = False
                
                if not retry_success:
                    print(f"\n✗ Échec après retry pour le lot {batch_number}. Arrêt du traitement.")
                    self._save_state(i, batch_number, total_batches)
                    self.stats['end_time'] = datetime.now()
                    return self.stats
            
            if success or (not success and retry_success):
                self.stats['successful_batches'] += 1
                self.stats['processed_items'] += len(batch)
            else:
                self.stats['failed_batches'] += 1
            
            # Sauvegarder l'état après chaque lot
            self._save_state(i + len(batch), batch_number, total_batches)
            
            # Enregistrer les stats du lot
            batch_stats = {
                'batch_number': batch_number,
                'items_count': len(batch),
                'success': success or retry_success,
                'timestamp': datetime.now().isoformat()
            }
            self.stats['batches'].append(batch_stats)
        
        # Validation finale si callback fourni
        if validate_callback:
            print("\n=== Validation finale ===")
            try:
                validation_result = validate_callback(self.collection)
                if validation_result:
                    print("✓ Validation réussie")
                else:
                    print("⚠ Validation échouée")
            except Exception as e:
                print(f"✗ Erreur lors de la validation: {e}")
        
        # Nettoyer l'état si tout s'est bien passé
        self._clear_state()
        
        self.stats['end_time'] = datetime.now()
        
        # Afficher les statistiques finales
        self._print_statistics()
        
        return self.stats
    
    def _print_statistics(self):
        """Affiche les statistiques de traitement"""
        duration = (self.stats['end_time'] - self.stats['start_time']).total_seconds()
        items_per_second = self.stats['processed_items'] / duration if duration > 0 else 0
        
        print("\n" + "="*60)
        print("STATISTIQUES DE TRAITEMENT")
        print("="*60)
        print(f"Items totaux: {self.stats['total_items']}")
        print(f"Items traités: {self.stats['processed_items']}")
        print(f"Lots réussis: {self.stats['successful_batches']}")
        print(f"Lots échoués: {self.stats['failed_batches']}")
        print(f"Lots retry: {self.stats['retried_batches']}")
        print(f"Durée: {duration:.2f} secondes")
        print(f"Vitesse: {items_per_second:.2f} items/seconde")
        print("="*60)
    
    def get_statistics(self) -> Dict:
        """Retourne les statistiques de traitement"""
        return self.stats.copy()
    
    def clear_resume_state(self):
        """Supprime l'état de reprise (utile pour forcer un redémarrage complet)"""
        self._clear_state()
        print("✓ État de reprise supprimé")


def calculate_optimal_batch_size(total_items: int, max_batch_size: int = 5000) -> int:
    """
    Calcule une taille de lot optimale basée sur le nombre total d'items
    
    Args:
        total_items: Nombre total d'items à traiter
        max_batch_size: Taille maximale de lot
        
    Returns:
        Taille de lot optimale
    """
    if total_items <= 1000:
        return min(100, total_items)
    elif total_items <= 10000:
        return min(1000, total_items)
    else:
        return max_batch_size
