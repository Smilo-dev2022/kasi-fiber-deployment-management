import React, { useState, useEffect } from 'react';
import {
  Grid,
  Card,
  CardContent,
  Typography,
  Box,
  CircularProgress,
  Alert,
} from '@mui/material';
import {
  Cable as PONIcon,
  Task as TaskIcon,
  CheckCircle as CompletedIcon,
  Schedule as PendingIcon,
} from '@mui/icons-material';
import { api } from '../../api/client';

const Dashboard = () => {
  const [stats, setStats] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [ops, setOps] = useState(null);

  useEffect(() => {
    const fetchStats = async () => {
      try {
        const token = localStorage.getItem('token');
        const config = {
          headers: {
            'x-auth-token': token,
          },
        };

        const [res, opsRes] = await Promise.all([
          api.get('/reports/dashboard', config),
          api.get('/reports/ops', config)
        ]);
        setStats(res.data);
        setOps(opsRes.data);
        setLoading(false);
      } catch (err) {
        setError('Failed to load dashboard data');
        setLoading(false);
      }
    };

    fetchStats();
  }, []);

  if (loading) {
    return (
      <Box display="flex" justifyContent="center" alignItems="center" minHeight="400px">
        <CircularProgress />
      </Box>
    );
  }

  if (error) {
    return (
      <Alert severity="error" sx={{ mb: 2 }}>
        {error}
      </Alert>
    );
  }

  const StatCard = ({ title, value, icon, color = 'primary' }) => (
    <Card>
      <CardContent>
        <Box display="flex" alignItems="center" justifyContent="space-between">
          <Box>
            <Typography color="textSecondary" gutterBottom variant="h6">
              {title}
            </Typography>
            <Typography variant="h4" component="div">
              {value}
            </Typography>
          </Box>
          <Box color={`${color}.main`} sx={{ fontSize: 48 }}>
            {icon}
          </Box>
        </Box>
      </CardContent>
    </Card>
  );

  return (
    <Box>
      <Typography variant="h4" gutterBottom>
        Dashboard
      </Typography>
      
      <Grid container spacing={3} sx={{ mb: 3 }}>
        <Grid item xs={12} sm={6} md={3}>
          <StatCard
            title="Total PONs"
            value={stats?.pons?.total || 0}
            icon={<PONIcon />}
            color="primary"
          />
        </Grid>
        <Grid item xs={12} sm={6} md={3}>
          <StatCard
            title="Completed PONs"
            value={stats?.pons?.completed || 0}
            icon={<CompletedIcon />}
            color="success"
          />
        </Grid>
        <Grid item xs={12} sm={6} md={3}>
          <StatCard
            title="Total Tasks"
            value={stats?.tasks?.total || 0}
            icon={<TaskIcon />}
            color="info"
          />
        </Grid>
        <Grid item xs={12} sm={6} md={3}>
          <StatCard
            title="Overdue Tasks"
            value={stats?.tasks?.overdue || 0}
            icon={<PendingIcon />}
            color="error"
          />
        </Grid>
        <Grid item xs={12} sm={6} md={3}>
          <StatCard
            title="MTTR (hrs)"
            value={ops ? ops.mttrHours : 0}
            icon={<PendingIcon />}
            color="secondary"
          />
        </Grid>
        <Grid item xs={12} sm={6} md={3}>
          <StatCard
            title="Avg Uptime (30d)"
            value={ops && ops.uptimeByWard && ops.uptimeByWard.length > 0 ?
              (ops.uptimeByWard.reduce((a, b) => a + (b.uptime || 0), 0) / ops.uptimeByWard.length).toFixed(1) + '%' : '—'}
            icon={<CompletedIcon />}
            color="success"
          />
        </Grid>
      </Grid>

      <Grid container spacing={3}>
        <Grid item xs={12} md={6}>
          <Card>
            <CardContent>
              <Typography variant="h6" gutterBottom>
                PON Status Overview
              </Typography>
              <Box sx={{ mt: 2 }}>
                <Box display="flex" justifyContent="space-between" mb={1}>
                  <Typography variant="body2">Completed</Typography>
                  <Typography variant="body2" color="success.main">
                    {stats?.pons?.completed || 0}
                  </Typography>
                </Box>
                <Box display="flex" justifyContent="space-between" mb={1}>
                  <Typography variant="body2">In Progress</Typography>
                  <Typography variant="body2" color="warning.main">
                    {stats?.pons?.inProgress || 0}
                  </Typography>
                </Box>
                <Box display="flex" justifyContent="space-between">
                  <Typography variant="body2">Planned</Typography>
                  <Typography variant="body2" color="info.main">
                    {stats?.pons?.planned || 0}
                  </Typography>
                </Box>
              </Box>
            </CardContent>
          </Card>
        </Grid>

        <Grid item xs={12} md={6}>
          <Card>
            <CardContent>
              <Typography variant="h6" gutterBottom>
                Task Status Overview
              </Typography>
              <Box sx={{ mt: 2 }}>
                <Box display="flex" justifyContent="space-between" mb={1}>
                  <Typography variant="body2">Completed</Typography>
                  <Typography variant="body2" color="success.main">
                    {stats?.tasks?.completed || 0}
                  </Typography>
                </Box>
                <Box display="flex" justifyContent="space-between" mb={1}>
                  <Typography variant="body2">Pending</Typography>
                  <Typography variant="body2" color="warning.main">
                    {stats?.tasks?.pending || 0}
                  </Typography>
                </Box>
                <Box display="flex" justifyContent="space-between">
                  <Typography variant="body2">Overdue</Typography>
                  <Typography variant="body2" color="error.main">
                    {stats?.tasks?.overdue || 0}
                  </Typography>
                </Box>
              </Box>
            </CardContent>
          </Card>
        </Grid>

        <Grid item xs={12} md={6}>
          <Card>
            <CardContent>
              <Typography variant="h6" gutterBottom>
                Uptime by Ward (30d)
              </Typography>
              <Box sx={{ mt: 2, maxHeight: 240, overflowY: 'auto' }}>
                {ops && ops.uptimeByWard && ops.uptimeByWard.length > 0 ? (
                  ops.uptimeByWard.map((w) => (
                    <Box key={w.ward} display="flex" justifyContent="space-between" mb={1}>
                      <Typography variant="body2">{w.ward}</Typography>
                      <Typography variant="body2" color="textSecondary">{w.uptime.toFixed(2)}%</Typography>
                    </Box>
                  ))
                ) : (
                  <Typography variant="body2" color="textSecondary">No data</Typography>
                )}
              </Box>
            </CardContent>
          </Card>
        </Grid>
      </Grid>
    </Box>
  );
};

export default Dashboard;