import { Dialog, DialogContent, DialogDescription, DialogHeader, DialogTitle } from '@/components/ui/dialog';
import { Badge } from '@/components/ui/badge';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { LineChart, Line, BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer, PieChart, Pie, Cell } from 'recharts';
import { useEventDetail } from '@/hooks/useApi';
import { Clock, Zap, TrendingDown, Activity, CheckCircle, AlertCircle, XCircle } from 'lucide-react';
import { format, differenceInMinutes } from 'date-fns';

interface EventDetailDialogProps {
  eventId: string | null;
  open: boolean;
  onOpenChange: (open: boolean) => void;
}

const COLORS = ['hsl(var(--success))', 'hsl(var(--primary))', 'hsl(var(--warning))', 'hsl(var(--accent))'];

export const EventDetailDialog = ({ eventId, open, onOpenChange }: EventDetailDialogProps) => {
  const { data: event, isLoading } = useEventDetail(eventId);

  if (!eventId) return null;

  const getStatusBadge = (status: string) => {
    const configs = {
      active: { icon: Activity, className: 'bg-success/10 text-success border-success/20' },
      completed: { icon: CheckCircle, className: 'bg-primary/10 text-primary border-primary/20' },
      scheduled: { icon: Clock, className: 'bg-warning/10 text-warning border-warning/20' },
      cancelled: { icon: XCircle, className: 'bg-destructive/10 text-destructive border-destructive/20' },
    };

    const config = configs[status as keyof typeof configs] || configs.active;
    const Icon = config.icon;

    return (
      <Badge variant="outline" className={config.className}>
        <Icon className="h-3 w-3 mr-1" />
        {status.charAt(0).toUpperCase() + status.slice(1)}
      </Badge>
    );
  };

  const duration = event ? differenceInMinutes(new Date(event.endTime), new Date(event.startTime)) : 0;
  const achievement = event && event.requestedReductionKw > 0 
    ? ((event.actualReductionKw / event.requestedReductionKw) * 100)
    : 0;

  // Prepare VEN participation data
  const venData = event?.vens?.map(v => ({
    name: v.venName.length > 20 ? v.venName.substring(0, 17) + '...' : v.venName,
    shed: v.shedKw,
    status: v.status,
  })) || [];

  // Prepare pie chart data for status breakdown
  const statusBreakdown = event?.vens?.reduce((acc, v) => {
    const status = v.status || 'unknown';
    acc[status] = (acc[status] || 0) + 1;
    return acc;
  }, {} as Record<string, number>) || {};

  const statusPieData = Object.entries(statusBreakdown).map(([name, value]) => ({
    name: name.charAt(0).toUpperCase() + name.slice(1),
    value,
  }));

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="max-w-5xl max-h-[90vh] overflow-y-auto">
        <DialogHeader>
          <div className="flex items-center justify-between">
            <div>
              <DialogTitle className="flex items-center gap-2">
                <Zap className="h-5 w-5 text-warning" />
                DR Event Details
              </DialogTitle>
              <DialogDescription className="font-mono text-xs mt-1">{eventId}</DialogDescription>
            </div>
            {event && getStatusBadge(event.status)}
          </div>
        </DialogHeader>

        {isLoading && (
          <div className="p-8 text-center text-muted-foreground">Loading event details...</div>
        )}

        {event && (
          <div className="space-y-6">
            {/* Summary Cards */}
            <div className="grid grid-cols-4 gap-4">
              <Card>
                <CardHeader className="pb-2">
                  <CardTitle className="text-xs text-muted-foreground">Requested</CardTitle>
                </CardHeader>
                <CardContent>
                  <div className="text-2xl font-bold text-warning">{event.requestedReductionKw.toFixed(1)} kW</div>
                </CardContent>
              </Card>

              <Card>
                <CardHeader className="pb-2">
                  <CardTitle className="text-xs text-muted-foreground">Actual</CardTitle>
                </CardHeader>
                <CardContent>
                  <div className="text-2xl font-bold text-success">{event.actualReductionKw.toFixed(1)} kW</div>
                </CardContent>
              </Card>

              <Card>
                <CardHeader className="pb-2">
                  <CardTitle className="text-xs text-muted-foreground">Achievement</CardTitle>
                </CardHeader>
                <CardContent>
                  <div className={`text-2xl font-bold ${achievement >= 90 ? 'text-success' : achievement >= 75 ? 'text-warning' : 'text-destructive'}`}>
                    {achievement.toFixed(1)}%
                  </div>
                </CardContent>
              </Card>

              <Card>
                <CardHeader className="pb-2">
                  <CardTitle className="text-xs text-muted-foreground">VENs</CardTitle>
                </CardHeader>
                <CardContent>
                  <div className="text-2xl font-bold text-primary">{event.vens?.length || 0}</div>
                </CardContent>
              </Card>
            </div>

            {/* Timeline */}
            <Card>
              <CardHeader>
                <CardTitle className="text-sm flex items-center gap-2">
                  <Clock className="h-4 w-4" />
                  Event Timeline
                </CardTitle>
              </CardHeader>
              <CardContent className="space-y-2">
                <div className="grid grid-cols-3 gap-4 text-sm">
                  <div>
                    <div className="text-muted-foreground text-xs mb-1">Start Time</div>
                    <div className="font-medium">{format(new Date(event.startTime), 'MMM d, yyyy')}</div>
                    <div className="text-xs">{format(new Date(event.startTime), 'HH:mm:ss')}</div>
                  </div>
                  <div>
                    <div className="text-muted-foreground text-xs mb-1">End Time</div>
                    <div className="font-medium">{format(new Date(event.endTime), 'MMM d, yyyy')}</div>
                    <div className="text-xs">{format(new Date(event.endTime), 'HH:mm:ss')}</div>
                  </div>
                  <div>
                    <div className="text-muted-foreground text-xs mb-1">Duration</div>
                    <div className="font-medium">{duration} minutes</div>
                    <div className="text-xs">{(duration / 60).toFixed(1)} hours</div>
                  </div>
                </div>
              </CardContent>
            </Card>

            {/* VEN Participation Charts */}
            {venData.length > 0 && (
              <div className="grid grid-cols-2 gap-4">
                <Card>
                  <CardHeader>
                    <CardTitle className="text-sm">Shed by VEN</CardTitle>
                    <CardDescription>Power reduction per participating VEN</CardDescription>
                  </CardHeader>
                  <CardContent>
                    <ResponsiveContainer width="100%" height={300}>
                      <BarChart data={venData} layout="horizontal">
                        <CartesianGrid strokeDasharray="3 3" stroke="hsl(var(--border))" />
                        <XAxis type="number" stroke="hsl(var(--muted-foreground))" fontSize={11} label={{ value: 'kW', position: 'insideRight', offset: -5 }} />
                        <YAxis type="category" dataKey="name" stroke="hsl(var(--muted-foreground))" fontSize={10} width={100} />
                        <Tooltip
                          contentStyle={{ backgroundColor: 'hsl(var(--card))', border: '1px solid hsl(var(--border))' }}
                          labelStyle={{ color: 'hsl(var(--foreground))' }}
                        />
                        <Bar dataKey="shed" fill="hsl(var(--success))" name="Shed (kW)" />
                      </BarChart>
                    </ResponsiveContainer>
                  </CardContent>
                </Card>

                {statusPieData.length > 0 && (
                  <Card>
                    <CardHeader>
                      <CardTitle className="text-sm">VEN Status Distribution</CardTitle>
                      <CardDescription>Response status breakdown</CardDescription>
                    </CardHeader>
                    <CardContent>
                      <ResponsiveContainer width="100%" height={300}>
                        <PieChart>
                          <Pie
                            data={statusPieData}
                            cx="50%"
                            cy="50%"
                            labelLine={false}
                            label={({ name, percent }) => `${name}: ${(percent * 100).toFixed(0)}%`}
                            outerRadius={80}
                            fill="#8884d8"
                            dataKey="value"
                          >
                            {statusPieData.map((entry, index) => (
                              <Cell key={`cell-${index}`} fill={COLORS[index % COLORS.length]} />
                            ))}
                          </Pie>
                          <Tooltip />
                        </PieChart>
                      </ResponsiveContainer>
                    </CardContent>
                  </Card>
                )}
              </div>
            )}

            {/* Participating VENs List */}
            {venData.length > 0 && (
              <Card>
                <CardHeader>
                  <CardTitle className="text-sm">Participating VENs</CardTitle>
                  <CardDescription>Detailed response from each VEN</CardDescription>
                </CardHeader>
                <CardContent>
                  <div className="space-y-2">
                    {event.vens?.map((ven) => (
                      <div key={ven.venId} className="flex items-center justify-between p-3 bg-muted/30 rounded-lg">
                        <div className="flex-1">
                          <div className="font-medium">{ven.venName}</div>
                          <div className="text-xs text-muted-foreground font-mono">{ven.venId}</div>
                        </div>
                        <div className="flex items-center gap-4">
                          <div className="text-right">
                            <div className="text-sm font-medium text-success">{ven.shedKw.toFixed(2)} kW</div>
                            <div className="text-xs text-muted-foreground">Shed</div>
                          </div>
                          <Badge variant="outline" className="text-xs">
                            {ven.status.charAt(0).toUpperCase() + ven.status.slice(1)}
                          </Badge>
                        </div>
                      </div>
                    ))}
                  </div>
                </CardContent>
              </Card>
            )}

            {venData.length === 0 && (
              <Card>
                <CardContent className="p-8 text-center text-muted-foreground">
                  <AlertCircle className="h-8 w-8 mx-auto mb-2 opacity-50" />
                  <div>No VEN participation data available</div>
                </CardContent>
              </Card>
            )}
          </div>
        )}
      </DialogContent>
    </Dialog>
  );
};
