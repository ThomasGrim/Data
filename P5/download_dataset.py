import kagglehub
import shutil
import os

# Download latest version
path = kagglehub.dataset_download("prasad22/healthcare-dataset")

print("Path to dataset files:", path)

# Copier le fichier CSV dans le dossier csv
csv_file = os.path.join(path, "healthcare_dataset.csv")
if os.path.exists(csv_file):
    # Créer le dossier csv s'il n'existe pas
    os.makedirs("csv", exist_ok=True)
    
    # Copier le fichier
    destination = os.path.join("csv", "healthcare_dataset.csv")
    shutil.copy2(csv_file, destination)
    print(f"Fichier copié dans: {destination}")
else:
    print("Fichier healthcare_dataset.csv non trouvé dans le dataset")

