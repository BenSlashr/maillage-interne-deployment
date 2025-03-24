# Configuration des colonnes du fichier
FILE_COLUMNS = {
    'url': 'Adresse',
    'type': 'Segments',
    'content1': 'Extracteur 1 1',  # Premier extracteur
    'content2': 'Extracteur 2 1',  # Deuxième extracteur
    'status': 'Statut',
    'http_code': 'Code HTTP',
    'source': 'Source',           # URL source du lien
    'target': 'Destination'       # URL destination du lien
}

# Configuration du modèle BERT
MODEL_NAME = "distiluse-base-multilingual-cased-v2"
BATCH_SIZE = 32

# Configuration des suggestions GSC
GSC_CONFIG = {
    'min_clicks': 10,
    'min_impressions': 100,
    'max_position': 20,
    'min_semantic_similarity': 0.5
}

# Configuration des suggestions
SUGGESTIONS_CONFIG = {
    'exact': {
        'min_similarity': 0.7,
        'max_suggestions': 10
    },
    'semantic': {
        'min_similarity': 0.35,    # Seuil abaissé pour avoir plus de suggestions
        'max_suggestions': 15      # Augmenté pour avoir plus d'options parmi lesquelles choisir
    }
}

# Configuration des règles de maillage par défaut
DEFAULT_LINKING_RULES = {
    'blog': {
        'blog': {'min_links': 3, 'max_links': 5},      # Articles liés thématiquement
        'categorie': {'min_links': 2, 'max_links': 4}, # Catégories principales du sujet
        'produit': {'min_links': 1, 'max_links': 3}    # Produits mentionnés dans l'article
    },
    'categorie': {
        'blog': {'min_links': 1, 'max_links': 3},      # Articles pertinents
        'categorie': {'min_links': 1, 'max_links': 3}, # Catégories complémentaires
        'produit': {'min_links': 1, 'max_links': 2}    # Produits phares
    },
    'produit': {
        'blog': {'min_links': 1, 'max_links': 2},      # Articles/guides d'utilisation
        'categorie': {'min_links': 1, 'max_links': 2}, # Catégories parentes
        'produit': {'min_links': 1, 'max_links': 2}    # Produits complémentaires/accessoires
    }
}

# Mapping des segments vers les types standards
SEGMENT_MAPPING = {
    'category': 'categorie',
    'categories': 'categorie',
    'categorie': 'categorie',
    'blog': 'blog',
    'blog-post': 'blog',
    'article': 'blog',
    'post': 'blog',
    'produit': 'produit',
    'product': 'produit'
}
