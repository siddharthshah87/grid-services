import { useEffect, useState } from 'react';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import { Progress } from '@/components/ui/progress';
import { ScrollArea } from '@/components/ui/scroll-area';
import { VenList } from './VenList';
import { MapView } from './MapView';
import { PowerMetrics } from './PowerMetrics';
import { AdrControls } from './AdrControls';
import { 
  Zap, 
  Activity, 
  MapPin, 
  List, 
  Power,
  TrendingDown,
  AlertTriangle,
  CheckCircle
} from 'lucide-react';
import { useNetworkStats } from '@/hooks/useApi';
import { formatPowerKw } from '@/lib/utils';

export const Dashboard = () => {
  const [activeView, setActiveView] = useState('list');
  const [mapFocusId, setMapFocusId] = useState<string | undefined>(undefined);

  const { data: stats, isLoading } = useNetworkStats();
  const onlineCount = stats?.onlineVens ?? 0;
  const totalVens = stats?.venCount ?? 0;

  // When a component (e.g., VenList) requests focusing a VEN, switch to the map
  // and pass a focusId prop to MapView to avoid global event loops.
  useEffect(() => {
    const onFocusVen = (e: Event) => {
      const id = (e as CustomEvent<{ id: string }>).detail?.id;
      if (!id) return;
      setActiveView('map');
      setMapFocusId(id);
    };
    window.addEventListener('focus-ven', onFocusVen as EventListener);
    return () => window.removeEventListener('focus-ven', onFocusVen as EventListener);
  }, []);

  return (
    <div className="min-h-screen bg-background p-6 space-y-6">
      {/* Status Bar */}
      <div className="flex items-center justify-end gap-4">
        <div className="flex items-center gap-2">
          <div className="w-3 h-3 rounded-full bg-online animate-pulse-energy"></div>
          <span className="text-sm text-success font-medium">System Online</span>
        </div>
        <Badge variant="outline" className="border-primary text-primary">
          VTN Status: Active
        </Badge>
      </div>

      {/* Key Metrics Overview */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
        <Card className="border-primary/20 bg-gradient-to-br from-card to-card/50">
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Network Status</CardTitle>
            <Activity className="h-4 w-4 text-primary" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold text-primary">
              {isLoading ? '…' : `${onlineCount}/${totalVens}`}
            </div>
            <p className="text-xs text-muted-foreground">
              VENs Online ({stats?.networkEfficiency ?? 0}% efficiency)
            </p>
          </CardContent>
        </Card>

        <Card className="border-success/20 bg-gradient-to-br from-card to-card/50">
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Controllable Power</CardTitle>
            <Zap className="h-4 w-4 text-success" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold text-success">
              {isLoading ? '…' : formatPowerKw(stats?.controllablePowerKw)}
            </div>
            <p className="text-xs text-muted-foreground">
              Available for load shedding
            </p>
          </CardContent>
        </Card>

        <Card className="border-warning/20 bg-gradient-to-br from-card to-card/50">
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Active Reduction</CardTitle>
            <TrendingDown className="h-4 w-4 text-warning" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold text-warning">
              {isLoading ? '…' : formatPowerKw(stats?.currentLoadReductionKw)}
            </div>
            <p className="text-xs text-muted-foreground">
              Current load reduction
            </p>
          </CardContent>
        </Card>

        <Card className="border-accent/20 bg-gradient-to-br from-card to-card/50">
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Avg House Power</CardTitle>
            <Power className="h-4 w-4 text-accent" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold text-accent">
              {isLoading ? '…' : formatPowerKw(stats?.averageHousePower)}
            </div>
            <p className="text-xs text-muted-foreground">
              Last hour average
            </p>
          </CardContent>
        </Card>
      </div>

      {/* Main Content Grid */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* VEN Management */}
        <div className="lg:col-span-2">
          <Card className="h-[calc(100vh-22rem)] flex flex-col">
            <CardHeader>
              <div className="flex items-center justify-between">
                <div>
                  <CardTitle className="flex items-center gap-2">
                    <MapPin className="h-5 w-5 text-primary" />
                    VEN Management
                  </CardTitle>
                  <CardDescription>
                    Monitor and control virtual end nodes
                  </CardDescription>
                </div>
                <Tabs value={activeView} onValueChange={setActiveView}>
                  <TabsList className="grid w-32 grid-cols-2">
                    <TabsTrigger value="list" className="text-xs">
                      <List className="h-3 w-3 mr-1" />
                      List
                    </TabsTrigger>
                    <TabsTrigger value="map" className="text-xs">
                      <MapPin className="h-3 w-3 mr-1" />
                      Map
                    </TabsTrigger>
                  </TabsList>
                </Tabs>
              </div>
            </CardHeader>
            <CardContent className="p-0 flex-1 overflow-hidden">
              <ScrollArea className="h-full">
                {activeView === 'list' ? <VenList /> : <MapView focusId={mapFocusId} onFocused={() => setMapFocusId(undefined)} />}
              </ScrollArea>
            </CardContent>
          </Card>
        </div>

        {/* Sidebar Controls */}
        <div>
          <Card className="h-[calc(100vh-22rem)] flex flex-col">
            <CardContent className="p-4 flex-1 overflow-hidden">
              <ScrollArea className="h-full">
                <div className="space-y-6 pr-4">
                  <PowerMetrics networkStats={stats} />
                  <AdrControls />
                </div>
              </ScrollArea>
            </CardContent>
          </Card>
        </div>
      </div>
    </div>
  );
};
