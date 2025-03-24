import React from 'react';
import { Box, Typography, Link, Container } from '@mui/material';

const Footer = () => {
  return (
    <Box
      component="footer"
      sx={{
        py: 3,
        px: 2,
        mt: 'auto',
        backgroundColor: (theme) => theme.palette.grey[100]
      }}
    >
      <Container maxWidth="lg">
        <Typography variant="body2" color="text.secondary" align="center">
          {'© '}
          {new Date().getFullYear()}
          {' '}
          <Link color="inherit" href="https://github.com/BenSlashr/maillage-interne" target="_blank">
            SEO Internal Linking
          </Link>
          {' - Outil d\'analyse et d\'optimisation du maillage interne pour améliorer le SEO'}
        </Typography>
      </Container>
    </Box>
  );
};

export default Footer;
