import React, { useState, useEffect } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { 
  Box, 
  Typography, 
  Paper, 
  Button, 
  CircularProgress, 
  Alert, 
  Table, 
  TableBody, 
  TableCell, 
  TableContainer, 
  TableHead, 
  TableRow,
  Chip,
  Tabs,
  Tab,
  TextField,
  InputAdornment,
  IconButton,
  Tooltip,
  Divider
} from '@mui/material';
import DownloadIcon from '@mui/icons-material/Download';
import SearchIcon from '@mui/icons-material/Search';
import FilterListIcon from '@mui/icons-material/FilterList';
import ClearIcon from '@mui/icons-material/Clear';
import LinkIcon from '@mui/icons-material/Link';
import axios from 'axios';
import config from '../config';

// URL de base de l'API
const API_BASE_URL = config.API_BASE_URL;

// Composant TabPanel pour les onglets
function TabPanel(props) {
  const { children, value, index, ...other } = props;

  return (
    <div
      role="tabpanel"
      hidden={value !== index}
      id={`results-tabpanel-${index}`}
      aria-labelledby={`results-tab-${index}`}
      {...other}
    >
      {value === index && (
        <Box sx={{ p: 3 }}>
          {children}
        </Box>
      )}
    </div>
  );
}

const ResultsPage = () => {
  const { jobId } = useParams();
  const navigate = useNavigate();
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [results, setResults] = useState(null);
  const [tabValue, setTabValue] = useState(0);
  const [searchTerm, setSearchTerm] = useState('');
  const [filteredResults, setFilteredResults] = useState(null);

  // Récupérer les résultats
  useEffect(() => {
    const fetchResults = async () => {
      if (!jobId) {
        setError('ID de tâche non spécifié');
        setLoading(false);
        return;
      }

      try {
        setLoading(true);
        const response = await axios.get(`${API_BASE_URL}/results/${jobId}`);
        setResults(response.data);
        setFilteredResults(response.data);
        setLoading(false);
      } catch (err) {
        setError(err.response?.data?.detail || 'Erreur lors de la récupération des résultats');
        setLoading(false);
      }
    };

    fetchResults();
  }, [jobId]);

  // Filtrer les résultats en fonction du terme de recherche
  useEffect(() => {
    if (!results) return;

    if (!searchTerm.trim()) {
      setFilteredResults(results);
      return;
    }

    const term = searchTerm.toLowerCase();
    
    // Filtrer les suggestions
    const filteredSuggestions = results.suggestions.filter(suggestion => 
      suggestion.source_url.toLowerCase().includes(term) ||
      suggestion.target_url.toLowerCase().includes(term) ||
      suggestion.source_title.toLowerCase().includes(term) ||
      suggestion.target_title.toLowerCase().includes(term) ||
      suggestion.source_segment.toLowerCase().includes(term) ||
      suggestion.target_segment.toLowerCase().includes(term) ||
      suggestion.anchor_suggestions.some(anchor => anchor.toLowerCase().includes(term))
    );

    // Filtrer les statistiques
    const filteredStats = {
      ...results.stats,
      segment_stats: Object.fromEntries(
        Object.entries(results.stats.segment_stats).filter(([segment]) => 
          segment.toLowerCase().includes(term)
        )
      )
    };

    setFilteredResults({
      ...results,
      suggestions: filteredSuggestions,
      stats: filteredStats
    });
  }, [searchTerm, results]);

  const handleTabChange = (event, newValue) => {
    setTabValue(newValue);
  };

  const handleDownloadResults = async () => {
    try {
      const response = await axios.get(`${API_BASE_URL}/download/${jobId}`, {
        responseType: 'blob'
      });
      
      // Créer un lien de téléchargement
      const url = window.URL.createObjectURL(new Blob([response.data]));
      const link = document.createElement('a');
      link.href = url;
      link.setAttribute('download', `suggestions_${jobId}.xlsx`);
      document.body.appendChild(link);
      link.click();
      
      // Nettoyer
      link.parentNode.removeChild(link);
      window.URL.revokeObjectURL(url);
    } catch (err) {
      setError('Erreur lors du téléchargement des résultats');
    }
  };

  const handleClearSearch = () => {
    setSearchTerm('');
  };

  if (loading) {
    return (
      <Box sx={{ display: 'flex', justifyContent: 'center', alignItems: 'center', height: '50vh' }}>
        <CircularProgress />
      </Box>
    );
  }

  if (error) {
    return (
      <Box>
        <Typography variant="h4" component="h1" gutterBottom>
          Résultats de l'analyse
        </Typography>
        
        <Alert severity="error" sx={{ mb: 3 }}>
          {error}
        </Alert>
        
        <Button
          variant="contained"
          color="primary"
          onClick={() => navigate('/analysis')}
        >
          Retour à l'analyse
        </Button>
      </Box>
    );
  }

  if (!results) {
    return (
      <Box>
        <Typography variant="h4" component="h1" gutterBottom>
          Résultats de l'analyse
        </Typography>
        
        <Alert severity="warning" sx={{ mb: 3 }}>
          Aucun résultat trouvé pour cette analyse.
        </Alert>
        
        <Button
          variant="contained"
          color="primary"
          onClick={() => navigate('/analysis')}
        >
          Retour à l'analyse
        </Button>
      </Box>
    );
  }

  return (
    <Box>
      <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 3 }}>
        <Typography variant="h4" component="h1">
          Résultats de l'analyse
        </Typography>
        
        <Button
          variant="contained"
          color="primary"
          startIcon={<DownloadIcon />}
          onClick={handleDownloadResults}
        >
          Télécharger les résultats
        </Button>
      </Box>
      
      <Paper elevation={3} sx={{ mb: 4, borderRadius: 2 }}>
        <Box sx={{ p: 3 }}>
          <Typography variant="h6" gutterBottom>
            Résumé de l'analyse
          </Typography>
          
          <Box sx={{ display: 'flex', flexWrap: 'wrap', gap: 2, mb: 2 }}>
            <Chip 
              icon={<LinkIcon />} 
              label={`${filteredResults.stats.total_suggestions} suggestions`} 
              color="primary" 
              variant="outlined" 
            />
            <Chip 
              label={`${filteredResults.stats.total_pages} pages analysées`} 
              color="default" 
              variant="outlined" 
            />
            <Chip 
              label={`${filteredResults.stats.total_existing_links} liens existants`} 
              color="default" 
              variant="outlined" 
            />
            <Chip 
              label={`Score moyen: ${filteredResults.stats.average_similarity.toFixed(2)}`} 
              color="default" 
              variant="outlined" 
            />
          </Box>
          
          <Typography variant="body2" color="text.secondary">
            Analyse effectuée le {new Date(filteredResults.timestamp).toLocaleString()}
          </Typography>
        </Box>
        
        <Divider />
        
        <Box sx={{ p: 3 }}>
          <TextField
            fullWidth
            variant="outlined"
            placeholder="Rechercher dans les résultats..."
            value={searchTerm}
            onChange={(e) => setSearchTerm(e.target.value)}
            InputProps={{
              startAdornment: (
                <InputAdornment position="start">
                  <SearchIcon />
                </InputAdornment>
              ),
              endAdornment: searchTerm && (
                <InputAdornment position="end">
                  <IconButton onClick={handleClearSearch} edge="end">
                    <ClearIcon />
                  </IconButton>
                </InputAdornment>
              )
            }}
            sx={{ mb: 2 }}
          />
        </Box>
        
        <Box sx={{ borderBottom: 1, borderColor: 'divider' }}>
          <Tabs value={tabValue} onChange={handleTabChange} aria-label="résultats tabs">
            <Tab label="Suggestions de liens" id="results-tab-0" />
            <Tab label="Statistiques par segment" id="results-tab-1" />
          </Tabs>
        </Box>
        
        <TabPanel value={tabValue} index={0}>
          {filteredResults.suggestions.length === 0 ? (
            <Alert severity="info">
              Aucune suggestion de lien trouvée.
              {searchTerm && " Essayez de modifier vos critères de recherche."}
            </Alert>
          ) : (
            <TableContainer>
              <Table size="small">
                <TableHead>
                  <TableRow>
                    <TableCell sx={{ fontWeight: 'bold' }}>Page source</TableCell>
                    <TableCell sx={{ fontWeight: 'bold' }}>Segment</TableCell>
                    <TableCell sx={{ fontWeight: 'bold' }}>Page cible</TableCell>
                    <TableCell sx={{ fontWeight: 'bold' }}>Segment</TableCell>
                    <TableCell sx={{ fontWeight: 'bold' }}>Score</TableCell>
                    <TableCell sx={{ fontWeight: 'bold' }}>Suggestions d'ancres</TableCell>
                  </TableRow>
                </TableHead>
                <TableBody>
                  {filteredResults.suggestions.map((suggestion, index) => (
                    <TableRow key={index} hover>
                      <TableCell>
                        <Tooltip title={suggestion.source_url}>
                          <Typography variant="body2" noWrap sx={{ maxWidth: 200 }}>
                            {suggestion.source_title || suggestion.source_url}
                          </Typography>
                        </Tooltip>
                      </TableCell>
                      <TableCell>
                        <Chip 
                          label={suggestion.source_segment} 
                          size="small" 
                          variant="outlined"
                        />
                      </TableCell>
                      <TableCell>
                        <Tooltip title={suggestion.target_url}>
                          <Typography variant="body2" noWrap sx={{ maxWidth: 200 }}>
                            {suggestion.target_title || suggestion.target_url}
                          </Typography>
                        </Tooltip>
                      </TableCell>
                      <TableCell>
                        <Chip 
                          label={suggestion.target_segment} 
                          size="small" 
                          variant="outlined"
                        />
                      </TableCell>
                      <TableCell>
                        {suggestion.similarity_score.toFixed(2)}
                      </TableCell>
                      <TableCell>
                        <Box sx={{ display: 'flex', flexWrap: 'wrap', gap: 0.5 }}>
                          {suggestion.anchor_suggestions.map((anchor, i) => (
                            <Chip 
                              key={i} 
                              label={anchor} 
                              size="small" 
                              color="primary"
                              variant="outlined"
                              sx={{ maxWidth: 150 }}
                            />
                          ))}
                        </Box>
                      </TableCell>
                    </TableRow>
                  ))}
                </TableBody>
              </Table>
            </TableContainer>
          )}
        </TabPanel>
        
        <TabPanel value={tabValue} index={1}>
          {Object.keys(filteredResults.stats.segment_stats).length === 0 ? (
            <Alert severity="info">
              Aucune statistique par segment disponible.
              {searchTerm && " Essayez de modifier vos critères de recherche."}
            </Alert>
          ) : (
            <TableContainer>
              <Table size="small">
                <TableHead>
                  <TableRow>
                    <TableCell sx={{ fontWeight: 'bold' }}>Segment</TableCell>
                    <TableCell sx={{ fontWeight: 'bold' }}>Nombre de pages</TableCell>
                    <TableCell sx={{ fontWeight: 'bold' }}>Liens entrants</TableCell>
                    <TableCell sx={{ fontWeight: 'bold' }}>Liens sortants</TableCell>
                    <TableCell sx={{ fontWeight: 'bold' }}>Suggestions</TableCell>
                  </TableRow>
                </TableHead>
                <TableBody>
                  {Object.entries(filteredResults.stats.segment_stats).map(([segment, stats]) => (
                    <TableRow key={segment} hover>
                      <TableCell>
                        <Chip 
                          label={segment} 
                          color="primary" 
                          variant="outlined"
                        />
                      </TableCell>
                      <TableCell>{stats.page_count}</TableCell>
                      <TableCell>{stats.incoming_links}</TableCell>
                      <TableCell>{stats.outgoing_links}</TableCell>
                      <TableCell>{stats.suggestions}</TableCell>
                    </TableRow>
                  ))}
                </TableBody>
              </Table>
            </TableContainer>
          )}
        </TabPanel>
      </Paper>
      
      <Box sx={{ display: 'flex', justifyContent: 'space-between' }}>
        <Button
          variant="outlined"
          onClick={() => navigate('/analysis')}
        >
          Nouvelle analyse
        </Button>
        
        <Button
          variant="outlined"
          color="primary"
          onClick={() => navigate('/rules')}
        >
          Modifier les règles
        </Button>
      </Box>
    </Box>
  );
};

export default ResultsPage;
