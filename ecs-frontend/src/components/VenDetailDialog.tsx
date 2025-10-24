import { Dialog, DialogContent, DialogDescription, DialogHeader, DialogTitle } from '@/components/ui/dialog';
import { Badge } from '@/components/ui/badge';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { LineChart, Line, BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer } from 'recharts';
import { useVenDetail, useVenCircuitHistory, useVenEventHistory } from '@/hooks/useApi';
import { Zap, Activity, MapPin, Clock, AlertTriangle, CheckCircle, Settings } from 'lucide-react';
import { format } from 'date-fns';

interface VenDetailDialogProps {
  venId: string | null;
  open: boolean;
  onOpenChange: (open: boolean) => void;
}

export const VenDetailDialog = ({ venId, open, onOpenChange }: VenDetailDialogProps) => {
  const { data: ven, isLoading } = useVenDetail(venId);
  const { data: circuitHistory } = useVenCircuitHistory(venId, { limit: 50 });
  const { data: eventHistory } = useVenEventHistory(venId);

  if (!venId) return null;

  const getStatusIcon = (status: string) => {
    switch (status) {
      case 'online':
        return <CheckCircle className="h-4 w-4 text-online" />;
      case 'offline':
        return <AlertTriangle className="h-4 w-4 text-offline" />;
      case 'maintenance':
        return <Settings className="h-4 w-4 text-warning" />;
      default:
        return <AlertTriangle className="h-4 w-4 text-muted-foreground" />;
    }
  };

  const getStatusBadge = (status: string) => {
    const variants = {
      online: 'bg-online/10 text-online border-online/20',
      offline: 'bg-offline/10 text-offline border-offline/20',
      maintenance: 'bg-warning/10 text-warning border-warning/20'
    };
    
    return (
      <Badge variant="outline" className={variants[status as keyof typeof variants] || ''}>
        {status.charAt(0).toUpperCase() + status.slice(1)}
      </Badge>
    );
  };

  // Prepare chart data with error handling
  const powerChartData = circuitHistory?.snapshots?.map(ch => {
    try {
      return {
        time: format(new Date(ch.timestamp), 'HH:mm:ss'),
        power: ch.currentPowerKw || 0,
        capacity: ch.shedCapabilityKw || 0,
      };
    } catch (error) {
      console.error('Error formatting circuit history:', error, ch);
      return {
        time: 'Invalid',
        power: 0,
        capacity: 0,
      };
    }
  }).filter(d => d.time !== 'Invalid') || [];

  const loadBreakdown = ven?.loads?.map(load => ({
    name: load.type || 'Unknown',
    current: load.currentPowerKw || 0,
    capacity: load.capacityKw || 0,
    shedCapability: load.shedCapabilityKw || 0,
  })) || [];

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="max-w-5xl max-h-[90vh] overflow-y-auto">
        <DialogHeader>
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-3">
              {ven && getStatusIcon(ven.status)}
              <div>
                <DialogTitle>{ven?.name || venId}</DialogTitle>
                <DialogDescription className="font-mono text-xs">{venId}</DialogDescription>
              </div>
            </div>
            {ven && getStatusBadge(ven.status)}
          </div>
        </DialogHeader>

        {isLoading && (
          <div className="p-8 text-center text-muted-foreground">Loading VEN details...</div>
        )}

        {ven && (
          <Tabs defaultValue="overview" className="w-full">
            <TabsList className="grid w-full grid-cols-4">
              <TabsTrigger value="overview">Overview</TabsTrigger>
              <TabsTrigger value="loads">Loads & Circuits</TabsTrigger>
              <TabsTrigger value="power">Power History</TabsTrigger>
              <TabsTrigger value="events">Event History</TabsTrigger>
            </TabsList>

            <TabsContent value="overview" className="space-y-4">
              <div className="grid grid-cols-2 gap-4">
                <Card>
                  <CardHeader className="pb-3">
                    <CardTitle className="text-sm flex items-center gap-2">
                      <Zap className="h-4 w-4 text-primary" />
                      Power Metrics
                    </CardTitle>
                  </CardHeader>
                  <CardContent className="space-y-2">
                    <div className="flex justify-between">
                      <span className="text-sm text-muted-foreground">Current Power</span>
                      <span className="font-medium text-success">{(ven.metrics?.currentPowerKw || 0).toFixed(2)} kW</span>
                    </div>
                    <div className="flex justify-between">
                      <span className="text-sm text-muted-foreground">Shed Capability</span>
                      <span className="font-medium text-primary">{(ven.metrics?.shedAvailabilityKw || 0).toFixed(2)} kW</span>
                    </div>
                    <div className="flex justify-between">
                      <span className="text-sm text-muted-foreground">Active Event</span>
                      <span className="font-medium">{ven.metrics?.activeEventId || 'None'}</span>
                    </div>
                  </CardContent>
                </Card>

                <Card>
                  <CardHeader className="pb-3">
                    <CardTitle className="text-sm flex items-center gap-2">
                      <MapPin className="h-4 w-4 text-accent" />
                      Location
                    </CardTitle>
                  </CardHeader>
                  <CardContent className="space-y-2">
                    <div className="flex justify-between">
                      <span className="text-sm text-muted-foreground">Latitude</span>
                      <span className="font-medium">{ven.location?.lat?.toFixed(4) || 'N/A'}</span>
                    </div>
                    <div className="flex justify-between">
                      <span className="text-sm text-muted-foreground">Longitude</span>
                      <span className="font-medium">{ven.location?.lon?.toFixed(4) || 'N/A'}</span>
                    </div>
                    <div className="flex justify-between">
                      <span className="text-sm text-muted-foreground">Created</span>
                      <span className="font-medium text-xs">
                        {ven.createdAt ? format(new Date(ven.createdAt), 'MMM d, yyyy') : 'N/A'}
                      </span>
                    </div>
                  </CardContent>
                </Card>
              </div>

              {loadBreakdown.length > 0 && (
                <Card>
                  <CardHeader>
                    <CardTitle className="text-sm">Load Distribution</CardTitle>
                    <CardDescription>Power usage by circuit type</CardDescription>
                  </CardHeader>
                  <CardContent>
                    <ResponsiveContainer width="100%" height={250}>
                      <BarChart data={loadBreakdown}>
                        <CartesianGrid strokeDasharray="3 3" stroke="hsl(var(--border))" />
                        <XAxis dataKey="name" stroke="hsl(var(--muted-foreground))" fontSize={12} />
                        <YAxis stroke="hsl(var(--muted-foreground))" fontSize={12} label={{ value: 'kW', angle: -90, position: 'insideLeft' }} />
                        <Tooltip
                          contentStyle={{ backgroundColor: 'hsl(var(--card))', border: '1px solid hsl(var(--border))' }}
                          labelStyle={{ color: 'hsl(var(--foreground))' }}
                        />
                        <Legend />
                        <Bar dataKey="current" fill="hsl(var(--success))" name="Current" />
                        <Bar dataKey="shedCapability" fill="hsl(var(--primary))" name="Shed Capability" />
                        <Bar dataKey="capacity" fill="hsl(var(--muted))" name="Capacity" />
                      </BarChart>
                    </ResponsiveContainer>
                  </CardContent>
                </Card>
              )}
            </TabsContent>

            <TabsContent value="loads" className="space-y-3">
              {ven.loads && ven.loads.length > 0 ? (
                ven.loads.map((load) => (
                  <Card key={load.id}>
                    <CardContent className="p-4">
                      <div className="flex items-center justify-between mb-3">
                        <div>
                          <h4 className="font-semibold">{load.name || load.type}</h4>
                          <p className="text-xs text-muted-foreground font-mono">{load.id}</p>
                        </div>
                        <Badge variant="outline">{load.type}</Badge>
                      </div>
                      <div className="grid grid-cols-3 gap-3">
                        <div className="text-center p-2 bg-muted/30 rounded">
                          <div className="text-sm font-medium text-success">{load.currentPowerKw.toFixed(1)} kW</div>
                          <div className="text-xs text-muted-foreground">Current</div>
                        </div>
                        <div className="text-center p-2 bg-muted/30 rounded">
                          <div className="text-sm font-medium text-primary">{load.shedCapabilityKw.toFixed(1)} kW</div>
                          <div className="text-xs text-muted-foreground">Shed Cap</div>
                        </div>
                        <div className="text-center p-2 bg-muted/30 rounded">
                          <div className="text-sm font-medium">{load.capacityKw.toFixed(1)} kW</div>
                          <div className="text-xs text-muted-foreground">Capacity</div>
                        </div>
                      </div>
                    </CardContent>
                  </Card>
                ))
              ) : (
                <div className="p-8 text-center text-muted-foreground">No loads configured</div>
              )}
            </TabsContent>

            <TabsContent value="power">
              <Card>
                <CardHeader>
                  <CardTitle className="text-sm">Power Usage Over Time</CardTitle>
                  <CardDescription>Last 50 readings</CardDescription>
                </CardHeader>
                <CardContent>
                  {powerChartData.length > 0 ? (
                    <ResponsiveContainer width="100%" height={350}>
                      <LineChart data={powerChartData}>
                        <CartesianGrid strokeDasharray="3 3" stroke="hsl(var(--border))" />
                        <XAxis dataKey="time" stroke="hsl(var(--muted-foreground))" fontSize={11} />
                        <YAxis stroke="hsl(var(--muted-foreground))" fontSize={11} label={{ value: 'kW', angle: -90, position: 'insideLeft' }} />
                        <Tooltip
                          contentStyle={{ backgroundColor: 'hsl(var(--card))', border: '1px solid hsl(var(--border))' }}
                          labelStyle={{ color: 'hsl(var(--foreground))' }}
                        />
                        <Legend />
                        <Line type="monotone" dataKey="power" stroke="hsl(var(--success))" name="Power Usage" strokeWidth={2} dot={false} />
                        <Line type="monotone" dataKey="capacity" stroke="hsl(var(--primary))" name="Shed Capacity" strokeWidth={2} dot={false} strokeDasharray="5 5" />
                      </LineChart>
                    </ResponsiveContainer>
                  ) : (
                    <div className="p-8 text-center text-muted-foreground">No power history available</div>
                  )}
                </CardContent>
              </Card>
            </TabsContent>

            <TabsContent value="events">
              <div className="space-y-3">
                {eventHistory && eventHistory.length > 0 ? (
                  eventHistory.map((evt) => (
                    <Card key={evt.eventId + evt.timestamp}>
                      <CardContent className="p-4">
                        <div className="flex items-center justify-between mb-2">
                          <div className="flex items-center gap-2">
                            <Clock className="h-4 w-4 text-muted-foreground" />
                            <span className="text-sm font-medium">
                              {evt.timestamp ? format(new Date(evt.timestamp), 'MMM d, yyyy HH:mm:ss') : 'N/A'}
                            </span>
                          </div>
                          <Badge variant="outline" className="text-xs">{evt.status || 'unknown'}</Badge>
                        </div>
                        <div className="text-xs text-muted-foreground mb-2 font-mono">Event: {evt.eventId}</div>
                        {evt.circuits && evt.circuits.length > 0 && (
                          <div className="space-y-1">
                            <div className="text-xs font-medium">Curtailed Circuits:</div>
                            <div className="grid grid-cols-2 gap-2">
                              {evt.circuits.map((circuit, idx) => (
                                <div key={idx} className="flex justify-between text-xs bg-muted/30 p-2 rounded">
                                  <span className="text-muted-foreground">{circuit.loadId}</span>
                                  <span className="font-medium text-warning">{(circuit.curtailedKw || 0).toFixed(2)} kW</span>
                                </div>
                              ))}
                            </div>
                          </div>
                        )}
                      </CardContent>
                    </Card>
                  ))
                ) : (
                  <div className="p-8 text-center text-muted-foreground">No event history available</div>
                )}
              </div>
            </TabsContent>
          </Tabs>
        )}
      </DialogContent>
    </Dialog>
  );
};
