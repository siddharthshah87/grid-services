import React, { useState } from 'react';
import {
  AppBar,
  Toolbar,
  Typography,
  Container,
  Grid,
  Paper,
  Table,
  TableHead,
  TableRow,
  TableCell,
  TableBody,
  Button,
  CssBaseline,
  LinearProgress,
  Box,
  Card,
  CardContent,
  ThemeProvider,
  createTheme
} from '@mui/material';
import { MapContainer, TileLayer, Marker, Popup } from 'react-leaflet';
import 'leaflet/dist/leaflet.css';
import { Bar } from 'react-chartjs-2';
import { Chart as ChartJS } from 'chart.js/auto';
import { vens, networkStats } from './dummyData';

const theme = createTheme({
  palette: {
    mode: 'dark',
    background: { default: '#111317', paper: '#1c1e24' },
    primary: { main: '#2bbdee' },
    success: { main: '#22c55e' },
    warning: { main: '#facc15' },
    text: { primary: '#fcfbf8', secondary: '#9ca3af' }
  }
});

function App() {
  const [eventIssued, setEventIssued] = useState(false);

  const chartData = {
    labels: vens.map(v => v.id),
    datasets: [
      {
        label: 'Controllable kW',
        data: vens.map(v => v.shed_kw),
        backgroundColor: '#2bbdee'
      }
    ]
  };

  const efficiencyColor =
    networkStats.networkEfficiency > 90
      ? 'success.main'
      : networkStats.networkEfficiency > 75
        ? 'warning.main'
        : 'error.main';

  return (
    <ThemeProvider theme={theme}>
      <CssBaseline />
      <AppBar position="static" color="transparent" elevation={0}>
        <Toolbar>
          <Typography variant="h6" sx={{ flexGrow: 1 }}>
            Energy Control Dashboard
          </Typography>
          <Button variant="contained" onClick={() => setEventIssued(true)}>
            Issue ADR Event
          </Button>
        </Toolbar>
      </AppBar>

      <Container sx={{ mt: 4 }}>
        {eventIssued && (
          <Typography color="success.main" sx={{ mb: 2 }}>
            ADR Event issued! Expected reduction: {networkStats.totalControllablePower} kW
          </Typography>
        )}
        <Grid container spacing={4}>
          <Grid item xs={12} md={4}>
            <Card>
              <CardContent>
                <Typography variant="h6" gutterBottom>
                  Network Stats
                </Typography>
                <Typography variant="body2" color="text.secondary">
                  Total Controllable Power
                </Typography>
                <Typography variant="h5" gutterBottom>
                  {networkStats.totalControllablePower} kW
                </Typography>
                <Typography variant="body2" color="text.secondary" sx={{ mt: 2 }}>
                  Current Load Reduction
                </Typography>
                <Typography variant="h6">
                  {networkStats.currentLoadReduction} kW
                </Typography>
                <Box sx={{ mt: 2 }}>
                  <Typography variant="body2" color="text.secondary">
                    Network Efficiency {networkStats.networkEfficiency}%
                  </Typography>
                  <LinearProgress
                    variant="determinate"
                    value={networkStats.networkEfficiency}
                    sx={{
                      height: 10,
                      borderRadius: 5,
                      backgroundColor: '#2e2e33',
                      '& .MuiLinearProgress-bar': {
                        backgroundColor: theme.palette[efficiencyColor.split('.')[0]].main
                      }
                    }}
                  />
                </Box>
              </CardContent>
            </Card>
          </Grid>

          <Grid item xs={12} md={8}>
            <Paper sx={{ p: 2 }}>
              <Typography variant="h6" gutterBottom>
                VEN Controllable Power
              </Typography>
              <Bar data={chartData} />
            </Paper>
          </Grid>

          <Grid item xs={12}>
            <Paper sx={{ p: 2 }}>
              <Typography variant="h6" gutterBottom>
                VEN List
              </Typography>
              <Table size="small">
                <TableHead>
                  <TableRow>
                    <TableCell>ID</TableCell>
                    <TableCell>Status</TableCell>
                    <TableCell align="right">Controllable kW</TableCell>
                    <TableCell>Address</TableCell>
                  </TableRow>
                </TableHead>
                <TableBody>
                  {vens.map(ven => (
                    <TableRow key={ven.id}>
                      <TableCell>{ven.id}</TableCell>
                      <TableCell sx={{ color: ven.status === 'online' ? 'success.main' : 'error.main' }}>
                        {ven.status}
                      </TableCell>
                      <TableCell align="right">{ven.shed_kw}</TableCell>
                      <TableCell>{ven.address}</TableCell>
                    </TableRow>
                  ))}
                </TableBody>
              </Table>
            </Paper>
          </Grid>

          <Grid item xs={12}>
            <Paper sx={{ p: 2 }}>
              <Typography variant="h6" gutterBottom>
                VEN Locations
              </Typography>
              <MapContainer center={[37.7749, -122.4194]} zoom={9} style={{ height: '400px', width: '100%' }}>
                <TileLayer
                  attribution='&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors'
                  url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png"
                />
                {vens.map(v => (
                  <Marker key={v.id} position={[v.lat, v.lon]}>
                    <Popup>
                      <strong>{v.id}</strong>
                      <br />Status: {v.status}
                      <br />Controllable: {v.shed_kw} kW
                    </Popup>
                  </Marker>
                ))}
              </MapContainer>
            </Paper>
          </Grid>
        </Grid>
      </Container>
    </ThemeProvider>
  );
}

export default App;
