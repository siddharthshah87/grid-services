import React, { useState } from 'react';
import { AppBar, Toolbar, Typography, Container, Grid, Paper, Table, TableHead, TableRow, TableCell, TableBody, Button } from '@mui/material';
import { MapContainer, TileLayer, Marker, Popup } from 'react-leaflet';
import 'leaflet/dist/leaflet.css';
import { Bar } from 'react-chartjs-2';
import { Chart as ChartJS } from 'chart.js/auto';
import { vens } from './dummyData';

function App() {
  const totalShed = vens.reduce((sum, v) => sum + v.shed_kw, 0);
  const [eventIssued, setEventIssued] = useState(false);

  const chartData = {
    labels: vens.map(v => v.id),
    datasets: [
      {
        label: 'Shed kW',
        data: vens.map(v => v.shed_kw),
        backgroundColor: 'rgba(75,192,192,0.6)'
      }
    ]
  };

  return (
    <div>
      <AppBar position="static">
        <Toolbar>
          <Typography variant="h6">Smart Grid Control Center</Typography>
        </Toolbar>
      </AppBar>

      <Container sx={{ mt: 4 }}>
        <Typography variant="h5" gutterBottom>Total Shed Capability: {totalShed} kW</Typography>
        <Button variant="contained" onClick={() => setEventIssued(true)}>Issue ADR Event</Button>
        {eventIssued && (
          <Typography color="success.main" sx={{ mt: 2 }}>
            ADR Event issued! Expected reduction: {totalShed} kW
          </Typography>
        )}

        <Grid container spacing={4} sx={{ mt: 1 }}>
          <Grid item xs={12} md={6}>
            <Paper sx={{ p: 2 }}>
              <Typography variant="h6" gutterBottom>VEN List</Typography>
              <Table size="small">
                <TableHead>
                  <TableRow>
                    <TableCell>ID</TableCell>
                    <TableCell>Status</TableCell>
                    <TableCell align="right">Shed kW</TableCell>
                    <TableCell>Address</TableCell>
                  </TableRow>
                </TableHead>
                <TableBody>
                  {vens.map(ven => (
                    <TableRow key={ven.id}>
                      <TableCell>{ven.id}</TableCell>
                      <TableCell>{ven.status}</TableCell>
                      <TableCell align="right">{ven.shed_kw}</TableCell>
                      <TableCell>{ven.address}</TableCell>
                    </TableRow>
                  ))}
                </TableBody>
              </Table>
            </Paper>
          </Grid>

          <Grid item xs={12} md={6}>
            <Paper sx={{ p: 2 }}>
              <Typography variant="h6" gutterBottom>Network Capability</Typography>
              <Bar data={chartData} />
            </Paper>
          </Grid>

          <Grid item xs={12}>
            <Paper sx={{ p: 2 }}>
              <Typography variant="h6" gutterBottom>VEN Locations</Typography>
              <MapContainer center={[37.7749, -122.4194]} zoom={9} style={{ height: '400px', width: '100%' }}>
                <TileLayer
                  attribution='&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors'
                  url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png"
                />
                {vens.map(v => (
                  <Marker key={v.id} position={[v.lat, v.lon]}>
                    <Popup>
                      <strong>{v.id}</strong><br />
                      Status: {v.status}<br />
                      Shed: {v.shed_kw} kW
                    </Popup>
                  </Marker>
                ))}
              </MapContainer>
            </Paper>
          </Grid>
        </Grid>
      </Container>
    </div>
  );
}

export default App;
