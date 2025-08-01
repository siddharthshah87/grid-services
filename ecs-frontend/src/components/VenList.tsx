import { Badge } from '@/components/ui/badge';
import { Card, CardContent } from '@/components/ui/card';
import { ScrollArea } from '@/components/ui/scroll-area';
import { Button } from '@/components/ui/button';
import { 
  MapPin, 
  Zap, 
  CheckCircle, 
  AlertTriangle, 
  Settings,
  Activity
} from 'lucide-react';

interface VenData {
  id: string;
  name: string;
  location: string;
  status: 'online' | 'offline' | 'maintenance';
  controllablePower: number; // kW
  currentPower: number; // kW
  address: string;
  lastSeen: string;
  responseTime: number; // ms
}

export const VenList = () => {
  // Mock VEN data - in real app this would come from API
  const vens: VenData[] = [
    {
      id: 'VEN-001',
      name: 'Residential Block A',
      location: 'Downtown District',
      status: 'online',
      controllablePower: 85.4,
      currentPower: 67.2,
      address: '123 Main St, Grid Sector 1',
      lastSeen: '2 mins ago',
      responseTime: 145
    },
    {
      id: 'VEN-002', 
      name: 'Commercial Plaza',
      location: 'Business District',
      status: 'online',
      controllablePower: 120.8,
      currentPower: 98.5,
      address: '456 Commerce Ave, Grid Sector 2',
      lastSeen: '1 min ago',
      responseTime: 89
    },
    {
      id: 'VEN-003',
      name: 'Industrial Complex',
      location: 'Manufacturing Zone',
      status: 'maintenance',
      controllablePower: 245.0,
      currentPower: 0,
      address: '789 Industrial Blvd, Grid Sector 3',
      lastSeen: '15 mins ago',
      responseTime: 0
    },
    {
      id: 'VEN-004',
      name: 'Residential Block B',
      location: 'Suburban Area',
      status: 'online',
      controllablePower: 62.3,
      currentPower: 45.1,
      address: '321 Oak Street, Grid Sector 4',
      lastSeen: '30 secs ago',
      responseTime: 234
    },
    {
      id: 'VEN-005',
      name: 'Shopping Center',
      location: 'Retail District',
      status: 'offline',
      controllablePower: 95.7,
      currentPower: 0,
      address: '654 Shopping Blvd, Grid Sector 5',
      lastSeen: '25 mins ago',
      responseTime: 0
    }
  ];

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
      <Badge variant="outline" className={variants[status as keyof typeof variants]}>
        {status.charAt(0).toUpperCase() + status.slice(1)}
      </Badge>
    );
  };

  return (
    <ScrollArea className="h-[500px]">
      <div className="p-4 space-y-3">
        {vens.map((ven) => (
          <Card key={ven.id} className="transition-all duration-200 hover:shadow-energy border-l-4 border-l-primary/30">
            <CardContent className="p-4">
              <div className="flex items-center justify-between mb-3">
                <div className="flex items-center gap-3">
                  {getStatusIcon(ven.status)}
                  <div>
                    <h3 className="font-semibold text-foreground">{ven.name}</h3>
                    <p className="text-sm text-muted-foreground">{ven.id}</p>
                  </div>
                </div>
                {getStatusBadge(ven.status)}
              </div>
              
              <div className="grid grid-cols-2 gap-4 mb-3">
                <div className="space-y-1">
                  <div className="flex items-center gap-2 text-sm">
                    <Zap className="h-3 w-3 text-primary" />
                    <span className="text-muted-foreground">Controllable:</span>
                    <span className="font-medium text-primary">{ven.controllablePower} kW</span>
                  </div>
                  <div className="flex items-center gap-2 text-sm">
                    <Activity className="h-3 w-3 text-success" />
                    <span className="text-muted-foreground">Current:</span>
                    <span className="font-medium text-success">{ven.currentPower} kW</span>
                  </div>
                </div>
                <div className="space-y-1">
                  <div className="text-sm">
                    <span className="text-muted-foreground">Location:</span>
                    <div className="font-medium">{ven.location}</div>
                  </div>
                  <div className="text-sm">
                    <span className="text-muted-foreground">Last Seen:</span>
                    <div className="font-medium">{ven.lastSeen}</div>
                  </div>
                </div>
              </div>

              <div className="flex items-center justify-between text-xs text-muted-foreground mb-3">
                <div className="flex items-center gap-1">
                  <MapPin className="h-3 w-3" />
                  <span>{ven.address}</span>
                </div>
                {ven.responseTime > 0 && (
                  <span>Response: {ven.responseTime}ms</span>
                )}
              </div>

              <div className="flex gap-2">
                <Button 
                  size="sm" 
                  variant="outline"
                  className="text-xs h-7"
                  disabled={ven.status !== 'online'}
                >
                  Configure
                </Button>
                <Button 
                  size="sm" 
                  variant="outline"
                  className="text-xs h-7"
                  disabled={ven.status !== 'online'}
                >
                  Send ADR
                </Button>
                <Button 
                  size="sm" 
                  variant="outline"
                  className="text-xs h-7"
                >
                  Details
                </Button>
              </div>
            </CardContent>
          </Card>
        ))}
      </div>
    </ScrollArea>
  );
};