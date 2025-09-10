import React, { useEffect, useState } from 'react';
import { useParams } from 'react-router-dom';
import { Typography, Card, CardContent, Grid, Box, Chip, CircularProgress, Alert } from '@mui/material';
import axios from 'axios';

const PONDetail = () => {
  const { id } = useParams();
  const [pon, setPon] = useState(null);
  const [incidents, setIncidents] = useState([]);
  const [optics, setOptics] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');

  useEffect(() => {
    const token = localStorage.getItem('token');
    const config = { headers: { 'x-auth-token': token } };
    async function load() {
      try {
        const [ponRes, incRes, optRes] = await Promise.all([
          axios.get(`/api/pons/${id}`, config),
          axios.get(`/api/incidents?pon=${id}&status=open`, config),
          axios.get(`/api/optics?pon=${id}&days=7`, config),
        ]);
        setPon(ponRes.data.pon || ponRes.data);
        setIncidents(incRes.data);
        setOptics(optRes.data);
        setLoading(false);
      } catch (e) {
        setError('Failed to load PON details');
        setLoading(false);
      }
    }
    load();
  }, [id]);

  if (loading) {
    return (
      <Box display="flex" justifyContent="center" alignItems="center" minHeight="400px">
        <CircularProgress />
      </Box>
    );
  }

  return (
    <Box>
      <Typography variant="h4" gutterBottom>
        PON Details
      </Typography>
      {error && <Alert severity="error">{error}</Alert>}

      {pon && (
        <Card sx={{ mb: 3 }}>
          <CardContent>
            <Typography variant="h6">{pon.name} ({pon.ponId})</Typography>
            <Typography variant="body2" color="textSecondary">{pon.location}</Typography>
            <Box display="flex" alignItems="center" gap={2} mt={1}>
              <Chip label={`Status: ${pon.status}`} size="small" />
              <Chip label={`Progress: ${pon.progress || 0}%`} size="small" />
            </Box>
          </CardContent>
        </Card>
      )}

      <Grid container spacing={3}>
        <Grid item xs={12} md={6}>
          <Card>
            <CardContent>
              <Typography variant="h6" gutterBottom>Open Incidents</Typography>
              {incidents.length === 0 ? (
                <Typography variant="body2" color="textSecondary">No open incidents</Typography>
              ) : (
                incidents.map((i) => (
                  <Box key={i._id} display="flex" justifyContent="space-between" py={1} borderBottom="1px solid #eee">
                    <Box>
                      <Typography variant="subtitle2">{i.title}</Typography>
                      <Typography variant="caption" color="textSecondary">{i.category} • {i.priority}</Typography>
                    </Box>
                    <Chip label={i.status} size="small" color={i.priority === 'P1' ? 'error' : i.priority === 'P2' ? 'warning' : 'default'} />
                  </Box>
                ))
              )}
            </CardContent>
          </Card>
        </Grid>

        <Grid item xs={12} md={6}>
          <Card>
            <CardContent>
              <Typography variant="h6" gutterBottom>Optical Power (7d)</Typography>
              {optics.length === 0 ? (
                <Typography variant="body2" color="textSecondary">No readings</Typography>
              ) : (
                <Box sx={{ maxHeight: 260, overflowY: 'auto' }}>
                  {optics.slice(0, 50).map((r) => (
                    <Box key={r._id} display="flex" justifyContent="space-between" py={0.5} borderBottom="1px dashed #f0f0f0">
                      <Typography variant="caption">{new Date(r.takenAt).toLocaleString()}</Typography>
                      <Typography variant="caption">{r.direction} {r.onuId || r.port}</Typography>
                      <Typography variant="caption">{r.powerDbm} dBm</Typography>
                    </Box>
                  ))}
                </Box>
              )}
            </CardContent>
          </Card>
        </Grid>
      </Grid>
    </Box>
  );
};

export default PONDetail;