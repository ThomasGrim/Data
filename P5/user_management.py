"""
Module de gestion des utilisateurs et authentification
Gère les utilisateurs, rôles et permissions pour MongoDB
"""

from pymongo import MongoClient
from werkzeug.security import generate_password_hash, check_password_hash
import os
from dotenv import load_dotenv

load_dotenv()

# Configuration MongoDB
MONGO_HOST = os.getenv('MONGO_HOST', 'localhost')
MONGO_PORT = int(os.getenv('MONGO_PORT', 27017))
MONGO_USERNAME = os.getenv('MONGO_USERNAME', 'admin')
MONGO_PASSWORD = os.getenv('MONGO_PASSWORD', 'admin123')
DATABASE_NAME = 'healthcare_db'

# Définition des rôles et permissions
ROLES_PERMISSIONS = {
    'admin': ['create', 'read', 'update', 'delete', 'export', 'import', 'manage_users'],
    'read_write': ['create', 'read', 'update', 'delete'],
    'read_only': ['read'],
    'analyst': ['read', 'export']
}

class UserManager:
    """Gestionnaire d'utilisateurs pour MongoDB"""
    
    def __init__(self):
        """Initialise la connexion MongoDB"""
        connection_string = f"mongodb://{MONGO_USERNAME}:{MONGO_PASSWORD}@{MONGO_HOST}:{MONGO_PORT}/"
        self.client = MongoClient(connection_string)
        self.db = self.client[DATABASE_NAME]
        self.users_collection = self.db['users']
        self.roles_collection = self.db['roles']
    
    def hash_password(self, password):
        """Hash un mot de passe avec salt"""
        return generate_password_hash(password)
    
    def verify_password(self, password_hash, password):
        """Vérifie un mot de passe"""
        return check_password_hash(password_hash, password)
    
    def initialize_roles(self):
        """Initialise les rôles dans la base de données"""
        for role_name, permissions in ROLES_PERMISSIONS.items():
            role_doc = {
                'name': role_name,
                'permissions': permissions
            }
            # Vérifier si le rôle existe déjà
            if not self.roles_collection.find_one({'name': role_name}):
                self.roles_collection.insert_one(role_doc)
    
    def create_user(self, username, password, role):
        """Crée un nouvel utilisateur"""
        if role not in ROLES_PERMISSIONS:
            raise ValueError(f"Rôle invalide: {role}")
        
        # Vérifier si l'utilisateur existe déjà
        if self.users_collection.find_one({'username': username}):
            raise ValueError(f"L'utilisateur '{username}' existe déjà")
        
        user_doc = {
            'username': username,
            'password_hash': self.hash_password(password),
            'role': role,
            'active': True
        }
        
        self.users_collection.insert_one(user_doc)
        return user_doc
    
    def authenticate_user(self, username, password):
        """Authentifie un utilisateur"""
        user = self.users_collection.find_one({'username': username, 'active': True})
        
        if not user:
            raise ValueError("Nom d'utilisateur ou mot de passe incorrect")
        
        if not self.verify_password(user['password_hash'], password):
            raise ValueError("Nom d'utilisateur ou mot de passe incorrect")
        
        # Retourner les informations de l'utilisateur (sans le hash)
        return {
            'username': user['username'],
            'role': user['role'],
            'permissions': ROLES_PERMISSIONS.get(user['role'], [])
        }
    
    def check_permission(self, user_info, permission):
        """Vérifie si l'utilisateur a une permission"""
        return permission in user_info.get('permissions', [])
    
    def list_users(self):
        """Liste tous les utilisateurs"""
        return list(self.users_collection.find({}, {'password_hash': 0}))
    
    def update_user_role(self, username, new_role):
        """Met à jour le rôle d'un utilisateur"""
        if new_role not in ROLES_PERMISSIONS:
            raise ValueError(f"Rôle invalide: {new_role}")
        
        result = self.users_collection.update_one(
            {'username': username},
            {'$set': {'role': new_role}}
        )
        
        if result.matched_count == 0:
            raise ValueError(f"Utilisateur '{username}' non trouvé")
    
    def deactivate_user(self, username):
        """Désactive un utilisateur"""
        result = self.users_collection.update_one(
            {'username': username},
            {'$set': {'active': False}}
        )
        
        if result.matched_count == 0:
            raise ValueError(f"Utilisateur '{username}' non trouvé")
    
    def delete_user(self, username):
        """Supprime un utilisateur"""
        result = self.users_collection.delete_one({'username': username})
        
        if result.deleted_count == 0:
            raise ValueError(f"Utilisateur '{username}' non trouvé")
    
    def close(self):
        """Ferme la connexion MongoDB"""
        self.client.close()
