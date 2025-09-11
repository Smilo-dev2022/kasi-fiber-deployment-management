import React, { useState, useEffect } from 'react';
import {
  Box,
  Typography,
  Card,
  CardContent,
  Grid,
  Button,
  Chip,
  CircularProgress,
  Alert,
} from '@mui/material';
import { Add as AddIcon } from '@mui/icons-material';
import { api } from '../../api/client';

const PONList = () => {
  const [pons, setPons] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');

  useEffect(() => {
    const fetchPONs = async () => {
      try {
        const token = localStorage.getItem('token');
        const config = {
          headers: {
            'x-auth-token': token,
          },
        };

        const res = await api.get('/pons', config);
        setPons(res.data);
        setLoading(false);
      } catch (err) {
        setError('Failed to load PONs');
        setLoading(false);
      }
    };

    fetchPONs();
  }, []);

  const getStatusColor = (status) => {
    switch (status) {
      case 'completed':
        return 'success';
      case 'in_progress':
        return 'warning';
      case 'planned':
        return 'info';
      case 'testing':
        return 'secondary';
      case 'maintenance':
        return 'error';
      default:
        return 'default';
    }
  };

  if (loading) {
    return (
      <Box display="flex" justifyContent="center" alignItems="center" minHeight="400px">
        <CircularProgress />
      </Box>
    );
  }

  return (
    <Box>
      <Box display="flex" justifyContent="space-between" alignItems="center" mb={3}>
        <Typography variant="h4" gutterBottom>
          PON Management
        </Typography>
        <Button
          variant="contained"
          startIcon={<AddIcon />}
          onClick={() => {
            // TODO: Implement PON creation dialog
            alert('PON creation feature - under development');
          }}
        >
          Add PON
        </Button>
      </Box>

      {error && (
        <Alert severity="error" sx={{ mb: 2 }}>
          {error}
        </Alert>
      )}

      {pons.length === 0 ? (
        <Card>
          <CardContent>
            <Typography variant="h6" color="textSecondary" align="center">
              No PONs found. Create your first PON to get started.
            </Typography>
          </CardContent>
        </Card>
      ) : (
        <Grid container spacing={3}>
          {pons.map((pon) => (
            <Grid item xs={12} md={6} lg={4} key={pon._id}>
              <Card>
                <CardContent>
                  <Typography variant="h6" gutterBottom>
                    {pon.name}
                  </Typography>
                  <Typography variant="body2" color="textSecondary" gutterBottom>
                    PON ID: {pon.ponId}
                  </Typography>
                  <Typography variant="body2" gutterBottom>
                    Location: {pon.location}
                  </Typography>
                  <Box display="flex" alignItems="center" justifyContent="space-between" mt={2}>
                    <Chip
                      label={pon.status.replace('_', ' ').toUpperCase()}
                      color={getStatusColor(pon.status)}
                      size="small"
                    />
                    <Typography variant="body2" color="textSecondary">
                      {pon.progress}% Complete
                    </Typography>
                  </Box>
                  <Box mt={2}>
                    <Typography variant="body2" color="textSecondary">
                      Project Manager: {pon.projectManager?.name}
                    </Typography>
                    {pon.siteManager && (
                      <Typography variant="body2" color="textSecondary">
                        Site Manager: {pon.siteManager.name}
                      </Typography>
                    )}
                  </Box>
                </CardContent>
              </Card>
            </Grid>
          ))}
        </Grid>
      )}
    </Box>
  );
};

export default PONList;