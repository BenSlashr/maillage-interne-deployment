from typing import Dict, Any, List, Optional
import json
import os
import logging

class LinkingRules:
    """
    Classe pour gérer les règles de maillage entre segments
    """
    
    def __init__(self):
        self.rules = {}
        self.load_rules()
    
    def load_rules(self) -> None:
        """
        Charge les règles de maillage depuis le fichier
        """
        try:
            if os.path.exists("segment_rules.json"):
                with open("segment_rules.json", "r", encoding="utf-8") as f:
                    self.rules = json.load(f)
                logging.info("Règles de maillage chargées depuis segment_rules.json")
            else:
                self.rules = self.get_default_rules()
                logging.info("Aucun fichier de règles trouvé, utilisation des règles par défaut")
        except Exception as e:
            self.rules = self.get_default_rules()
            logging.error(f"Erreur lors du chargement des règles: {str(e)}")
    
    def save_rules(self) -> None:
        """
        Sauvegarde les règles de maillage dans un fichier
        """
        try:
            with open("segment_rules.json", "w", encoding="utf-8") as f:
                json.dump(self.rules, f, ensure_ascii=False, indent=4)
            logging.info("Règles de maillage sauvegardées dans segment_rules.json")
        except Exception as e:
            logging.error(f"Erreur lors de la sauvegarde des règles: {str(e)}")
    
    def get_default_rules(self) -> Dict[str, Dict[str, Dict[str, int]]]:
        """
        Retourne les règles de maillage par défaut
        
        Returns:
            Dict: Règles de maillage par défaut
        """
        return {
            "blog": {
                "blog": {"min_links": 3, "max_links": 5},      # Articles liés thématiquement
                "categorie": {"min_links": 2, "max_links": 4}, # Catégories principales du sujet
                "produit": {"min_links": 1, "max_links": 3}    # Produits mentionnés dans l'article
            },
            "categorie": {
                "blog": {"min_links": 1, "max_links": 3},      # Articles pertinents
                "categorie": {"min_links": 1, "max_links": 3}, # Catégories complémentaires
                "produit": {"min_links": 1, "max_links": 2}    # Produits phares
            },
            "produit": {
                "blog": {"min_links": 1, "max_links": 2},      # Articles/guides d'utilisation
                "categorie": {"min_links": 1, "max_links": 2}, # Catégories parentes
                "produit": {"min_links": 1, "max_links": 2}    # Produits complémentaires/accessoires
            }
        }
    
    def set_rules(self, rules: Dict[str, Dict[str, Dict[str, int]]]) -> None:
        """
        Définit les règles de maillage
        
        Args:
            rules: Règles de maillage
        """
        self.rules = rules
        self.save_rules()
    
    def get_rules(self) -> Dict[str, Dict[str, Dict[str, int]]]:
        """
        Retourne les règles de maillage
        
        Returns:
            Dict: Règles de maillage
        """
        return self.rules
    
    def get_rule(self, source_type: str, target_type: str) -> Dict[str, int]:
        """
        Retourne la règle de maillage pour un type source et un type cible
        
        Args:
            source_type: Type de page source
            target_type: Type de page cible
            
        Returns:
            Dict: Règle de maillage (min_links, max_links)
        """
        if source_type in self.rules and target_type in self.rules[source_type]:
            return self.rules[source_type][target_type]
        else:
            return {"min_links": 0, "max_links": 0}
    
    def set_rule(self, source_type: str, target_type: str, min_links: int, max_links: int) -> None:
        """
        Définit une règle de maillage
        
        Args:
            source_type: Type de page source
            target_type: Type de page cible
            min_links: Nombre minimum de liens
            max_links: Nombre maximum de liens
        """
        if source_type not in self.rules:
            self.rules[source_type] = {}
        
        self.rules[source_type][target_type] = {
            "min_links": min_links,
            "max_links": max_links
        }
        
        self.save_rules()
    
    def get_segments(self) -> List[str]:
        """
        Retourne la liste des segments
        
        Returns:
            List: Liste des segments
        """
        segments = set()
        
        for source_type in self.rules:
            segments.add(source_type)
            for target_type in self.rules[source_type]:
                segments.add(target_type)
        
        return sorted(list(segments))
    
    def validate_rules(self) -> bool:
        """
        Valide les règles de maillage
        
        Returns:
            bool: True si les règles sont valides, False sinon
        """
        for source_type, targets in self.rules.items():
            for target_type, rule in targets.items():
                if "min_links" not in rule or "max_links" not in rule:
                    return False
                
                min_links = rule["min_links"]
                max_links = rule["max_links"]
                
                if not isinstance(min_links, int) or not isinstance(max_links, int):
                    return False
                
                if min_links < 0 or max_links < 0:
                    return False
                
                if min_links > max_links:
                    return False
        
        return True
