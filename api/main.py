from fastapi import FastAPI, UploadFile, File, Form, HTTPException, BackgroundTasks, WebSocket, WebSocketDisconnect, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import JSONResponse, FileResponse
from typing import List, Dict, Optional, Any
import pandas as pd
import numpy as np
import os
import json
import logging
import uuid
import shutil
import asyncio
from datetime import datetime
from pydantic import BaseModel

# Import des modules personnalisés
from web_app.models.linking_rules import LinkingRules
from web_app.models.seo_analyzer import SEOAnalyzer
from web_app.utils.file_utils import save_uploaded_file, validate_excel_file, get_job_status, get_job_result

# Configuration du logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler('seo_analysis_api.log')
    ]
)

# Création de l'application FastAPI
app = FastAPI(
    title="SEO Internal Linking API",
    description="API pour l'analyse et l'optimisation du maillage interne pour le SEO",
    version="1.0.0"
)

# Configuration CORS pour permettre les requêtes depuis le frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # En production, spécifiez les origines exactes
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Création des dossiers pour les uploads et les résultats
os.makedirs("uploads/content", exist_ok=True)
os.makedirs("uploads/links", exist_ok=True)
os.makedirs("uploads/gsc", exist_ok=True)
os.makedirs("results", exist_ok=True)

# Montage du dossier static pour servir les fichiers statiques
app.mount("/static", StaticFiles(directory="static"), name="static")

# Dictionnaire pour suivre les tâches en cours
jobs = {}

# Gestionnaire de connexions WebSocket
class ConnectionManager:
    def __init__(self):
        self.active_connections: Dict[str, List[WebSocket]] = {}

    async def connect(self, websocket: WebSocket, job_id: str):
        await websocket.accept()
        if job_id not in self.active_connections:
            self.active_connections[job_id] = []
        self.active_connections[job_id].append(websocket)
        logging.info(f"Nouvelle connexion WebSocket pour la tâche {job_id}, total: {len(self.active_connections[job_id])}")

    def disconnect(self, websocket: WebSocket, job_id: str):
        if job_id in self.active_connections:
            if websocket in self.active_connections[job_id]:
                self.active_connections[job_id].remove(websocket)
                logging.info(f"Déconnexion WebSocket pour la tâche {job_id}, restant: {len(self.active_connections[job_id])}")

    async def send_job_update(self, job_id: str, data: dict):
        if job_id in self.active_connections and self.active_connections[job_id]:
            logging.info(f"Envoi de mise à jour WebSocket pour la tâche {job_id} à {len(self.active_connections[job_id])} clients")
            for connection in self.active_connections[job_id]:
                try:
                    await connection.send_json(data)
                except Exception as e:
                    logging.error(f"Erreur lors de l'envoi de la mise à jour WebSocket: {str(e)}")

manager = ConnectionManager()

# Modèles Pydantic pour la validation des données
class LinkingRule(BaseModel):
    min_links: int
    max_links: int

class SegmentRules(BaseModel):
    rules: Dict[str, Dict[str, LinkingRule]]

class AnalysisConfig(BaseModel):
    min_similarity: float = 0.2
    anchor_suggestions: int = 3

# Routes API
@app.get("/")
async def root():
    return {"message": "Bienvenue sur l'API de SEO Internal Linking"}

@app.post("/upload/content")
async def upload_content_file(file: UploadFile = File(...)):
    """Téléchargement du fichier de contenu"""
    try:
        file_path = await save_uploaded_file(file, "content", "content")
        # Valider que le fichier est un Excel avec les colonnes requises
        validation_result = validate_excel_file(file_path, ["Adresse", "Segments", "Extracteur 1 1"])
        if not validation_result["valid"]:
            os.remove(file_path)
            raise HTTPException(status_code=400, detail=validation_result["message"])
        
        return {"filename": file.filename, "path": file_path}
    except Exception as e:
        logging.error(f"Erreur lors du téléchargement du fichier de contenu: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/upload/links")
async def upload_links_file(file: UploadFile = File(...)):
    """Téléchargement du fichier de liens existants"""
    try:
        file_path = await save_uploaded_file(file, "links", "links")
        # Valider que le fichier est un Excel avec les colonnes requises
        validation_result = validate_excel_file(file_path, ["Source", "Destination"])
        if not validation_result["valid"]:
            os.remove(file_path)
            raise HTTPException(status_code=400, detail=validation_result["message"])
        
        return {"filename": file.filename, "path": file_path}
    except Exception as e:
        logging.error(f"Erreur lors du téléchargement du fichier de liens: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/upload/gsc")
async def upload_gsc_file(file: UploadFile = File(...)):
    """Téléchargement du fichier GSC (Google Search Console)"""
    try:
        file_path = await save_uploaded_file(file, "gsc", "gsc")
        # Valider que le fichier est un Excel avec les colonnes requises
        validation_result = validate_excel_file(file_path, ["URL", "Clics", "Impressions", "Position"])
        if not validation_result["valid"]:
            os.remove(file_path)
            raise HTTPException(status_code=400, detail=validation_result["message"])
        
        return {"filename": file.filename, "path": file_path}
    except Exception as e:
        logging.error(f"Erreur lors du téléchargement du fichier GSC: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/segments")
async def get_segments(content_file: str):
    """Récupère les segments uniques du fichier de contenu"""
    try:
        if not os.path.exists(content_file):
            raise HTTPException(status_code=404, detail="Fichier de contenu non trouvé")
        
        df = pd.read_excel(content_file)
        if "Segments" not in df.columns:
            raise HTTPException(status_code=400, detail="Colonne 'Segments' non trouvée dans le fichier")
        
        segments = sorted(set(
            segment.lower().strip() 
            for segment in df["Segments"].dropna().unique()
        ))
        
        # Normaliser les segments
        normalized_segments = sorted(set(
            'blog' if 'blog' in s or 'article' in s 
            else 'categorie' if 'categ' in s 
            else 'produit' if 'produit' in s or 'product' in s 
            else s 
            for s in segments
        ))
        
        return {"segments": normalized_segments}
    except Exception as e:
        logging.error(f"Erreur lors de la récupération des segments: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/rules")
async def set_linking_rules(rules: SegmentRules):
    """Définit les règles de maillage entre segments"""
    try:
        # Sauvegarder les règles dans un fichier
        with open("segment_rules.json", "w", encoding="utf-8") as f:
            json.dump(rules.rules, f, ensure_ascii=False, indent=4)
        
        return {"message": "Règles de maillage enregistrées avec succès"}
    except Exception as e:
        logging.error(f"Erreur lors de l'enregistrement des règles de maillage: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/rules")
async def get_linking_rules():
    """Récupère les règles de maillage configurées"""
    try:
        if os.path.exists("segment_rules.json"):
            with open("segment_rules.json", "r", encoding="utf-8") as f:
                rules = json.load(f)
            return {"rules": rules}
        else:
            # Retourner les règles par défaut
            from web_app.utils.default_config import DEFAULT_LINKING_RULES
            return {"rules": DEFAULT_LINKING_RULES}
    except Exception as e:
        logging.error(f"Erreur lors de la récupération des règles de maillage: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/analyze")
async def analyze_content(
    background_tasks: BackgroundTasks,
    content_file: str = Form(...),
    links_file: Optional[str] = Form(None),
    gsc_file: Optional[str] = Form(None),
    config: str = Form(...)
):
    """Lance l'analyse du contenu et génère des suggestions de maillage interne"""
    try:
        # Vérifier que les fichiers existent
        if not os.path.exists(content_file):
            raise HTTPException(status_code=404, detail="Fichier de contenu non trouvé")
        
        if links_file and not os.path.exists(links_file):
            raise HTTPException(status_code=404, detail="Fichier de liens non trouvé")
        
        if gsc_file and not os.path.exists(gsc_file):
            raise HTTPException(status_code=404, detail="Fichier GSC non trouvé")
        
        # Convertir la configuration en objet
        analysis_config = json.loads(config)
        
        # Générer un ID unique pour la tâche
        job_id = str(uuid.uuid4())
        
        # Initialiser le statut de la tâche
        jobs[job_id] = {
            "status": "queued",
            "progress": 0,
            "message": "Tâche en attente",
            "result_file": None,
            "start_time": datetime.now().isoformat()
        }
        
        # Lancer l'analyse en arrière-plan
        background_tasks.add_task(
            run_analysis,
            job_id,
            content_file,
            links_file,
            gsc_file,
            analysis_config
        )
        
        return {"job_id": job_id}
    except Exception as e:
        logging.error(f"Erreur lors du lancement de l'analyse: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/job/{job_id}")
async def check_job_status(job_id: str):
    """Vérifie le statut d'une tâche"""
    if job_id not in jobs:
        raise HTTPException(status_code=404, detail="Tâche non trouvée")
    
    job_info = jobs[job_id].copy()
    
    # Vérifier si le fichier de résultats existe
    if "result_file" in job_info and job_info["result_file"]:
        if os.path.exists(job_info["result_file"]):
            # Si le fichier existe mais le statut n'est pas "completed", le mettre à jour
            if job_info["status"] != "completed":
                logging.info(f"Fichier de résultats trouvé pour la tâche {job_id}, mise à jour du statut à 'completed'")
                jobs[job_id]["status"] = "completed"
                jobs[job_id]["progress"] = 100
                jobs[job_id]["message"] = "Analyse terminée avec succès"
                if "end_time" not in jobs[job_id] or not jobs[job_id]["end_time"]:
                    jobs[job_id]["end_time"] = datetime.now().isoformat()
                job_info = jobs[job_id].copy()
        else:
            logging.warning(f"Le fichier de résultats n'existe pas: {job_info['result_file']}")
            
            # Chercher des fichiers de résultats potentiels
            results_dir = "results"
            if os.path.exists(results_dir):
                potential_files = [f for f in os.listdir(results_dir) if f.startswith("seo_suggestions_")]
                potential_files.sort(reverse=True)  # Trier par ordre décroissant (le plus récent en premier)
                
                if potential_files:
                    latest_file = os.path.join(results_dir, potential_files[0])
                    logging.info(f"Fichier de résultats non trouvé pour la tâche {job_id}, mais un fichier potentiel a été trouvé: {latest_file}")
                    jobs[job_id]["result_file"] = latest_file
                    job_info["result_file"] = latest_file
    
    # Si la progression est à 100% mais le statut n'est pas "completed", vérifier s'il y a des fichiers de résultats
    elif job_info["progress"] == 100 and ("result_file" in jobs[job_id] and jobs[job_id]["result_file"]):
        results_dir = "results"
        if os.path.exists(results_dir):
            potential_files = [f for f in os.listdir(results_dir) if f.startswith("seo_suggestions_")]
            potential_files.sort(reverse=True)  # Trier par ordre décroissant (le plus récent en premier)
            
            if potential_files:
                latest_file = os.path.join(results_dir, potential_files[0])
                logging.info(f"Progression à 100% pour la tâche {job_id}, fichier de résultats potentiel trouvé: {latest_file}")
                jobs[job_id]["status"] = "completed"
                jobs[job_id]["result_file"] = latest_file
                if "end_time" not in jobs[job_id] or not jobs[job_id]["end_time"]:
                    jobs[job_id]["end_time"] = datetime.now().isoformat()
                job_info = jobs[job_id].copy()
    
    return job_info

@app.get("/results/{job_id}")
async def get_results(job_id: str, format: str = "xlsx"):
    """Récupère les résultats d'une analyse terminée"""
    job_info = get_job_status(job_id, jobs)
    
    if job_info["status"] != "completed":
        raise HTTPException(status_code=400, detail="L'analyse n'est pas encore terminée")
    
    if not job_info["result_file"] or not os.path.exists(job_info["result_file"]):
        raise HTTPException(status_code=404, detail="Fichier de résultats non trouvé")
    
    # Si le format demandé est CSV, convertir le fichier Excel en CSV
    if format.lower() == "csv":
        try:
            # Lire le fichier Excel
            df = pd.read_excel(job_info["result_file"])
            
            # Créer un fichier CSV temporaire
            csv_file = job_info["result_file"].replace(".xlsx", ".csv")
            df.to_csv(csv_file, index=False, encoding='utf-8')
            
            return FileResponse(
                csv_file,
                filename=os.path.basename(csv_file),
                media_type="text/csv"
            )
        except Exception as e:
            logging.error(f"Erreur lors de la conversion en CSV: {str(e)}")
            raise HTTPException(status_code=500, detail="Erreur lors de la conversion en CSV")
    
    # Par défaut, renvoyer le fichier Excel
    return FileResponse(
        job_info["result_file"],
        filename=os.path.basename(job_info["result_file"]),
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    )

@app.get("/force-complete/{job_id}")
async def force_complete_job(job_id: str):
    """Force l'arrêt de l'analyse et renvoie les résultats"""
    logging.info(f"Tentative de forcer la complétion de la tâche {job_id}")
    
    if job_id not in jobs:
        raise HTTPException(status_code=404, detail="Tâche non trouvée")
    
    job_info = jobs[job_id]
    
    # Vérifier si le fichier de résultats existe
    result_file = job_info.get("result_file")
    if result_file and os.path.exists(result_file):
        logging.info(f"Fichier de résultats trouvé pour la tâche {job_id}, mise à jour du statut à 'completed'")
        jobs[job_id]["status"] = "completed"
        jobs[job_id]["progress"] = 100
        jobs[job_id]["message"] = "Analyse terminée avec succès (forcé)"
        if "end_time" not in jobs[job_id] or not jobs[job_id]["end_time"]:
            jobs[job_id]["end_time"] = datetime.now().isoformat()
        return {"status": "completed", "result_file": result_file}
    else:
        # Chercher des fichiers de résultats potentiels
        results_dir = "results"
        potential_files = [f for f in os.listdir(results_dir) if f.startswith("seo_suggestions_")]
        potential_files.sort(reverse=True)  # Trier par ordre décroissant (le plus récent en premier)
        
        if potential_files:
            latest_file = os.path.join(results_dir, potential_files[0])
            logging.info(f"Aucun fichier de résultats associé à la tâche {job_id}, mais un fichier potentiel a été trouvé: {latest_file}")
            jobs[job_id]["status"] = "completed"
            jobs[job_id]["progress"] = 100
            jobs[job_id]["message"] = "Analyse terminée avec succès (forcé)"
            jobs[job_id]["result_file"] = latest_file
            if "end_time" not in jobs[job_id] or not jobs[job_id]["end_time"]:
                jobs[job_id]["end_time"] = datetime.now().isoformat()
            return {"status": "completed", "result_file": latest_file}
        else:
            logging.warning(f"Aucun fichier de résultats trouvé pour la tâche {job_id}")
            raise HTTPException(status_code=404, detail="Aucun fichier de résultats trouvé")

@app.post("/job/{job_id}/stop")
async def stop_job(job_id: str):
    """Arrête une analyse en cours"""
    logging.info(f"Tentative d'arrêt de la tâche {job_id}")
    
    if job_id not in jobs:
        raise HTTPException(status_code=404, detail="Tâche non trouvée")
    
    # Vérifier si la tâche est en cours
    if jobs[job_id]["status"] != "running":
        return {"message": "La tâche n'est pas en cours d'exécution"}
    
    # Vérifier si le fichier de résultats existe
    result_file = jobs[job_id].get("result_file")
    if result_file and os.path.exists(result_file):
        logging.info(f"Fichier de résultats trouvé pour la tâche {job_id}, mise à jour du statut à 'completed'")
        jobs[job_id]["status"] = "completed"
        jobs[job_id]["progress"] = 100
        jobs[job_id]["message"] = "Analyse terminée avec succès (arrêtée manuellement)"
        if "end_time" not in jobs[job_id] or not jobs[job_id]["end_time"]:
            jobs[job_id]["end_time"] = datetime.now().isoformat()
        return {"status": "completed", "result_file": result_file}
    else:
        # Chercher des fichiers de résultats potentiels
        results_dir = "results"
        potential_files = [f for f in os.listdir(results_dir) if f.startswith("seo_suggestions_")]
        potential_files.sort(reverse=True)  # Trier par ordre décroissant (le plus récent en premier)
        
        if potential_files:
            latest_file = os.path.join(results_dir, potential_files[0])
            logging.info(f"Aucun fichier de résultats associé à la tâche {job_id}, mais un fichier potentiel a été trouvé: {latest_file}")
            jobs[job_id]["status"] = "completed"
            jobs[job_id]["progress"] = 100
            jobs[job_id]["message"] = "Analyse terminée avec succès (arrêtée manuellement)"
            jobs[job_id]["result_file"] = latest_file
            if "end_time" not in jobs[job_id] or not jobs[job_id]["end_time"]:
                jobs[job_id]["end_time"] = datetime.now().isoformat()
            return {"status": "completed", "result_file": latest_file}
        else:
            logging.warning(f"Aucun fichier de résultats trouvé pour la tâche {job_id}")
            jobs[job_id]["status"] = "failed"
            jobs[job_id]["message"] = "Analyse arrêtée manuellement, aucun résultat disponible"
            if "end_time" not in jobs[job_id] or not jobs[job_id]["end_time"]:
                jobs[job_id]["end_time"] = datetime.now().isoformat()
            return {"status": "failed", "message": "Analyse arrêtée, aucun résultat disponible"}

@app.get("/download-sample/{file_type}")
async def download_sample(file_type: str):
    """Télécharge un fichier exemple"""
    sample_files = {
        "content": "static/samples/sample-content.xlsx",
        "links": "static/samples/sample-links.xlsx",
        "gsc": "static/samples/sample-gsc.xlsx"
    }
    
    if file_type not in sample_files:
        raise HTTPException(status_code=400, detail="Type de fichier non valide")
    
    file_path = sample_files[file_type]
    if not os.path.exists(file_path):
        raise HTTPException(status_code=404, detail="Fichier exemple non trouvé")
    
    return FileResponse(
        file_path,
        filename=os.path.basename(file_path),
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    )

@app.websocket("/ws/{job_id}")
async def websocket_endpoint(websocket: WebSocket, job_id: str):
    await manager.connect(websocket, job_id)
    try:
        # Envoyer le statut initial
        if job_id in jobs:
            await websocket.send_json(jobs[job_id])
        
        while True:
            # Attendre un message du client (ping)
            await websocket.receive_text()
            # Envoyer le statut actuel
            if job_id in jobs:
                await websocket.send_json(jobs[job_id])
    except WebSocketDisconnect:
        manager.disconnect(websocket, job_id)
    except Exception as e:
        logging.error(f"Erreur WebSocket: {str(e)}")
        manager.disconnect(websocket, job_id)

# Fonction pour exécuter l'analyse en arrière-plan
async def run_analysis(job_id: str, content_file: str, links_file: Optional[str], gsc_file: Optional[str], config: Dict[str, Any]):
    """Exécute l'analyse SEO en arrière-plan"""
    try:
        logging.info(f"Démarrage de l'analyse pour la tâche {job_id}")
        
        # Mettre à jour le statut
        jobs[job_id]["status"] = "running"
        jobs[job_id]["message"] = "Initialisation de l'analyse"
        
        # Charger les règles de maillage
        rules = None
        if os.path.exists("segment_rules.json"):
            with open("segment_rules.json", "r", encoding="utf-8") as f:
                rules = json.load(f)
                logging.info(f"Règles de maillage chargées: {len(rules)} règles")
        else:
            logging.info("Aucune règle de maillage trouvée")
        
        # Créer l'analyseur SEO
        logging.info(f"Création de l'analyseur SEO pour la tâche {job_id}")
        analyzer = SEOAnalyzer(
            progress_callback=lambda desc, current, total: update_job_progress(job_id, desc, current, total)
        )
        
        # Lancer l'analyse
        logging.info(f"Lancement de l'analyse pour la tâche {job_id}")
        result_file = await analyzer.analyze(
            content_file=content_file,
            links_file=links_file,
            gsc_file=gsc_file,
            min_similarity=config.get("min_similarity", 0.2),
            anchor_suggestions=config.get("anchor_suggestions", 3),
            linking_rules=rules
        )
        
        # Vérifier si le fichier de résultats existe
        if result_file and os.path.exists(result_file):
            logging.info(f"Analyse terminée avec succès pour la tâche {job_id}, fichier de résultats: {result_file}")
        else:
            logging.warning(f"Analyse terminée mais fichier de résultats non trouvé pour la tâche {job_id}")
        
        # Mettre à jour le statut
        logging.info(f"Mise à jour du statut de la tâche {job_id} à 'completed'")
        jobs[job_id]["status"] = "completed"
        jobs[job_id]["progress"] = 100
        jobs[job_id]["message"] = "Analyse terminée avec succès"
        jobs[job_id]["result_file"] = result_file
        jobs[job_id]["end_time"] = datetime.now().isoformat()
        
        # Envoyer une mise à jour WebSocket
        await manager.send_job_update(job_id, jobs[job_id])
        
    except Exception as e:
        logging.error(f"Erreur lors de l'analyse pour la tâche {job_id}: {str(e)}")
        jobs[job_id]["status"] = "failed"
        jobs[job_id]["message"] = f"Erreur: {str(e)}"
        jobs[job_id]["end_time"] = datetime.now().isoformat()
        # Initialiser result_file à None en cas d'erreur
        jobs[job_id]["result_file"] = None

# Fonction pour mettre à jour la progression d'une tâche
def update_job_progress(job_id: str, desc: str, current: int, total: int):
    """Met à jour la progression d'une tâche"""
    if job_id in jobs:
        progress = int((current / total) * 100) if total > 0 else 0
        logging.info(f"Mise à jour de la progression pour la tâche {job_id}: {progress}% - {desc}")
        jobs[job_id]["progress"] = progress
        jobs[job_id]["message"] = desc
        
        # Envoyer une mise à jour WebSocket - sans await car nous sommes dans une fonction synchrone
        asyncio.create_task(manager.send_job_update(job_id, jobs[job_id]))
        
        # Vérifier si la tâche est terminée
        if progress == 100 and ("result_file" in jobs[job_id] and jobs[job_id]["result_file"]):
            if os.path.exists(jobs[job_id]["result_file"]):
                jobs[job_id]["status"] = "completed"
                logging.info(f"Tâche {job_id} marquée comme terminée")
        
        # Vérifier si la progression est à 100% mais le statut n'est pas "completed", vérifier s'il y a des fichiers de résultats
        elif progress == 100 and ("result_file" in jobs[job_id] and jobs[job_id]["result_file"]):
            results_dir = "results"
            if os.path.exists(results_dir):
                potential_files = [f for f in os.listdir(results_dir) if f.startswith("seo_suggestions_")]
                potential_files.sort(reverse=True)  # Trier par ordre décroissant (le plus récent en premier)
                
                if potential_files:
                    latest_file = os.path.join(results_dir, potential_files[0])
                    logging.info(f"Progression à 100% pour la tâche {job_id}, fichier de résultats potentiel trouvé: {latest_file}")
                    jobs[job_id]["status"] = "completed"
                    jobs[job_id]["result_file"] = latest_file
                    if "end_time" not in jobs[job_id] or not jobs[job_id]["end_time"]:
                        jobs[job_id]["end_time"] = datetime.now().isoformat()

# Point d'entrée pour uvicorn
if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
