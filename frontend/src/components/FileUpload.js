import React, { useState } from 'react';
import { useDropzone } from 'react-dropzone';
import { Box, Typography, Button, LinearProgress, Paper, Alert } from '@mui/material';
import CloudUploadIcon from '@mui/icons-material/CloudUpload';
import CheckCircleIcon from '@mui/icons-material/CheckCircle';
import ErrorIcon from '@mui/icons-material/Error';
import axios from 'axios';
import config from '../config';

// URL de base de l'API
const API_BASE_URL = config.API_BASE_URL;

const FileUpload = ({ title, description, endpoint, onFileUploaded, acceptedFileTypes = ['.xlsx', '.xls'] }) => {
  const [file, setFile] = useState(null);
  const [uploading, setUploading] = useState(false);
  const [uploadProgress, setUploadProgress] = useState(0);
  const [uploadSuccess, setUploadSuccess] = useState(false);
  const [error, setError] = useState(null);

  const onDrop = async (acceptedFiles) => {
    // Reset states
    setError(null);
    setUploadSuccess(false);
    
    // Get the first file
    const uploadFile = acceptedFiles[0];
    if (!uploadFile) return;
    
    setFile(uploadFile);
    
    // Upload the file
    const formData = new FormData();
    formData.append('file', uploadFile);
    
    setUploading(true);
    setUploadProgress(0);
    
    try {
      // Utiliser l'URL complète de l'API
      const fullEndpoint = `${API_BASE_URL}${endpoint}`;
      console.log(`Téléchargement vers: ${fullEndpoint}`);
      
      const response = await axios.post(fullEndpoint, formData, {
        headers: {
          'Content-Type': 'multipart/form-data',
        },
        onUploadProgress: (progressEvent) => {
          const percentCompleted = Math.round((progressEvent.loaded * 100) / progressEvent.total);
          setUploadProgress(percentCompleted);
        },
      });
      
      setUploadSuccess(true);
      setUploading(false);
      
      // Call the callback with the response data
      if (onFileUploaded) {
        onFileUploaded(response.data);
      }
    } catch (err) {
      setError(err.response?.data?.detail || 'Une erreur est survenue lors du téléchargement');
      setUploading(false);
    }
  };
  
  const { getRootProps, getInputProps, isDragActive } = useDropzone({
    onDrop,
    accept: {
      'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet': acceptedFileTypes,
      'application/vnd.ms-excel': acceptedFileTypes
    },
    multiple: false
  });

  return (
    <Paper
      elevation={3}
      sx={{
        p: 3,
        mb: 3,
        borderRadius: 2,
        backgroundColor: (theme) => isDragActive ? theme.palette.action.hover : 'white'
      }}
    >
      <Typography variant="h6" gutterBottom>
        {title}
      </Typography>
      
      <Typography variant="body2" color="text.secondary" paragraph>
        {description}
      </Typography>
      
      {error && (
        <Alert 
          severity="error" 
          sx={{ mb: 2 }}
          icon={<ErrorIcon fontSize="inherit" />}
        >
          {error}
        </Alert>
      )}
      
      {uploadSuccess ? (
        <Box sx={{ display: 'flex', alignItems: 'center', mb: 2 }}>
          <CheckCircleIcon color="success" sx={{ mr: 1 }} />
          <Typography variant="body2" color="success.main">
            Fichier téléchargé avec succès: {file?.name}
          </Typography>
        </Box>
      ) : (
        <Box
          {...getRootProps()}
          sx={{
            border: '2px dashed',
            borderColor: 'primary.main',
            borderRadius: 1,
            p: 3,
            textAlign: 'center',
            cursor: 'pointer',
            mb: 2,
            '&:hover': {
              backgroundColor: 'action.hover'
            }
          }}
        >
          <input {...getInputProps()} />
          <CloudUploadIcon color="primary" sx={{ fontSize: 48, mb: 1 }} />
          <Typography>
            {isDragActive
              ? 'Déposez le fichier ici...'
              : 'Glissez-déposez un fichier ici, ou cliquez pour sélectionner un fichier'}
          </Typography>
          <Typography variant="body2" color="text.secondary" sx={{ mt: 1 }}>
            Formats acceptés: {acceptedFileTypes.join(', ')}
          </Typography>
        </Box>
      )}
      
      {uploading && (
        <Box sx={{ width: '100%', mb: 2 }}>
          <LinearProgress variant="determinate" value={uploadProgress} />
          <Typography variant="body2" color="text.secondary" align="center" sx={{ mt: 1 }}>
            {uploadProgress}%
          </Typography>
        </Box>
      )}
      
      {file && !uploading && !uploadSuccess && (
        <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
          <Typography variant="body2">
            Fichier sélectionné: {file.name}
          </Typography>
          <Button
            variant="contained"
            color="primary"
            onClick={() => onDrop([file])}
          >
            Télécharger
          </Button>
        </Box>
      )}
      
      {uploadSuccess && (
        <Button
          variant="outlined"
          color="primary"
          onClick={() => {
            setFile(null);
            setUploadSuccess(false);
          }}
        >
          Télécharger un autre fichier
        </Button>
      )}
    </Paper>
  );
};

export default FileUpload;
