"""
Module d'aide pour l'authentification et la gestion des permissions
Fournit des fonctions utilitaires pour l'authentification des utilisateurs
"""

from pymongo import MongoClient
import os
from dotenv import load_dotenv
from user_management import UserManager

load_dotenv()

# Configuration MongoDB
MONGO_HOST = os.getenv('MONGO_HOST', 'localhost')
MONGO_PORT = int(os.getenv('MONGO_PORT', 27017))
MONGO_USERNAME = os.getenv('MONGO_USERNAME', 'admin')
MONGO_PASSWORD = os.getenv('MONGO_PASSWORD', 'admin123')
DATABASE_NAME = 'healthcare_db'

def authenticate_and_get_user():
    """
    Demande les identifiants à l'utilisateur et retourne les informations de l'utilisateur
    
    Returns:
        dict: Informations de l'utilisateur (username, role, permissions) ou None si échec
    """
    username = input("Nom d'utilisateur: ")
    password = input("Mot de passe: ")
    
    try:
        manager = UserManager()
        user_info = manager.authenticate_user(username, password)
        return user_info
    except Exception as e:
        print(f"✗ Erreur d'authentification: {e}")
        return None

def require_permission(user_info, permission, action_description=""):
    """
    Vérifie si l'utilisateur a la permission requise
    
    Args:
        user_info: Dictionnaire avec les informations de l'utilisateur
        permission: Permission requise (create, read, update, delete, export, import, manage_users)
        action_description: Description de l'action (pour le message d'erreur)
    
    Raises:
        PermissionError: Si l'utilisateur n'a pas la permission
    """
    if not user_info:
        raise PermissionError("Utilisateur non authentifié")
    
    mgr = UserManager()
    if not mgr.check_permission(user_info, permission):
        action = f" pour {action_description}" if action_description else ""
        raise PermissionError(
            f"Permission refusée: l'utilisateur '{user_info['username']}' "
            f"(rôle: {user_info['role']}) n'a pas la permission '{permission}'{action}"
        )

def get_authenticated_connection():
    """
    Établit une connexion MongoDB authentifiée
    
    Returns:
        tuple: (MongoClient, user_info) ou (None, None) en cas d'échec
    """
    user_info = authenticate_and_get_user()
    if not user_info:
        return None, None
    
    try:
        # Connexion MongoDB avec les identifiants admin (pour la connexion de base)
        connection_string = f"mongodb://{MONGO_USERNAME}:{MONGO_PASSWORD}@{MONGO_HOST}:{MONGO_PORT}/"
        client = MongoClient(connection_string)
        
        # Tester la connexion
        client.admin.command('ping')
        
        return client, user_info
    except Exception as e:
        print(f"✗ Erreur de connexion à MongoDB: {e}")
        return None, None
