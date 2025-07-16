import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Progress } from '@/components/ui/progress';
import { Badge } from '@/components/ui/badge';
import { 
  Zap, 
  Home, 
  TrendingUp, 
  Battery,
  ArrowUpCircle,
  ArrowDownCircle
} from 'lucide-react';

interface NetworkStats {
  totalVens: number;
  onlineVens: number;
  totalControllablePower: number;
  currentLoadReduction: number;
  networkEfficiency: number;
  averageHousePower: number;
  totalHousePowerToday: number;
}

interface PowerMetricsProps {
  networkStats: NetworkStats;
}

export const PowerMetrics = ({ networkStats }: PowerMetricsProps) => {
  const loadReductionPercentage = (networkStats.currentLoadReduction / networkStats.totalControllablePower) * 100;
  const efficiencyColor = networkStats.networkEfficiency > 90 ? 'text-success' : 
                         networkStats.networkEfficiency > 75 ? 'text-warning' : 'text-destructive';

  return (
    <div className="space-y-4">
      {/* Power Capacity */}
      <Card>
        <CardHeader className="pb-2">
          <CardTitle className="text-sm flex items-center gap-2">
            <Battery className="h-4 w-4 text-primary" />
            Power Capacity
          </CardTitle>
          <CardDescription>
            Total controllable power available
          </CardDescription>
        </CardHeader>
        <CardContent className="space-y-3">
          <div className="flex justify-between items-end">
            <div>
              <div className="text-2xl font-bold text-primary">
                {networkStats.totalControllablePower} MW
              </div>
              <div className="text-sm text-muted-foreground">
                Maximum available
              </div>
            </div>
            <Badge variant="outline" className="border-success text-success">
              {networkStats.networkEfficiency}% efficient
            </Badge>
          </div>
          
          <div className="space-y-2">
            <div className="flex justify-between text-sm">
              <span className="text-muted-foreground">Current Reduction</span>
              <span className="font-medium">{networkStats.currentLoadReduction} MW</span>
            </div>
            <Progress value={loadReductionPercentage} className="h-2" />
            <div className="text-xs text-muted-foreground">
              {loadReductionPercentage.toFixed(1)}% of capacity in use
            </div>
          </div>
        </CardContent>
      </Card>

      {/* Residential Metrics */}
      <Card>
        <CardHeader className="pb-2">
          <CardTitle className="text-sm flex items-center gap-2">
            <Home className="h-4 w-4 text-accent" />
            Residential Metrics
          </CardTitle>
          <CardDescription>
            Average household consumption
          </CardDescription>
        </CardHeader>
        <CardContent className="space-y-3">
          <div className="grid grid-cols-2 gap-3">
            <div className="text-center p-2 bg-muted/30 rounded-lg">
              <div className="text-lg font-bold text-accent">
                {networkStats.averageHousePower} kW
              </div>
              <div className="text-xs text-muted-foreground">
                Last Hour Avg
              </div>
            </div>
            <div className="text-center p-2 bg-muted/30 rounded-lg">
              <div className="text-lg font-bold text-accent">
                {networkStats.totalHousePowerToday} kWh
              </div>
              <div className="text-xs text-muted-foreground">
                Today Total
              </div>
            </div>
          </div>
          
          <div className="flex items-center justify-between text-sm">
            <div className="flex items-center gap-1">
              <TrendingUp className="h-3 w-3 text-success" />
              <span className="text-success">5.2% efficiency gain</span>
            </div>
            <span className="text-muted-foreground">vs yesterday</span>
          </div>
        </CardContent>
      </Card>

      {/* Grid Impact */}
      <Card>
        <CardHeader className="pb-2">
          <CardTitle className="text-sm flex items-center gap-2">
            <Zap className="h-4 w-4 text-warning" />
            Grid Impact
          </CardTitle>
          <CardDescription>
            Network contribution to grid stability
          </CardDescription>
        </CardHeader>
        <CardContent className="space-y-3">
          <div className="space-y-2">
            <div className="flex items-center justify-between">
              <span className="text-sm text-muted-foreground">Peak Shaving Potential</span>
              <span className="font-medium text-warning">
                {(networkStats.totalControllablePower * 0.7).toFixed(1)} MW
              </span>
            </div>
            <div className="flex items-center justify-between">
              <span className="text-sm text-muted-foreground">Response Time</span>
              <span className="font-medium text-success">
                &lt;45ms avg
              </span>
            </div>
            <div className="flex items-center justify-between">
              <span className="text-sm text-muted-foreground">Reliability Score</span>
              <span className={`font-medium ${efficiencyColor}`}>
                {networkStats.networkEfficiency}/100
              </span>
            </div>
          </div>

          <div className="pt-2 border-t border-border">
            <div className="flex items-center gap-2 text-xs">
              <ArrowDownCircle className="h-3 w-3 text-success" />
              <span className="text-success">Reducing grid stress by 12.4%</span>
            </div>
          </div>
        </CardContent>
      </Card>
    </div>
  );
};