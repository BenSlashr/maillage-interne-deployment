import React, { useState, useEffect } from 'react';
import { Box, Typography, LinearProgress, Paper, Chip, Button, List, ListItem, ListItemIcon, ListItemText, Divider } from '@mui/material';
import { useNavigate } from 'react-router-dom';
import axios from 'axios';
import useWebSocket from 'react-use-websocket';
import config from '../config';
import CheckCircleIcon from '@mui/icons-material/CheckCircle';
import LoopIcon from '@mui/icons-material/Loop';
import DescriptionIcon from '@mui/icons-material/Description';
import LinkIcon from '@mui/icons-material/Link';
import BarChartIcon from '@mui/icons-material/BarChart';
import MemoryIcon from '@mui/icons-material/Memory';
import DownloadIcon from '@mui/icons-material/Download';
import StopIcon from '@mui/icons-material/Stop';

// URL de base de l'API
const API_BASE_URL = config.API_BASE_URL;

const ProgressTracker = ({ jobId }) => {
  const [jobStatus, setJobStatus] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [logHistory, setLogHistory] = useState([]);
  const navigate = useNavigate();

  // URL du WebSocket (remplacer localhost par window.location.hostname en production)
  const socketUrl = `ws://localhost:8002/ws/${jobId}`;
  
  // Utilisation du hook WebSocket
  const { lastJsonMessage, sendMessage, readyState } = useWebSocket(socketUrl, {
    onOpen: () => {
      console.log('WebSocket connecté pour la tâche:', jobId);
      setLoading(false);
    },
    onError: (event) => {
      console.error('Erreur WebSocket:', event);
      setError('Erreur de connexion au serveur WebSocket');
      setLoading(false);
      // Fallback au polling HTTP en cas d'erreur WebSocket
      fetchStatusHTTP();
    },
    shouldReconnect: (closeEvent) => true, // Reconnexion automatique
    reconnectAttempts: 10,
    reconnectInterval: 3000,
    share: true, // Partager la connexion entre les composants
    onClose: () => {
      console.log('WebSocket déconnecté');
    },
    retryOnError: true,
  });

  // Fallback au polling HTTP en cas d'échec WebSocket
  const fetchStatusHTTP = async () => {
    try {
      console.log("Fallback HTTP: Vérification du statut de la tâche:", jobId);
      const response = await axios.get(`${API_BASE_URL}/job/${jobId}`);
      const data = response.data;
      console.log("Statut reçu via HTTP:", data);
      setJobStatus(data);
      setLoading(false);
    } catch (err) {
      console.error("Erreur lors de la récupération du statut via HTTP:", err);
      setError(err.response?.data?.detail || 'Erreur lors de la récupération du statut');
      setLoading(false);
    }
  };

  // Mettre à jour le statut quand un message WebSocket est reçu
  useEffect(() => {
    if (lastJsonMessage) {
      console.log('Message WebSocket reçu:', lastJsonMessage);
      setJobStatus(lastJsonMessage);
      
      // Ajouter le message au historique des logs s'il est nouveau
      if (lastJsonMessage.message && 
          (logHistory.length === 0 || logHistory[logHistory.length - 1] !== lastJsonMessage.message)) {
        setLogHistory(prev => [...prev, lastJsonMessage.message]);
      }
    }
  }, [lastJsonMessage]);

  // Envoyer un ping toutes les 5 secondes pour maintenir la connexion
  useEffect(() => {
    const interval = setInterval(() => {
      if (readyState === 1) { // 1 = OPEN
        sendMessage('ping');
      }
    }, 5000);
    
    return () => clearInterval(interval);
  }, [readyState, sendMessage]);

  // Charger le statut initial via HTTP si WebSocket n'est pas disponible
  useEffect(() => {
    if (!jobId) return;
    
    // Si WebSocket n'est pas supporté ou échoue, utiliser HTTP
    if (readyState === 3) { // 3 = CLOSED
      fetchStatusHTTP();
    }
    
    return () => {
      console.log("Nettoyage du composant ProgressTracker");
    };
  }, [jobId, readyState]);

  const getStatusColor = (status) => {
    switch (status) {
      case 'completed':
        return 'success';
      case 'failed':
        return 'error';
      case 'running':
        return 'primary';
      case 'queued':
        return 'warning';
      default:
        return 'default';
    }
  };

  const getStatusLabel = (status) => {
    switch (status) {
      case 'completed':
        return 'Terminé';
      case 'failed':
        return 'Échoué';
      case 'running':
        return 'En cours';
      case 'queued':
        return 'En attente';
      default:
        return 'Inconnu';
    }
  };

  const getIconForLogMessage = (message) => {
    if (message.includes('Fichier de contenu chargé')) {
      return <DescriptionIcon color="primary" />;
    } else if (message.includes('Fichier de liens existants chargé')) {
      return <LinkIcon color="primary" />;
    } else if (message.includes('Fichier GSC chargé')) {
      return <BarChartIcon color="primary" />;
    } else if (message.includes('embeddings')) {
      return <MemoryIcon color="primary" />;
    } else if (message.includes('Analyse de la page')) {
      return <LoopIcon color="primary" />;
    } else if (message.includes('terminé')) {
      return <CheckCircleIcon color="success" />;
    } else {
      return <LoopIcon color="primary" />;
    }
  };

  const handleViewResults = () => {
    navigate(`/results/${jobId}`);
  };

  const handleDownloadResults = (format) => {
    window.open(`${API_BASE_URL}/results/${jobId}?format=${format}`, '_blank');
  };

  const handleStopAnalysis = async () => {
    try {
      console.log("Tentative de forcer la complétion de l'analyse...");
      const response = await axios.get(`${API_BASE_URL}/force-complete/${jobId}`);
      console.log("Réponse reçue:", response.data);
      
      // Mettre à jour le statut localement
      if (response.data.status === 'completed') {
        setJobStatus(prev => ({
          ...prev,
          status: 'completed',
          progress: 100,
          message: 'Analyse terminée avec succès (forcé)',
          result_file: response.data.result_file
        }));
      }
    } catch (err) {
      console.error("Erreur lors de la complétion forcée de l'analyse:", err);
      alert("Impossible de forcer la complétion de l'analyse. Veuillez réessayer.");
    }
  };

  if (loading) {
    return (
      <Paper elevation={3} sx={{ p: 3, mb: 3, borderRadius: 2 }}>
        <Typography variant="h6" gutterBottom>
          Chargement du statut...
        </Typography>
        <LinearProgress />
      </Paper>
    );
  }

  if (error) {
    return (
      <Paper elevation={3} sx={{ p: 3, mb: 3, borderRadius: 2 }}>
        <Typography variant="h6" color="error" gutterBottom>
          Erreur
        </Typography>
        <Typography variant="body1">{error}</Typography>
      </Paper>
    );
  }

  if (!jobStatus) {
    return (
      <Paper elevation={3} sx={{ p: 3, mb: 3, borderRadius: 2 }}>
        <Typography variant="h6" gutterBottom>
          Aucune tâche en cours
        </Typography>
      </Paper>
    );
  }

  return (
    <Paper elevation={3} sx={{ p: 3, mb: 3, borderRadius: 2, bgcolor: '#222', color: 'white' }}>
      <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 2 }}>
        <Typography variant="h6">
          Progression de l'analyse (VERSION NOIRE)
        </Typography>
        <Chip 
          label={getStatusLabel(jobStatus.status)} 
          color={getStatusColor(jobStatus.status)} 
          variant="outlined" 
          sx={{ borderColor: 'white', color: 'white' }}
        />
      </Box>

      <Typography variant="body1" gutterBottom>
        {jobStatus.message}
      </Typography>

      <Box sx={{ mt: 2, mb: 2 }}>
        <LinearProgress 
          variant="determinate" 
          value={jobStatus.progress} 
          color={getStatusColor(jobStatus.status)}
        />
        <Typography variant="body2" align="center" sx={{ mt: 1 }}>
          {jobStatus.progress}%
        </Typography>
      </Box>
      
      {/* Historique des logs */}
      {logHistory.length > 0 && (
        <Box sx={{ mt: 3 }}>
          <Divider sx={{ mb: 2 }} />
          <Typography variant="subtitle1" gutterBottom>
            Détails de l'analyse
          </Typography>
          <List dense sx={{ maxHeight: '200px', overflow: 'auto', bgcolor: '#f5f5f5', borderRadius: 1 }}>
            {logHistory.map((log, index) => (
              <ListItem key={index}>
                <ListItemIcon>
                  {getIconForLogMessage(log)}
                </ListItemIcon>
                <ListItemText 
                  primary={log}
                  primaryTypographyProps={{ 
                    variant: 'body2',
                    style: { fontFamily: 'monospace' }
                  }}
                />
              </ListItem>
            ))}
          </List>
        </Box>
      )}

      {(jobStatus.status === 'completed' || (jobStatus.result_file && jobStatus.progress === 100)) && (
        <Box sx={{ display: 'flex', justifyContent: 'center', mt: 2, gap: 2, flexWrap: 'wrap' }}>
          <Button 
            variant="contained" 
            color="primary" 
            onClick={handleViewResults}
            startIcon={<DescriptionIcon />}
          >
            Voir les résultats
          </Button>
          <Button 
            variant="outlined" 
            color="primary" 
            onClick={() => handleDownloadResults('xlsx')}
            startIcon={<DownloadIcon />}
          >
            Télécharger XLSX
          </Button>
          <Button 
            variant="outlined" 
            color="secondary" 
            onClick={() => handleDownloadResults('csv')}
            startIcon={<DownloadIcon />}
          >
            Télécharger CSV
          </Button>
        </Box>
      )}

      {jobStatus.status === 'running' && (
        <Box sx={{ display: 'flex', justifyContent: 'center', mt: 2, gap: 2, flexWrap: 'wrap' }}>
          <Button 
            variant="contained" 
            color="error" 
            onClick={handleStopAnalysis}
            startIcon={<StopIcon />}
          >
            Forcer la fin de l'analyse
          </Button>
        </Box>
      )}

      {jobStatus.status === 'failed' && (
        <Typography variant="body2" color="error">
          L'analyse a échoué. Veuillez réessayer ou contacter le support.
        </Typography>
      )}
    </Paper>
  );
};

export default ProgressTracker;
