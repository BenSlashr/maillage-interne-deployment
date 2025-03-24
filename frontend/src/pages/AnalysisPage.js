import React, { useState } from 'react';
import { Box, Typography, Paper, Stepper, Step, StepLabel, Button, Divider, Slider, TextField, Grid, Alert, CircularProgress } from '@mui/material';
import { useNavigate } from 'react-router-dom';
import FileUpload from '../components/FileUpload';
import ProgressTracker from '../components/ProgressTracker';
import axios from 'axios';
import config from '../config';

// URL de base de l'API
const API_BASE_URL = config.API_BASE_URL;

const steps = ['Téléchargement des fichiers', 'Configuration', 'Analyse'];

const AnalysisPage = () => {
  const [activeStep, setActiveStep] = useState(0);
  const [contentFile, setContentFile] = useState(null);
  const [linksFile, setLinksFile] = useState(null);
  const [gscFile, setGscFile] = useState(null);
  const [minSimilarity, setMinSimilarity] = useState(0.2);
  const [anchorSuggestions, setAnchorSuggestions] = useState(3);
  const [analyzing, setAnalyzing] = useState(false);
  const [error, setError] = useState(null);
  const [jobId, setJobId] = useState(null);
  const navigate = useNavigate();
  
  // Fonctions pour gérer les téléchargements de fichiers
  const handleContentFileUploaded = (data) => {
    setContentFile(data);
  };
  
  const handleLinksFileUploaded = (data) => {
    setLinksFile(data);
  };
  
  const handleGscFileUploaded = (data) => {
    setGscFile(data);
  };
  
  // Fonction pour démarrer l'analyse
  const startAnalysis = async () => {
    // Vérifier que tous les fichiers nécessaires sont téléchargés
    if (!contentFile) {
      setError('Veuillez télécharger un fichier de contenu');
      return;
    }
    
    setError(null);
    setAnalyzing(true);
    
    // Préparer les données pour l'analyse
    const formData = new FormData();
    formData.append('content_file', contentFile.path);
    
    if (linksFile) {
      formData.append('links_file', linksFile.path);
    }
    
    if (gscFile) {
      formData.append('gsc_file', gscFile.path);
    }
    
    // Ajouter la configuration
    formData.append('config', JSON.stringify({
      min_similarity: minSimilarity,
      anchor_suggestions: anchorSuggestions
    }));
    
    try {
      const response = await axios.post(`${API_BASE_URL}/analyze`, formData);
      setJobId(response.data.job_id);
      setActiveStep(2);
    } catch (error) {
      console.error('Erreur lors du démarrage de l\'analyse:', error);
      setError('Erreur lors du démarrage de l\'analyse');
      setAnalyzing(false);
    }
  };
  
  const handleNext = () => {
    setActiveStep((prevActiveStep) => prevActiveStep + 1);
  };

  const handleBack = () => {
    setActiveStep((prevActiveStep) => prevActiveStep - 1);
  };

  const handleReset = () => {
    setActiveStep(0);
    setContentFile(null);
    setLinksFile(null);
    setGscFile(null);
    setJobId(null);
    setError(null);
  };

  const getStepContent = (step) => {
    switch (step) {
      case 0:
        return (
          <Box>
            <Typography variant="h6" gutterBottom>
              Téléchargez vos fichiers pour l'analyse
            </Typography>
            
            <FileUpload
              title="Fichier de contenu (obligatoire)"
              description="Ce fichier doit contenir les colonnes 'Adresse', 'Segments' et 'Extracteur 1 1'."
              endpoint="/upload/content"
              onFileUploaded={(data) => setContentFile(data)}
            />
            
            <FileUpload
              title="Fichier de liens existants (optionnel)"
              description="Ce fichier doit contenir les colonnes 'Source' et 'Destination'."
              endpoint="/upload/links"
              onFileUploaded={(data) => setLinksFile(data)}
            />
            
            <FileUpload
              title="Fichier GSC (optionnel)"
              description="Ce fichier doit contenir les colonnes 'URL', 'Clics', 'Impressions' et 'Position'."
              endpoint="/upload/gsc"
              onFileUploaded={(data) => setGscFile(data)}
            />
          </Box>
        );
      case 1:
        return (
          <Box>
            <Typography variant="h6" gutterBottom>
              Configuration de l'analyse
            </Typography>
            
            <Paper elevation={3} sx={{ p: 3, mb: 3, borderRadius: 2 }}>
              <Typography variant="subtitle1" gutterBottom>
                Paramètres de similarité
              </Typography>
              
              <Grid container spacing={2} alignItems="center">
                <Grid item xs={12} md={6}>
                  <Typography gutterBottom>
                    Score minimum de similarité: {minSimilarity}
                  </Typography>
                  <Slider
                    value={minSimilarity}
                    onChange={(e, newValue) => setMinSimilarity(newValue)}
                    step={0.05}
                    marks={[
                      { value: 0, label: '0' },
                      { value: 0.5, label: '0.5' },
                      { value: 1, label: '1' }
                    ]}
                    min={0}
                    max={1}
                    valueLabelDisplay="auto"
                  />
                  <Typography variant="body2" color="text.secondary">
                    Plus la valeur est élevée, plus les suggestions seront pertinentes mais moins nombreuses.
                  </Typography>
                </Grid>
                
                <Grid item xs={12} md={6}>
                  <Typography gutterBottom>
                    Nombre de suggestions d'ancres
                  </Typography>
                  <TextField
                    type="number"
                    value={anchorSuggestions}
                    onChange={(e) => setAnchorSuggestions(Math.max(1, Math.min(10, parseInt(e.target.value) || 1)))}
                    InputProps={{ inputProps: { min: 1, max: 10 } }}
                    fullWidth
                  />
                  <Typography variant="body2" color="text.secondary">
                    Nombre de suggestions d'ancres à générer pour chaque lien (1-10).
                  </Typography>
                </Grid>
              </Grid>
            </Paper>
            
            <Typography variant="subtitle1" gutterBottom>
              Fichiers sélectionnés
            </Typography>
            
            <Paper elevation={1} sx={{ p: 2, mb: 3, borderRadius: 2 }}>
              <Typography variant="body1">
                Fichier de contenu: <strong>{contentFile?.filename || 'Non sélectionné'}</strong>
              </Typography>
              
              <Typography variant="body1">
                Fichier de liens: <strong>{linksFile?.filename || 'Non sélectionné'}</strong>
              </Typography>
              
              <Typography variant="body1">
                Fichier GSC: <strong>{gscFile?.filename || 'Non sélectionné'}</strong>
              </Typography>
            </Paper>
            
            {!contentFile && (
              <Alert severity="warning" sx={{ mb: 2 }}>
                Le fichier de contenu est obligatoire pour lancer l'analyse.
              </Alert>
            )}
          </Box>
        );
      case 2:
        return (
          <Box>
            <Typography variant="h6" gutterBottom>
              Progression de l'analyse
            </Typography>
            
            {analyzing ? (
              <CircularProgress />
            ) : (
              <ProgressTracker jobId={jobId} />
            )}
            
            <Typography variant="body2" color="text.secondary" sx={{ mt: 2 }}>
              L'analyse peut prendre plusieurs minutes en fonction de la taille de vos fichiers.
              Vous pouvez fermer cette page et revenir plus tard, l'analyse continuera en arrière-plan.
            </Typography>
          </Box>
        );
      default:
        return 'Étape inconnue';
    }
  };

  return (
    <Box>
      <Typography variant="h4" component="h1" gutterBottom>
        Analyse du maillage interne via proximité sémantique
      </Typography>
      
      <Stepper activeStep={activeStep} sx={{ mb: 4 }}>
        {steps.map((label) => (
          <Step key={label}>
            <StepLabel>{label}</StepLabel>
          </Step>
        ))}
      </Stepper>
      
      {error && (
        <Alert severity="error" sx={{ mb: 3 }}>
          {error}
        </Alert>
      )}
      
      <Paper elevation={3} sx={{ p: 3, mb: 3, borderRadius: 2 }}>
        {getStepContent(activeStep)}
        
        <Divider sx={{ my: 3 }} />
        
        <Box sx={{ display: 'flex', justifyContent: 'space-between' }}>
          <Button
            variant="outlined"
            disabled={activeStep === 0}
            onClick={handleBack}
          >
            Retour
          </Button>
          
          <Box>
            {activeStep === steps.length - 1 ? (
              <Button 
                variant="contained" 
                color="primary" 
                onClick={handleReset}
              >
                Nouvelle analyse
              </Button>
            ) : (
              <Button
                variant="contained"
                color="primary"
                onClick={activeStep === 1 ? startAnalysis : handleNext}
                disabled={activeStep === 0 && !contentFile}
              >
                {activeStep === 1 ? 'Lancer l\'analyse' : 'Suivant'}
              </Button>
            )}
          </Box>
        </Box>
      </Paper>
    </Box>
  );
};

export default AnalysisPage;
