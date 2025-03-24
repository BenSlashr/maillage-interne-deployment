import os
import pandas as pd
import uuid
from fastapi import UploadFile, HTTPException
import logging
from typing import Dict, List, Any, Optional
from datetime import datetime

# Définir le répertoire de base pour les uploads
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
UPLOAD_DIR = os.path.join(BASE_DIR, "api", "uploads")

async def save_uploaded_file(file: UploadFile, directory: str, prefix: str = "") -> str:
    """
    Sauvegarde un fichier téléchargé dans le répertoire spécifié
    
    Args:
        file: Fichier téléchargé
        directory: Répertoire de destination
        prefix: Préfixe pour le nom du fichier
        
    Returns:
        str: Chemin du fichier sauvegardé
    """
    try:
        # Utiliser un chemin absolu pour le répertoire d'upload
        full_directory = os.path.join(UPLOAD_DIR, directory)
        logging.info(f"Répertoire d'upload: {full_directory}")
        logging.info(f"Fichier à télécharger: {file.filename}")
        
        # Créer le répertoire s'il n'existe pas
        os.makedirs(full_directory, exist_ok=True)
        
        # Générer un nom de fichier unique
        file_extension = os.path.splitext(file.filename)[1]
        unique_filename = f"{prefix}_{uuid.uuid4().hex}{file_extension}"
        file_path = os.path.join(full_directory, unique_filename)
        logging.info(f"Chemin du fichier à sauvegarder: {file_path}")
        
        # Sauvegarder le fichier
        with open(file_path, "wb") as f:
            content = await file.read()
            logging.info(f"Taille du contenu: {len(content)} octets")
            f.write(content)
        
        logging.info(f"Fichier sauvegardé avec succès: {file_path}")
        return file_path
    except Exception as e:
        logging.error(f"Erreur lors de la sauvegarde du fichier: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Erreur lors de la sauvegarde du fichier: {str(e)}")

def validate_excel_file(file_path: str, required_columns: List[str]) -> Dict[str, Any]:
    """
    Valide qu'un fichier Excel contient les colonnes requises
    
    Args:
        file_path: Chemin du fichier Excel
        required_columns: Liste des colonnes requises
        
    Returns:
        Dict: Résultat de la validation
    """
    try:
        # Vérifier que le fichier existe
        if not os.path.exists(file_path):
            return {
                "valid": False,
                "message": f"Le fichier {file_path} n'existe pas"
            }
        
        # Vérifier que le fichier est un Excel
        if not file_path.endswith((".xlsx", ".xls")):
            return {
                "valid": False,
                "message": "Le fichier doit être au format Excel (.xlsx ou .xls)"
            }
        
        # Lire le fichier Excel
        df = pd.read_excel(file_path)
        
        # Vérifier les colonnes requises
        missing_columns = [col for col in required_columns if col not in df.columns]
        if missing_columns:
            return {
                "valid": False,
                "message": f"Colonnes requises manquantes: {', '.join(missing_columns)}"
            }
        
        return {
            "valid": True,
            "message": "Fichier valide"
        }
    except Exception as e:
        logging.error(f"Erreur lors de la validation du fichier: {str(e)}")
        return {
            "valid": False,
            "message": f"Erreur lors de la validation du fichier: {str(e)}"
        }

def get_job_status(job_id: str, jobs: Dict[str, Dict[str, Any]]) -> Dict[str, Any]:
    """
    Récupère le statut d'une tâche
    
    Args:
        job_id: ID de la tâche
        jobs: Dictionnaire des tâches
        
    Returns:
        Dict: Statut de la tâche
    """
    if job_id not in jobs:
        raise HTTPException(status_code=404, detail="Tâche non trouvée")
    
    job_info = jobs[job_id].copy()
    
    # Vérifier si le fichier de résultats existe, même si le statut n'est pas "completed"
    if "result_file" in job_info and job_info["result_file"] and os.path.exists(job_info["result_file"]):
        # Si le fichier existe mais que le statut n'est pas "completed", mettre à jour le statut
        if job_info["status"] != "completed":
            logging.info(f"Fichier de résultats trouvé pour la tâche {job_id}, mise à jour du statut")
            jobs[job_id]["status"] = "completed"
            jobs[job_id]["progress"] = 100
            jobs[job_id]["message"] = "Analyse terminée avec succès"
            if "end_time" not in jobs[job_id] or not jobs[job_id]["end_time"]:
                jobs[job_id]["end_time"] = datetime.now().isoformat()
            job_info = jobs[job_id].copy()
    
    return job_info

def get_job_result(job_id: str, jobs: Dict[str, Dict[str, Any]]) -> str:
    """
    Récupère le résultat d'une tâche
    
    Args:
        job_id: ID de la tâche
        jobs: Dictionnaire des tâches
        
    Returns:
        str: Chemin du fichier de résultats
    """
    job_info = get_job_status(job_id, jobs)
    
    if job_info["status"] != "completed":
        raise HTTPException(status_code=400, detail="L'analyse n'est pas encore terminée")
    
    if not job_info["result_file"] or not os.path.exists(job_info["result_file"]):
        raise HTTPException(status_code=404, detail="Fichier de résultats non trouvé")
    
    return job_info["result_file"]
