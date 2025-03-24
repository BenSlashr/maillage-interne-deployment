import pandas as pd
import numpy as np
from sentence_transformers import SentenceTransformer
from sklearn.metrics.pairwise import cosine_similarity
import logging
import os
import json
import time
from datetime import datetime
import torch
from typing import Dict, List, Callable, Optional, Tuple, Any
import nltk
from nltk.corpus import stopwords
from urllib.parse import urlparse

# Télécharger les stopwords NLTK si nécessaire
try:
    nltk.download('stopwords', quiet=True)
    STOP_WORDS = set(stopwords.words('french'))
except:
    STOP_WORDS = set()

# Configuration du modèle BERT
MODEL_NAME = "distiluse-base-multilingual-cased-v2"
BATCH_SIZE = 32

class SEOAnalyzer:
    def __init__(self, progress_callback: Optional[Callable[[str, int, int], None]] = None):
        """
        Initialise l'analyseur SEO avec le modèle BERT
        
        Args:
            progress_callback: Fonction de callback pour suivre la progression
        """
        self.progress_callback = progress_callback
        
        # Initialiser le modèle BERT
        try:
            self.model = SentenceTransformer(MODEL_NAME)
            device_name = 'mps' if torch.backends.mps.is_available() else 'cuda' if torch.cuda.is_available() else 'cpu'
            self.model.to(device_name)
            logging.info(f"Utilisation du périphérique PyTorch: {device_name}")
            logging.info(f"Modèle SentenceTransformer chargé: {MODEL_NAME}")
        except Exception as e:
            logging.error(f"Erreur lors du chargement du modèle: {str(e)}")
            raise e
    
    async def analyze(
        self,
        content_file: str,
        links_file: Optional[str] = None,
        gsc_file: Optional[str] = None,
        min_similarity: float = 0.2,
        anchor_suggestions: int = 3,
        linking_rules: Optional[Dict[str, Dict[str, Dict[str, int]]]] = None
    ) -> str:
        """
        Analyse le contenu et génère des suggestions de maillage interne
        
        Args:
            content_file: Chemin vers le fichier de contenu
            links_file: Chemin vers le fichier de liens existants
            gsc_file: Chemin vers le fichier GSC
            min_similarity: Score minimum de similarité pour les suggestions
            anchor_suggestions: Nombre de suggestions d'ancres
            linking_rules: Règles de maillage entre segments
            
        Returns:
            Chemin vers le fichier de résultats
        """
        start_time = time.time()
        logging.info("Début de l'analyse SEO")
        
        # Charger les fichiers
        self._update_progress("Initialisation de l'analyse...", 0, 5)
        
        # Charger le fichier de contenu
        content_df = self._load_content_file(content_file)
        num_pages_original = len(content_df)
        self._update_progress(f"Fichier de contenu chargé ({num_pages_original} pages)", 1, 5)
        
        # Charger le fichier de liens existants si fourni
        existing_links = self._load_links_file(links_file) if links_file else pd.DataFrame(columns=["Source", "Destination"])
        num_existing_links = len(existing_links)
        self._update_progress(f"Fichier de liens existants chargé ({num_existing_links} liens)", 2, 5)
        
        # Charger le fichier GSC si fourni
        gsc_data = self._load_gsc_file(gsc_file) if gsc_file else pd.DataFrame(columns=["URL", "Clics", "Impressions", "Position"])
        num_gsc_entries = len(gsc_data)
        self._update_progress(f"Fichier GSC chargé ({num_gsc_entries} entrées)", 3, 5)
        
        # Prétraiter les données
        self._update_progress("Prétraitement des données...", 4, 5)
        content_df = self._preprocess_content(content_df)
        num_pages_after_preprocess = len(content_df)
        
        # Journaliser si des pages ont été filtrées pendant le prétraitement
        if num_pages_original != num_pages_after_preprocess:
            logging.info(f"{num_pages_original - num_pages_after_preprocess} pages ont été filtrées pendant le prétraitement")
            self._update_progress(f"Prétraitement terminé - {num_pages_after_preprocess}/{num_pages_original} pages conservées", 5, 5)
        else:
            self._update_progress(f"Prétraitement terminé pour {num_pages_after_preprocess} pages", 5, 5)
        
        # Générer les embeddings pour le contenu
        self._update_progress(f"Préparation des embeddings pour {num_pages_after_preprocess} pages...", 0, content_df.shape[0])
        embeddings = self._generate_embeddings(content_df)
        
        # Calculer la matrice de similarité
        self._update_progress("Calcul de la matrice de similarité...", 0, 1)
        similarity_matrix = cosine_similarity(embeddings)
        self._update_progress(f"Matrice de similarité calculée ({num_pages_after_preprocess}x{num_pages_after_preprocess})", 1, 1)
        
        # Vérifier que la taille de la matrice de similarité correspond au nombre de lignes dans content_df
        if similarity_matrix.shape[0] != content_df.shape[0]:
            error_msg = f"Incohérence de dimensions: matrice de similarité ({similarity_matrix.shape[0]}x{similarity_matrix.shape[1]}) vs DataFrame de contenu ({content_df.shape[0]} lignes)"
            logging.error(error_msg)
            raise ValueError(error_msg)
        
        # Générer les suggestions de liens
        self._update_progress(f"Début de l'analyse des {num_pages_after_preprocess} pages...", 0, num_pages_after_preprocess)
        suggestions_df = self._generate_suggestions(
            content_df,
            similarity_matrix,
            existing_links,
            gsc_data,
            min_similarity,
            anchor_suggestions,
            linking_rules
        )
        
        # Sauvegarder les résultats
        self._update_progress("Sauvegarde des résultats...", 0, 1)
        result_file = self._save_results(suggestions_df)
        self._update_progress("Analyse terminée", 1, 1)
        
        elapsed_time = time.time() - start_time
        logging.info(f"Analyse terminée en {elapsed_time:.2f} secondes")
        
        return result_file
    
    def _update_progress(self, description: str, current: int, total: int):
        """Met à jour la progression via le callback"""
        if self.progress_callback:
            self.progress_callback(description, current, total)
    
    def _load_content_file(self, file_path: str) -> pd.DataFrame:
        """Charge le fichier de contenu"""
        try:
            df = pd.read_excel(file_path)
            required_columns = ["Adresse", "Segments", "Extracteur 1 1"]
            for col in required_columns:
                if col not in df.columns:
                    raise ValueError(f"Colonne requise manquante dans le fichier de contenu: {col}")
            
            # Renommer les colonnes pour faciliter l'accès
            column_mapping = {
                "Adresse": "url",
                "Segments": "type",
                "Extracteur 1 1": "content1",
                "Extracteur 2 1": "content2" if "Extracteur 2 1" in df.columns else None
            }
            
            # Supprimer les mappings None
            column_mapping = {k: v for k, v in column_mapping.items() if v is not None}
            
            df = df.rename(columns=column_mapping)
            
            # Filtrer les lignes avec du contenu
            df = df.dropna(subset=["content1"])
            
            return df
        except Exception as e:
            logging.error(f"Erreur lors du chargement du fichier de contenu: {str(e)}")
            raise e
    
    def _load_links_file(self, file_path: str) -> pd.DataFrame:
        """Charge le fichier de liens existants"""
        try:
            df = pd.read_excel(file_path)
            required_columns = ["Source", "Destination"]
            for col in required_columns:
                if col not in df.columns:
                    raise ValueError(f"Colonne requise manquante dans le fichier de liens: {col}")
            
            return df
        except Exception as e:
            logging.error(f"Erreur lors du chargement du fichier de liens: {str(e)}")
            raise e
    
    def _load_gsc_file(self, file_path: str) -> pd.DataFrame:
        """Charge le fichier GSC"""
        try:
            df = pd.read_excel(file_path)
            required_columns = ["URL", "Clics", "Impressions", "Position"]
            for col in required_columns:
                if col not in df.columns:
                    raise ValueError(f"Colonne requise manquante dans le fichier GSC: {col}")
            
            return df
        except Exception as e:
            logging.error(f"Erreur lors du chargement du fichier GSC: {str(e)}")
            raise e
    
    def _preprocess_content(self, df: pd.DataFrame) -> pd.DataFrame:
        """Prétraite le contenu pour l'analyse"""
        # Normaliser les URLs
        df["url"] = df["url"].apply(self._normalize_url)
        
        # Normaliser les types de pages
        df["type"] = df["type"].apply(self._normalize_segment)
        
        # Combiner le contenu si content2 existe
        if "content2" in df.columns:
            df["combined_content"] = df.apply(
                lambda row: str(row["content1"]) + " " + str(row["content2"]) if pd.notnull(row["content2"]) else str(row["content1"]),
                axis=1
            )
        else:
            df["combined_content"] = df["content1"].astype(str)
        
        # Nettoyer le contenu
        df["combined_content"] = df["combined_content"].apply(self._clean_text)
        
        return df
    
    def _normalize_url(self, url: str) -> str:
        """Normalise une URL"""
        if pd.isna(url):
            return ""
        
        url = str(url).strip()
        
        # Supprimer le protocole et www
        parsed = urlparse(url)
        normalized = parsed.netloc + parsed.path
        
        # Supprimer les slashes finaux
        normalized = normalized.rstrip("/")
        
        # Ajouter un slash au début si nécessaire
        if not normalized.startswith("/") and parsed.netloc:
            normalized = "/" + normalized
        
        return normalized.lower()
    
    def _normalize_segment(self, segment: str) -> str:
        """Normalise un segment"""
        if pd.isna(segment):
            return "unknown"
        
        segment = str(segment).lower().strip()
        
        # Mapping des segments
        segment_mapping = {
            "category": "categorie",
            "categories": "categorie",
            "categorie": "categorie",
            "blog": "blog",
            "blog-post": "blog",
            "article": "blog",
            "post": "blog",
            "produit": "produit",
            "product": "produit"
        }
        
        # Appliquer le mapping ou utiliser le segment original
        for key, value in segment_mapping.items():
            if key in segment:
                return value
        
        return segment
    
    def _clean_text(self, text: str) -> str:
        """Nettoie le texte pour l'analyse"""
        if pd.isna(text):
            return ""
        
        text = str(text).lower()
        
        # Supprimer les caractères spéciaux
        text = ''.join([c if c.isalnum() or c.isspace() else ' ' for c in text])
        
        # Supprimer les espaces multiples
        text = ' '.join(text.split())
        
        return text
    
    def _generate_embeddings(self, df: pd.DataFrame) -> np.ndarray:
        """Génère les embeddings pour le contenu"""
        texts = df["combined_content"].tolist()
        embeddings = []
        
        # Traiter par lots pour économiser la mémoire
        for i in range(0, len(texts), BATCH_SIZE):
            batch = texts[i:i+BATCH_SIZE]
            batch_embeddings = self.model.encode(batch, show_progress_bar=False)
            embeddings.extend(batch_embeddings)
            # Ajouter des détails sur le nombre d'embeddings générés
            self._update_progress(f"Génération des embeddings ({i + len(batch)}/{len(texts)} pages)", i + len(batch), len(texts))
        
        # Vérification supplémentaire
        if len(embeddings) != len(df):
            logging.error(f"Incohérence de dimensions: {len(embeddings)} embeddings générés pour {len(df)} lignes dans le DataFrame")
        
        return np.array(embeddings)
    
    def _generate_suggestions(
        self,
        content_df: pd.DataFrame,
        similarity_matrix: np.ndarray,
        existing_links: pd.DataFrame,
        gsc_data: pd.DataFrame,
        min_similarity: float,
        anchor_suggestions: int,
        linking_rules: Optional[Dict[str, Dict[str, Dict[str, int]]]] = None
    ) -> pd.DataFrame:
        """Génère les suggestions de liens"""
        suggestions = []
        total_pages = content_df.shape[0]
        
        # Journalisation détaillée des dimensions
        logging.info(f"Dimensions du DataFrame de contenu: {content_df.shape}")
        logging.info(f"Dimensions de la matrice de similarité: {similarity_matrix.shape}")
        
        # Vérifier que la taille de la matrice de similarité correspond au nombre de lignes dans content_df
        if similarity_matrix.shape[0] != total_pages:
            error_msg = f"Incohérence de dimensions dans _generate_suggestions: matrice de similarité ({similarity_matrix.shape[0]}x{similarity_matrix.shape[1]}) vs DataFrame de contenu ({total_pages} lignes)"
            logging.error(error_msg)
            raise ValueError(error_msg)
        
        # Créer un dictionnaire des liens existants pour une recherche rapide
        existing_links_dict = {}
        for _, row in existing_links.iterrows():
            source = self._normalize_url(row["Source"])
            destination = self._normalize_url(row["Destination"])
            if source not in existing_links_dict:
                existing_links_dict[source] = set()
            existing_links_dict[source].add(destination)
        
        # Créer un dictionnaire des données GSC pour une recherche rapide
        gsc_dict = {}
        for _, row in gsc_data.iterrows():
            url = self._normalize_url(row["URL"])
            gsc_dict[url] = {
                "clicks": row["Clics"],
                "impressions": row["Impressions"],
                "position": row["Position"]
            }
        
        self._update_progress(f"Début de l'analyse des {total_pages} pages...", 0, total_pages)
        
        # Vérifier si des règles de maillage sont définies
        has_rules = linking_rules is not None and len(linking_rules) > 0
        logging.info(f"Règles de maillage définies: {has_rules}")
        
        # Pour chaque page source
        for i, source_row in enumerate(content_df.iterrows()):
            # Vérification supplémentaire pour éviter les erreurs d'indexation
            if i >= similarity_matrix.shape[0]:
                logging.error(f"Erreur d'indexation: tentative d'accès à l'indice {i} dans une matrice de taille {similarity_matrix.shape[0]}")
                continue
                
            # Extraire l'index et la ligne
            idx, row = source_row
            
            # Journalisation détaillée
            logging.info(f"Traitement de la page {i+1}/{total_pages} (index={idx})")
            
            source_url = row["url"]
            source_type = row["type"]
            
            # Récupérer les liens existants pour cette source
            existing_destinations = existing_links_dict.get(source_url, set())
            
            # Calculer les scores de similarité pour toutes les destinations potentielles
            similarities = similarity_matrix[i]
            
            suggestions_for_page = 0
            
            # Si des règles de maillage sont définies, les utiliser
            if has_rules and source_type in linking_rules:
                source_rules = linking_rules[source_type]
                
                # Pour chaque type de destination, appliquer les règles de maillage
                for target_type, rule in source_rules.items():
                    min_links = rule.get("min_links", 0)
                    max_links = rule.get("max_links", 0)
                    
                    if min_links <= 0 and max_links <= 0:
                        continue
                    
                    # Filtrer les destinations par type
                    target_indices = content_df[content_df["type"] == target_type].index.tolist()
                    
                    if not target_indices:
                        continue
                    
                    # Calculer les scores pour les destinations de ce type
                    target_scores = []
                    for j in target_indices:
                        if j != idx:  # Ne pas suggérer de liens vers la page elle-même
                            # Trouver l'indice correspondant dans la matrice de similarité
                            j_pos = content_df.index.get_loc(j)
                            if j_pos < similarity_matrix.shape[1]:
                                target_scores.append((j, similarities[j_pos]))
                            else:
                                logging.warning(f"Index {j_pos} hors limites pour la matrice de similarité de taille {similarity_matrix.shape[1]}")
                    
                    # Trier par score de similarité
                    target_scores.sort(key=lambda x: x[1], reverse=True)
                    
                    # Filtrer par score minimum
                    target_scores = [(j, score) for j, score in target_scores if score >= min_similarity]
                    
                    # Limiter au nombre maximum de liens
                    target_scores = target_scores[:max_links]
                    
                    # Ajouter les suggestions
                    for j, score in target_scores:
                        # Récupérer la ligne correspondante
                        target_row = content_df.loc[j]
                        target_url = target_row["url"]
                        
                        # Vérifier si le lien existe déjà
                        if target_url in existing_destinations:
                            continue
                        
                        # Générer des suggestions d'ancres
                        anchor_texts = self._generate_anchor_suggestions(
                            row["combined_content"],
                            target_row["combined_content"],
                            anchor_suggestions
                        )
                        
                        # Calculer le score final
                        final_score = score
                        
                        # Bonus pour les pages GSC performantes
                        if target_url in gsc_dict:
                            gsc_info = gsc_dict[target_url]
                            if gsc_info["clicks"] > 10:
                                final_score *= 1.3
                            if gsc_info["position"] < 10:
                                final_score *= 1.2
                        
                        suggestions.append({
                            "source_url": source_url,
                            "source_type": source_type,
                            "target_url": target_url,
                            "target_type": target_row["type"],
                            "similarity_score": score,
                            "final_score": final_score,
                            "anchor_suggestions": anchor_texts
                        })
                        suggestions_for_page += 1
            
            # Si aucune règle n'est définie ou si le type de source n'a pas de règles, générer des suggestions basées uniquement sur la similarité
            else:
                # Calculer les scores pour toutes les destinations
                target_scores = []
                for j_pos in range(similarity_matrix.shape[1]):
                    if j_pos != i:  # Ne pas suggérer de liens vers la page elle-même
                        score = similarities[j_pos]
                        if score >= min_similarity:
                            # Récupérer l'index correspondant dans le DataFrame
                            j = content_df.index[j_pos]
                            target_scores.append((j, score))
                
                # Trier par score de similarité
                target_scores.sort(key=lambda x: x[1], reverse=True)
                
                # Limiter au nombre maximum de liens (par défaut 5)
                max_default_links = 5
                target_scores = target_scores[:max_default_links]
                
                # Ajouter les suggestions
                for j, score in target_scores:
                    # Récupérer la ligne correspondante
                    target_row = content_df.loc[j]
                    target_url = target_row["url"]
                    
                    # Vérifier si le lien existe déjà
                    if target_url in existing_destinations:
                        continue
                    
                    # Générer des suggestions d'ancres
                    anchor_texts = self._generate_anchor_suggestions(
                        row["combined_content"],
                        target_row["combined_content"],
                        anchor_suggestions
                    )
                    
                    # Calculer le score final
                    final_score = score
                    
                    # Bonus pour les pages GSC performantes
                    if target_url in gsc_dict:
                        gsc_info = gsc_dict[target_url]
                        if gsc_info["clicks"] > 10:
                            final_score *= 1.3
                        if gsc_info["position"] < 10:
                            final_score *= 1.2
                    
                    suggestions.append({
                        "source_url": source_url,
                        "source_type": source_type,
                        "target_url": target_url,
                        "target_type": target_row["type"],
                        "similarity_score": score,
                        "final_score": final_score,
                        "anchor_suggestions": anchor_texts
                    })
                    suggestions_for_page += 1
            
            # Mise à jour de la progression avec des détails sur le nombre de suggestions générées
            self._update_progress(f"Analyse de la page {i+1}/{total_pages} ({suggestions_for_page} suggestions)", i + 1, total_pages)
        
        # Convertir en DataFrame
        suggestions_df = pd.DataFrame(suggestions)
        
        # Trier par score final
        if not suggestions_df.empty:
            suggestions_df = suggestions_df.sort_values(by=["source_url", "final_score"], ascending=[True, False])
        
        return suggestions_df
    
    def _generate_anchor_suggestions(self, source_text: str, target_text: str, num_suggestions: int) -> List[str]:
        """Génère des suggestions d'ancres basées sur le contenu"""
        # Extraire les mots-clés du texte cible
        words = target_text.split()
        
        # Filtrer les stopwords et les mots courts
        filtered_words = [word for word in words if word not in STOP_WORDS and len(word) > 3]
        
        # Compter les occurrences
        word_counts = {}
        for word in filtered_words:
            if word in word_counts:
                word_counts[word] += 1
            else:
                word_counts[word] = 1
        
        # Trier par fréquence
        sorted_words = sorted(word_counts.items(), key=lambda x: x[1], reverse=True)
        
        # Extraire les mots-clés les plus fréquents
        top_keywords = [word for word, _ in sorted_words[:10]]
        
        # Générer des phrases courtes comme suggestions d'ancres
        suggestions = []
        
        # Suggestion 1: Mot-clé principal
        if top_keywords:
            suggestions.append(top_keywords[0].capitalize())
        
        # Suggestion 2: Combinaison de mots-clés
        if len(top_keywords) >= 2:
            suggestions.append(f"{top_keywords[0].capitalize()} {top_keywords[1]}")
        
        # Suggestion 3: Phrase plus longue
        if len(top_keywords) >= 3:
            suggestions.append(f"{top_keywords[0].capitalize()} {top_keywords[1]} {top_keywords[2]}")
        
        # Compléter avec des mots-clés individuels si nécessaire
        for i in range(len(suggestions), num_suggestions):
            if i < len(top_keywords):
                suggestions.append(top_keywords[i].capitalize())
        
        return suggestions[:num_suggestions]
    
    def _save_results(self, suggestions_df: pd.DataFrame) -> str:
        """Sauvegarde les résultats dans un fichier Excel"""
        # Créer le dossier de résultats si nécessaire
        os.makedirs("results", exist_ok=True)
        
        # Générer un nom de fichier unique
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        result_file = f"results/seo_suggestions_{timestamp}.xlsx"
        
        # Renommer les colonnes pour plus de clarté
        if not suggestions_df.empty:
            suggestions_df = suggestions_df.rename(columns={
                "source_url": "URL Source",
                "source_type": "Type Source",
                "target_url": "URL Destination",
                "target_type": "Type Destination",
                "similarity_score": "Score de Similarité",
                "final_score": "Score Final",
                "anchor_suggestions": "Suggestions d'Ancres"
            })
            
            # Convertir la liste de suggestions d'ancres en chaîne
            suggestions_df["Suggestions d'Ancres"] = suggestions_df["Suggestions d'Ancres"].apply(
                lambda x: " | ".join(x) if isinstance(x, list) else str(x)
            )
        
        # Sauvegarder dans un fichier Excel
        with pd.ExcelWriter(result_file, engine='openpyxl') as writer:
            suggestions_df.to_excel(writer, index=False, sheet_name="Suggestions de Liens")
        
        return result_file
