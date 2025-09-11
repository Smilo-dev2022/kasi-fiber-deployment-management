import React, { useState, useEffect } from 'react';
import {
  Box,
  Typography,
  Card,
  CardContent,
  Button,
  Grid,
  CircularProgress,
  Alert,
} from '@mui/material';
import { Download as DownloadIcon } from '@mui/icons-material';
import { api } from '../../api/client';

const Reports = () => {
  const [ponData, setPonData] = useState([]);
  const [taskData, setTaskData] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');

  useEffect(() => {
    const fetchReportData = async () => {
      try {
        const token = localStorage.getItem('token');
        const config = {
          headers: {
            'x-auth-token': token,
          },
        };

        const [ponRes, taskRes] = await Promise.all([
          api.get('/reports/pons', config),
          api.get('/reports/tasks', config),
        ]);

        setPonData(ponRes.data);
        setTaskData(taskRes.data);
        setLoading(false);
      } catch (err) {
        setError('Failed to load report data');
        setLoading(false);
      }
    };

    fetchReportData();
  }, []);

  const handleExport = async (type) => {
    try {
      const token = localStorage.getItem('token');
      const config = {
        headers: {
          'x-auth-token': token,
        },
        responseType: 'blob',
      };

      const res = await api.get(`/reports/export/${type}`, config);
      
      // Create download link
      const url = window.URL.createObjectURL(new Blob([res.data]));
      const link = document.createElement('a');
      link.href = url;
      link.setAttribute('download', `${type}_report.csv`);
      document.body.appendChild(link);
      link.click();
      link.remove();
    } catch (err) {
      alert('Failed to export report');
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
      <Typography variant="h4" gutterBottom>
        Reports & Analytics
      </Typography>

      {error && (
        <Alert severity="error" sx={{ mb: 2 }}>
          {error}
        </Alert>
      )}

      <Grid container spacing={3}>
        <Grid item xs={12} md={6}>
          <Card>
            <CardContent>
              <Typography variant="h6" gutterBottom>
                PON Reports
              </Typography>
              <Typography variant="body2" color="textSecondary" paragraph>
                Export PON data including status, progress, and management assignments.
              </Typography>
              <Typography variant="body2" gutterBottom>
                Total PONs: {ponData.length}
              </Typography>
              <Button
                variant="contained"
                startIcon={<DownloadIcon />}
                onClick={() => handleExport('pons')}
                fullWidth
              >
                Export PON Report (CSV)
              </Button>
            </CardContent>
          </Card>
        </Grid>

        <Grid item xs={12} md={6}>
          <Card>
            <CardContent>
              <Typography variant="h6" gutterBottom>
                Task Reports
              </Typography>
              <Typography variant="body2" color="textSecondary" paragraph>
                Export task data including status, priority, and evidence tracking.
              </Typography>
              <Typography variant="body2" gutterBottom>
                Total Tasks: {taskData.length}
              </Typography>
              <Button
                variant="contained"
                startIcon={<DownloadIcon />}
                onClick={() => alert('Task export feature - under development')}
                fullWidth
                disabled
              >
                Export Task Report (CSV)
              </Button>
            </CardContent>
          </Card>
        </Grid>

        <Grid item xs={12}>
          <Card>
            <CardContent>
              <Typography variant="h6" gutterBottom>
                Key Metrics Summary
              </Typography>
              <Grid container spacing={2}>
                <Grid item xs={6} md={3}>
                  <Typography variant="h4" color="primary">
                    {ponData.filter(p => p.status === 'completed').length}
                  </Typography>
                  <Typography variant="body2" color="textSecondary">
                    Completed PONs
                  </Typography>
                </Grid>
                <Grid item xs={6} md={3}>
                  <Typography variant="h4" color="warning.main">
                    {ponData.filter(p => p.status === 'in_progress').length}
                  </Typography>
                  <Typography variant="body2" color="textSecondary">
                    In Progress PONs
                  </Typography>
                </Grid>
                <Grid item xs={6} md={3}>
                  <Typography variant="h4" color="success.main">
                    {taskData.filter(t => t.status === 'completed').length}
                  </Typography>
                  <Typography variant="body2" color="textSecondary">
                    Completed Tasks
                  </Typography>
                </Grid>
                <Grid item xs={6} md={3}>
                  <Typography variant="h4" color="error.main">
                    {taskData.filter(t => 
                      t.status !== 'completed' && 
                      new Date(t.dueDate) < new Date()
                    ).length}
                  </Typography>
                  <Typography variant="body2" color="textSecondary">
                    Overdue Tasks
                  </Typography>
                </Grid>
              </Grid>
            </CardContent>
          </Card>
        </Grid>
      </Grid>
    </Box>
  );
};

export default Reports;