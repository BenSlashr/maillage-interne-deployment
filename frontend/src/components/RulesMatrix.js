import React, { useState, useEffect } from 'react';
import {
  Box,
  Typography,
  Paper,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  TextField,
  Button,
  Alert,
  CircularProgress
} from '@mui/material';
import axios from 'axios';
import config from '../config';

// URL de base de l'API
const API_BASE_URL = config.API_BASE_URL;

const RulesMatrix = ({ contentFilePath }) => {
  const [segments, setSegments] = useState([]);
  const [rules, setRules] = useState({});
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState(null);
  const [success, setSuccess] = useState(false);

  // Charger les segments depuis le fichier de contenu
  useEffect(() => {
    const fetchSegments = async () => {
      if (!contentFilePath) return;

      try {
        setLoading(true);
        const response = await axios.get(`${API_BASE_URL}/segments?content_file=${contentFilePath}`);
        setSegments(response.data.segments);
        
        // Charger les règles existantes
        const rulesResponse = await axios.get(`${API_BASE_URL}/rules`);
        setRules(rulesResponse.data.rules || {});
        
        setLoading(false);
      } catch (err) {
        setError(err.response?.data?.detail || 'Erreur lors du chargement des segments');
        setLoading(false);
      }
    };

    fetchSegments();
  }, [contentFilePath]);

  // Mettre à jour une règle
  const handleRuleChange = (sourceType, targetType, field, value) => {
    // Convertir la valeur en nombre
    const numValue = parseInt(value, 10);
    
    // Vérifier que la valeur est un nombre valide
    if (isNaN(numValue) || numValue < 0) return;
    
    // Créer une copie des règles
    const newRules = { ...rules };
    
    // Créer le type source s'il n'existe pas
    if (!newRules[sourceType]) {
      newRules[sourceType] = {};
    }
    
    // Créer le type cible s'il n'existe pas
    if (!newRules[sourceType][targetType]) {
      newRules[sourceType][targetType] = { min_links: 0, max_links: 0 };
    }
    
    // Mettre à jour la valeur
    newRules[sourceType][targetType][field] = numValue;
    
    // Si min > max, ajuster max
    if (field === 'min_links' && numValue > newRules[sourceType][targetType].max_links) {
      newRules[sourceType][targetType].max_links = numValue;
    }
    
    // Si max < min, ajuster min
    if (field === 'max_links' && numValue < newRules[sourceType][targetType].min_links) {
      newRules[sourceType][targetType].min_links = numValue;
    }
    
    // Mettre à jour les règles
    setRules(newRules);
  };

  // Sauvegarder les règles
  const handleSaveRules = async () => {
    try {
      setSaving(true);
      setError(null);
      setSuccess(false);
      
      await axios.post(`${API_BASE_URL}/rules`, { rules });
      
      setSuccess(true);
      setSaving(false);
    } catch (err) {
      setError(err.response?.data?.detail || 'Erreur lors de la sauvegarde des règles');
      setSaving(false);
    }
  };

  // Charger les règles par défaut
  const handleLoadDefaultRules = async () => {
    try {
      setLoading(true);
      
      // Obtenir les règles par défaut
      const response = await axios.get(`${API_BASE_URL}/rules`);
      
      // Mettre à jour les règles
      setRules(response.data.rules);
      
      setLoading(false);
    } catch (err) {
      setError(err.response?.data?.detail || 'Erreur lors du chargement des règles par défaut');
      setLoading(false);
    }
  };

  if (loading) {
    return (
      <Box sx={{ display: 'flex', justifyContent: 'center', p: 3 }}>
        <CircularProgress />
      </Box>
    );
  }

  if (!contentFilePath) {
    return (
      <Alert severity="info">
        Veuillez d'abord télécharger un fichier de contenu pour configurer les règles de maillage.
      </Alert>
    );
  }

  if (segments.length === 0) {
    return (
      <Alert severity="warning">
        Aucun segment trouvé dans le fichier de contenu. Vérifiez que votre fichier contient une colonne "Segments".
      </Alert>
    );
  }

  return (
    <Paper elevation={3} sx={{ p: 3, mb: 3, borderRadius: 2 }}>
      <Typography variant="h6" gutterBottom>
        Configuration des règles de maillage
      </Typography>
      
      <Typography variant="body2" color="text.secondary" paragraph>
        Configurez les règles de maillage interne entre les différents types de pages.
        Pour chaque combinaison de types :
        <br />
        - Min : nombre minimum de liens à créer
        <br />
        - Max : nombre maximum de liens autorisés
      </Typography>
      
      {error && (
        <Alert severity="error" sx={{ mb: 2 }}>
          {error}
        </Alert>
      )}
      
      {success && (
        <Alert severity="success" sx={{ mb: 2 }}>
          Règles de maillage sauvegardées avec succès.
        </Alert>
      )}
      
      <TableContainer component={Paper} variant="outlined" sx={{ mb: 3 }}>
        <Table size="small">
          <TableHead>
            <TableRow>
              <TableCell sx={{ fontWeight: 'bold' }}>De / Vers</TableCell>
              {segments.map((segment) => (
                <TableCell key={segment} align="center" sx={{ fontWeight: 'bold' }}>
                  {segment}
                </TableCell>
              ))}
            </TableRow>
          </TableHead>
          <TableBody>
            {segments.map((sourceType) => (
              <TableRow key={sourceType}>
                <TableCell component="th" scope="row" sx={{ fontWeight: 'bold' }}>
                  {sourceType}
                </TableCell>
                {segments.map((targetType) => {
                  // Récupérer les valeurs actuelles
                  const minLinks = rules[sourceType]?.[targetType]?.min_links || 0;
                  const maxLinks = rules[sourceType]?.[targetType]?.max_links || 0;
                  
                  return (
                    <TableCell key={`${sourceType}-${targetType}`} align="center">
                      <Box sx={{ display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
                        <TextField
                          type="number"
                          size="small"
                          variant="outlined"
                          InputProps={{ inputProps: { min: 0, max: 10 } }}
                          value={minLinks}
                          onChange={(e) => handleRuleChange(sourceType, targetType, 'min_links', e.target.value)}
                          sx={{ width: 60, mr: 1 }}
                        />
                        <Typography variant="body2" sx={{ mx: 1 }}>-</Typography>
                        <TextField
                          type="number"
                          size="small"
                          variant="outlined"
                          InputProps={{ inputProps: { min: 0, max: 10 } }}
                          value={maxLinks}
                          onChange={(e) => handleRuleChange(sourceType, targetType, 'max_links', e.target.value)}
                          sx={{ width: 60, ml: 1 }}
                        />
                      </Box>
                    </TableCell>
                  );
                })}
              </TableRow>
            ))}
          </TableBody>
        </Table>
      </TableContainer>
      
      <Box sx={{ display: 'flex', justifyContent: 'space-between' }}>
        <Button
          variant="outlined"
          onClick={handleLoadDefaultRules}
          disabled={loading || saving}
        >
          Règles par défaut
        </Button>
        
        <Button
          variant="contained"
          color="primary"
          onClick={handleSaveRules}
          disabled={loading || saving}
        >
          {saving ? <CircularProgress size={24} /> : 'Sauvegarder les règles'}
        </Button>
      </Box>
    </Paper>
  );
};

export default RulesMatrix;
