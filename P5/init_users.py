"""
Script d'initialisation du système d'authentification
Crée les rôles et un utilisateur admin par défaut
"""

from user_management import UserManager

def main():
    """Initialise le système d'authentification"""
    print("=== Initialisation du système d'authentification ===\n")
    
    manager = UserManager()
    
    try:
        # Initialiser les rôles
        print("Initialisation des rôles...")
        manager.initialize_roles()
        print("✓ Rôles initialisés")
        
        # Créer l'utilisateur admin par défaut
        print("\nCréation de l'utilisateur admin par défaut...")
        try:
            manager.create_user('admin', 'admin123', 'admin')
            print("✓ Utilisateur 'admin' créé (mot de passe: admin123)")
        except ValueError as e:
            if "existe déjà" in str(e):
                print("⚠ L'utilisateur 'admin' existe déjà")
            else:
                raise
        
        print("\n✓ Initialisation terminée")
        
    except Exception as e:
        print(f"\n✗ Erreur lors de l'initialisation: {e}")
    finally:
        manager.close()

if __name__ == "__main__":
    main()
