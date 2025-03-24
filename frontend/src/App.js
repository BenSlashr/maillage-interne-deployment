import React from 'react';
import { Routes, Route } from 'react-router-dom';
import { Box, Container, CssBaseline } from '@mui/material';
import Header from './components/Header';
import Footer from './components/Footer';
import HomePage from './pages/HomePage';
import AnalysisPage from './pages/AnalysisPage';
import RulesPage from './pages/RulesPage';
import ResultsPage from './pages/ResultsPage';

function App() {
  return (
    <Box sx={{ 
      display: 'flex', 
      flexDirection: 'column', 
      minHeight: '100vh' 
    }}>
      <CssBaseline />
      <Header />
      <Container component="main" sx={{ mt: 4, mb: 4, flexGrow: 1 }}>
        <Routes>
          <Route path="/" element={<HomePage />} />
          <Route path="/analysis" element={<AnalysisPage />} />
          <Route path="/rules" element={<RulesPage />} />
          <Route path="/results/:jobId" element={<ResultsPage />} />
        </Routes>
      </Container>
      <Footer />
    </Box>
  );
}

export default App;
