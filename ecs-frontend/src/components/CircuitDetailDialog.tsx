import { Dialog, DialogContent, DialogDescription, DialogHeader, DialogTitle } from '@/components/ui/dialog';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer, Area, AreaChart } from 'recharts';
import { useVenCircuitHistory } from '@/hooks/useApi';
import { Zap, Activity, TrendingUp, TrendingDown, Calendar } from 'lucide-react';
import { format } from 'date-fns';
import { useMemo } from 'react';

interface CircuitDetailDialogProps {
  venId: string;
  loadId: string;
  loadName: string;
  loadType: string;
  currentPowerKw: number;
  capacityKw: number;
  shedCapabilityKw: number;
  open: boolean;
  onOpenChange: (open: boolean) => void;
}

export const CircuitDetailDialog = ({
  venId,
  loadId,
  loadName,
  loadType,
  currentPowerKw,
  capacityKw,
  shedCapabilityKw,
  open,
  onOpenChange
}: CircuitDetailDialogProps) => {
  // Get data for the last 24 hours - memoize to prevent query key changes on every render
  const startTime = useMemo(() => new Date(Date.now() - 24 * 60 * 60 * 1000).toISOString(), []);
  
  const { data: history, isLoading, isError } = useVenCircuitHistory(
    open ? venId : null,
    { loadId, start: startTime, limit: 5000 }
  );

  // Prepare chart data
  const chartData = history?.snapshots?.map(snap => ({
    time: format(new Date(snap.timestamp), 'MMM dd HH:mm'),
    power: snap.currentPowerKw || 0,
    capacity: capacityKw,
    shed: shedCapabilityKw,
  })) || [];

  // Calculate statistics
  const avgPower = history?.snapshots?.length 
    ? history.snapshots.reduce((sum, s) => sum + (s.currentPowerKw || 0), 0) / history.snapshots.length
    : 0;
  
  const maxPower = history?.snapshots?.length
    ? Math.max(...history.snapshots.map(s => s.currentPowerKw || 0))
    : 0;

  const minPower = history?.snapshots?.length
    ? Math.min(...history.snapshots.map(s => s.currentPowerKw || 0))
    : 0;

  const utilizationPercent = capacityKw > 0 ? (currentPowerKw / capacityKw) * 100 : 0;

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="max-w-4xl max-h-[90vh] overflow-y-auto">
        <DialogHeader>
          <DialogTitle className="flex items-center gap-2">
            <Zap className="h-5 w-5 text-primary" />
            {loadName || loadType}
          </DialogTitle>
          <DialogDescription className="font-mono text-xs mt-1">{loadId}</DialogDescription>
        </DialogHeader>

        <div className="space-y-6">
          {/* Current Metrics - Always show these */}
          <div className="grid grid-cols-4 gap-4">
            <Card>
              <CardHeader className="pb-2">
                <CardTitle className="text-xs text-muted-foreground">Current Power</CardTitle>
              </CardHeader>
              <CardContent>
                <div className="text-2xl font-bold text-success">{currentPowerKw.toFixed(2)} kW</div>
                <div className="text-xs text-muted-foreground mt-1">
                  {utilizationPercent.toFixed(1)}% utilization
                </div>
              </CardContent>
            </Card>

            <Card>
              <CardHeader className="pb-2">
                <CardTitle className="text-xs text-muted-foreground">Rated Power</CardTitle>
              </CardHeader>
              <CardContent>
                <div className="text-2xl font-bold">{capacityKw.toFixed(2)} kW</div>
                <div className="text-xs text-muted-foreground mt-1">Maximum rated</div>
              </CardContent>
            </Card>

            <Card>
              <CardHeader className="pb-2">
                <CardTitle className="text-xs text-muted-foreground">Shed Capability</CardTitle>
              </CardHeader>
              <CardContent>
                <div className="text-2xl font-bold text-primary">{shedCapabilityKw.toFixed(2)} kW</div>
                <div className="text-xs text-muted-foreground mt-1">Available to shed</div>
              </CardContent>
            </Card>

            <Card>
              <CardHeader className="pb-2">
                <CardTitle className="text-xs text-muted-foreground">Data Points</CardTitle>
              </CardHeader>
              <CardContent>
                <div className="text-2xl font-bold text-accent">{history?.totalCount || 0}</div>
                <div className="text-xs text-muted-foreground mt-1">Historical records</div>
              </CardContent>
            </Card>
          </div>

          {/* Statistics - Show when data is available */}
          {!isLoading && !isError && history?.snapshots && history.snapshots.length > 0 && (
              <Card>
                <CardHeader className="pb-3">
                  <CardTitle className="text-sm flex items-center gap-2">
                    <Activity className="h-4 w-4 text-primary" />
                    Usage Statistics
                  </CardTitle>
                  <CardDescription>Based on last {history.snapshots.length} readings</CardDescription>
                </CardHeader>
                <CardContent>
                  <div className="grid grid-cols-3 gap-4">
                    <div className="text-center p-3 bg-muted/30 rounded-lg">
                      <div className="flex items-center justify-center gap-1 text-sm text-muted-foreground mb-1">
                        <TrendingUp className="h-3 w-3" />
                        Average
                      </div>
                      <div className="text-lg font-bold">{avgPower.toFixed(2)} kW</div>
                    </div>
                    <div className="text-center p-3 bg-muted/30 rounded-lg">
                      <div className="flex items-center justify-center gap-1 text-sm text-muted-foreground mb-1">
                        <TrendingUp className="h-3 w-3 text-warning" />
                        Peak
                      </div>
                      <div className="text-lg font-bold text-warning">{maxPower.toFixed(2)} kW</div>
                    </div>
                    <div className="text-center p-3 bg-muted/30 rounded-lg">
                      <div className="flex items-center justify-center gap-1 text-sm text-muted-foreground mb-1">
                        <TrendingDown className="h-3 w-3 text-success" />
                        Minimum
                      </div>
                      <div className="text-lg font-bold text-success">{minPower.toFixed(2)} kW</div>
                    </div>
                  </div>
                </CardContent>
              </Card>
            )}

            {/* Power History Chart */}
            <Card>
              <CardHeader>
                <CardTitle className="text-sm flex items-center gap-2">
                  <Calendar className="h-4 w-4 text-primary" />
                  Power Usage Over Time
                </CardTitle>
                <CardDescription>Last {history?.snapshots?.length || 0} readings</CardDescription>
              </CardHeader>
              <CardContent>
                {isLoading && (
                  <div className="p-8 text-center text-muted-foreground">Loading historical data...</div>
                )}
                {isError && (
                  <div className="p-8 text-center text-destructive">Failed to load circuit history</div>
                )}
                {!isLoading && !isError && chartData.length > 0 && (
                  <ResponsiveContainer width="100%" height={350}>
                    <AreaChart data={chartData}>
                      <defs>
                        <linearGradient id="colorPower" x1="0" y1="0" x2="0" y2="1">
                          <stop offset="5%" stopColor="hsl(var(--success))" stopOpacity={0.3}/>
                          <stop offset="95%" stopColor="hsl(var(--success))" stopOpacity={0}/>
                        </linearGradient>
                      </defs>
                      <CartesianGrid strokeDasharray="3 3" stroke="hsl(var(--border))" />
                      <XAxis 
                        dataKey="time" 
                        stroke="hsl(var(--muted-foreground))" 
                        fontSize={11}
                        angle={-45}
                        textAnchor="end"
                        height={60}
                      />
                      <YAxis 
                        stroke="hsl(var(--muted-foreground))" 
                        fontSize={11} 
                        label={{ value: 'Power (kW)', angle: -90, position: 'insideLeft' }} 
                      />
                      <Tooltip
                        contentStyle={{ 
                          backgroundColor: 'hsl(var(--popover))', 
                          border: '1px solid hsl(var(--border))',
                          borderRadius: '0.5rem',
                          backdropFilter: 'blur(8px)'
                        }}
                        labelStyle={{ color: 'hsl(var(--popover-foreground))', fontWeight: 600 }}
                        cursor={{ stroke: 'hsl(var(--muted))', strokeWidth: 1, strokeDasharray: '5 5' }}
                      />
                      <Legend 
                        wrapperStyle={{ color: 'hsl(var(--foreground))' }}
                        iconType="line"
                      />
                      <Area 
                        type="monotone" 
                        dataKey="power" 
                        stroke="hsl(var(--success))" 
                        fill="url(#colorPower)"
                        strokeWidth={2}
                        name="Power Usage"
                      />
                      <Line 
                        type="monotone" 
                        dataKey="capacity" 
                        stroke="hsl(var(--muted-foreground))" 
                        strokeWidth={1.5}
                        strokeDasharray="5 5"
                        dot={false}
                        name="Rated Power"
                      />
                      <Line 
                        type="monotone" 
                        dataKey="shed" 
                        stroke="hsl(var(--primary))" 
                        strokeWidth={1.5}
                        strokeDasharray="3 3"
                        dot={false}
                        name="Shed Capability"
                      />
                    </AreaChart>
                  </ResponsiveContainer>
                )}
                {!isLoading && !isError && chartData.length === 0 && (
                  <div className="p-8 text-center text-muted-foreground">
                    No historical data available for this circuit
                  </div>
                )}
              </CardContent>
            </Card>
          </div>
      </DialogContent>
    </Dialog>
  );
};
