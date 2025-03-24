import React from 'react';
import { Box, Typography, Button, Grid, Card, CardContent, CardActions, Paper } from '@mui/material';
import { Link as RouterLink } from 'react-router-dom';
import LinkIcon from '@mui/icons-material/Link';
import SettingsIcon from '@mui/icons-material/Settings';
import AnalyticsIcon from '@mui/icons-material/Analytics';
import DownloadIcon from '@mui/icons-material/Download';

const HomePage = () => {
  return (
    <Box>
      {/* Hero Section */}
      <Paper 
        elevation={3}
        sx={{ 
          p: 5, 
          mb: 5, 
          borderRadius: 2,
          background: 'linear-gradient(45deg, #2196F3 30%, #21CBF3 90%)',
          color: 'white'
        }}
      >
        <Grid container spacing={3} alignItems="center">
          <Grid item xs={12} md={8}>
            <Typography variant="h3" component="h1" gutterBottom>
              SEO Internal Linking Tool
            </Typography>
            <Typography variant="h6" paragraph>
              Optimisez votre maillage interne pour améliorer votre référencement naturel
            </Typography>
            <Typography variant="body1" paragraph>
              Notre outil utilise l'intelligence artificielle (BERT) pour analyser la pertinence sémantique entre vos pages 
              et suggérer des liens internes pertinents, améliorant ainsi la structure de votre site et son référencement.
            </Typography>
            <Button 
              variant="contained" 
              color="secondary" 
              size="large"
              component={RouterLink}
              to="/analysis"
              sx={{ mt: 2 }}
            >
              Commencer l'analyse
            </Button>
          </Grid>
          <Grid item xs={12} md={4} sx={{ textAlign: 'center' }}>
            <LinkIcon sx={{ fontSize: 180, opacity: 0.8 }} />
          </Grid>
        </Grid>
      </Paper>

      {/* Features Section */}
      <Typography variant="h4" component="h2" gutterBottom sx={{ mb: 3 }}>
        Fonctionnalités principales
      </Typography>

      <Grid container spacing={4}>
        <Grid item xs={12} md={4}>
          <Card sx={{ height: '100%', display: 'flex', flexDirection: 'column' }}>
            <CardContent sx={{ flexGrow: 1 }}>
              <AnalyticsIcon color="primary" sx={{ fontSize: 40, mb: 2 }} />
              <Typography variant="h5" component="h3" gutterBottom>
                Analyse Sémantique Avancée
              </Typography>
              <Typography variant="body2" color="text.secondary">
                Utilisation du modèle BERT multilingue pour une analyse contextuelle approfondie du contenu de vos pages.
                Support du traitement GPU pour des performances optimales.
              </Typography>
            </CardContent>
            <CardActions>
              <Button 
                size="small" 
                color="primary"
                component={RouterLink}
                to="/analysis"
              >
                Lancer une analyse
              </Button>
            </CardActions>
          </Card>
        </Grid>

        <Grid item xs={12} md={4}>
          <Card sx={{ height: '100%', display: 'flex', flexDirection: 'column' }}>
            <CardContent sx={{ flexGrow: 1 }}>
              <SettingsIcon color="primary" sx={{ fontSize: 40, mb: 2 }} />
              <Typography variant="h5" component="h3" gutterBottom>
                Gestion des Règles de Maillage
              </Typography>
              <Typography variant="body2" color="text.secondary">
                Interface matricielle pour la configuration des règles de maillage. Règles personnalisables par type de page (blog, catégorie, produit).
                Limites min/max de liens configurables.
              </Typography>
            </CardContent>
            <CardActions>
              <Button 
                size="small" 
                color="primary"
                component={RouterLink}
                to="/rules"
              >
                Configurer les règles
              </Button>
            </CardActions>
          </Card>
        </Grid>

        <Grid item xs={12} md={4}>
          <Card sx={{ height: '100%', display: 'flex', flexDirection: 'column' }}>
            <CardContent sx={{ flexGrow: 1 }}>
              <DownloadIcon color="primary" sx={{ fontSize: 40, mb: 2 }} />
              <Typography variant="h5" component="h3" gutterBottom>
                Téléchargement d'exemples
              </Typography>
              <Typography variant="body2" color="text.secondary">
                Téléchargez des fichiers exemples pour comprendre le format attendu pour l'analyse.
                Formats supportés : Excel (.xlsx, .xls).
              </Typography>
            </CardContent>
            <CardActions>
              <Button 
                size="small" 
                color="primary"
                component="a"
                href="/download-sample/content"
              >
                Exemple de contenu
              </Button>
              <Button 
                size="small" 
                color="primary"
                component="a"
                href="/download-sample/links"
              >
                Exemple de liens
              </Button>
            </CardActions>
          </Card>
        </Grid>
      </Grid>

      {/* How it works Section */}
      <Typography variant="h4" component="h2" gutterBottom sx={{ mt: 6, mb: 3 }}>
        Comment ça marche
      </Typography>

      <Paper elevation={1} sx={{ p: 3, mb: 4, borderRadius: 2 }}>
        <Grid container spacing={2}>
          <Grid item xs={12} md={3}>
            <Box sx={{ textAlign: 'center', p: 2 }}>
              <Typography variant="h5" component="div" sx={{ mb: 1 }}>
                1
              </Typography>
              <Typography variant="h6" component="div">
                Téléchargez vos fichiers
              </Typography>
              <Typography variant="body2" color="text.secondary">
                Importez votre fichier de contenu, de liens existants et de données GSC (optionnel).
              </Typography>
            </Box>
          </Grid>
          <Grid item xs={12} md={3}>
            <Box sx={{ textAlign: 'center', p: 2 }}>
              <Typography variant="h5" component="div" sx={{ mb: 1 }}>
                2
              </Typography>
              <Typography variant="h6" component="div">
                Configurez les règles
              </Typography>
              <Typography variant="body2" color="text.secondary">
                Définissez les règles de maillage entre les différents types de pages.
              </Typography>
            </Box>
          </Grid>
          <Grid item xs={12} md={3}>
            <Box sx={{ textAlign: 'center', p: 2 }}>
              <Typography variant="h5" component="div" sx={{ mb: 1 }}>
                3
              </Typography>
              <Typography variant="h6" component="div">
                Lancez l'analyse
              </Typography>
              <Typography variant="body2" color="text.secondary">
                Notre algorithme analyse le contenu et génère des suggestions de liens pertinents.
              </Typography>
            </Box>
          </Grid>
          <Grid item xs={12} md={3}>
            <Box sx={{ textAlign: 'center', p: 2 }}>
              <Typography variant="h5" component="div" sx={{ mb: 1 }}>
                4
              </Typography>
              <Typography variant="h6" component="div">
                Exportez les résultats
              </Typography>
              <Typography variant="body2" color="text.secondary">
                Téléchargez les suggestions de liens au format Excel pour les implémenter sur votre site.
              </Typography>
            </Box>
          </Grid>
        </Grid>
      </Paper>

      {/* CTA Section */}
      <Box sx={{ textAlign: 'center', mt: 6, mb: 4 }}>
        <Typography variant="h5" component="div" gutterBottom>
          Prêt à optimiser votre maillage interne ?
        </Typography>
        <Button 
          variant="contained" 
          color="primary" 
          size="large"
          component={RouterLink}
          to="/analysis"
          sx={{ mt: 2 }}
        >
          Commencer maintenant
        </Button>
      </Box>
    </Box>
  );
};

export default HomePage;
