import React, { useState, useEffect } from 'react';
import { Box, Typography, Paper, Alert, Button, CircularProgress } from '@mui/material';
import RulesMatrix from '../components/RulesMatrix';
import FileUpload from '../components/FileUpload';
import axios from 'axios';
import config from '../config';

// URL de base de l'API
const API_BASE_URL = config.API_BASE_URL;

const RulesPage = () => {
  const [contentFile, setContentFile] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [segments, setSegments] = useState([]);

  useEffect(() => {
    const fetchContentFile = async () => {
      try {
        setLoading(true);
        setError(null);
        
        const response = await axios.get(`${API_BASE_URL}/files/content`);
        setContentFile(response.data);
        
        // Si nous avons un fichier de contenu, récupérer les segments
        if (response.data && response.data.path) {
          const segmentsResponse = await axios.get(`${API_BASE_URL}/segments?content_file=${response.data.path}`);
          setSegments(segmentsResponse.data.segments);
        }
        
        setLoading(false);
      } catch (error) {
        console.error('Erreur lors de la récupération du fichier de contenu:', error);
        setError('Erreur lors de la récupération du fichier de contenu');
        setLoading(false);
      }
    };
    
    fetchContentFile();
  }, []);

  const handleContentFileUploaded = async (data) => {
    setContentFile(data);
    
    try {
      const response = await axios.get(`${API_BASE_URL}/segments?content_file=${data.path}`);
      setSegments(response.data.segments);
    } catch (error) {
      console.error('Erreur lors de la récupération des segments:', error);
      setError('Erreur lors de la récupération des segments');
    }
  };

  return (
    <Box>
      <Typography variant="h4" component="h1" gutterBottom>
        Gestion des règles de maillage
      </Typography>
      
      <Typography variant="body1" paragraph>
        Configurez les règles de maillage interne entre les différents types de pages de votre site.
        Ces règles déterminent le nombre minimum et maximum de liens à créer entre chaque type de page.
      </Typography>
      
      {error && (
        <Alert severity="error" sx={{ mb: 3 }}>
          {error}
        </Alert>
      )}
      
      {loading ? (
        <Box sx={{ display: 'flex', justifyContent: 'center', p: 3 }}>
          <CircularProgress />
        </Box>
      ) : (
        <>
          {!contentFile && (
            <Paper elevation={3} sx={{ p: 3, mb: 3, borderRadius: 2 }}>
              <Typography variant="h6" gutterBottom>
                Téléchargez d'abord votre fichier de contenu
              </Typography>
              
              <Typography variant="body2" color="text.secondary" paragraph>
                Pour configurer les règles de maillage, nous avons besoin de connaître les différents types de pages (segments) présents dans votre site.
              </Typography>
              
              <FileUpload
                title="Fichier de contenu"
                description="Ce fichier doit contenir une colonne 'Segments' qui liste les différents types de pages."
                endpoint="/upload/content"
                onFileUploaded={handleContentFileUploaded}
              />
            </Paper>
          )}
          
          {contentFile && segments.length === 0 && (
            <Alert severity="warning" sx={{ mb: 3 }}>
              Aucun segment trouvé dans le fichier de contenu. Vérifiez que votre fichier contient une colonne "Segments".
            </Alert>
          )}
          
          {contentFile && segments.length > 0 && (
            <>
              <Paper elevation={3} sx={{ p: 3, mb: 3, borderRadius: 2 }}>
                <Typography variant="h6" gutterBottom>
                  Fichier de contenu chargé
                </Typography>
                
                <Typography variant="body1">
                  Nom du fichier: <strong>{contentFile.filename}</strong>
                </Typography>
                
                <Typography variant="body1">
                  Segments détectés: <strong>{segments.join(', ')}</strong>
                </Typography>
                
                <Button
                  variant="outlined"
                  color="primary"
                  sx={{ mt: 2 }}
                  onClick={() => setContentFile(null)}
                >
                  Changer de fichier
                </Button>
              </Paper>
              
              <RulesMatrix contentFilePath={contentFile.path} />
            </>
          )}
        </>
      )}
    </Box>
  );
};

export default RulesPage;
