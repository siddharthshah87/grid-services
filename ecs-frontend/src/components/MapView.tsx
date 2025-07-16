import { Card, CardContent } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { MapPin, Zap, Activity } from 'lucide-react';

export const MapView = () => {
  // Mock VEN locations for the map view
  const venLocations = [
    { id: 'VEN-001', name: 'Residential Block A', x: 25, y: 30, status: 'online', power: 67.2 },
    { id: 'VEN-002', name: 'Commercial Plaza', x: 60, y: 45, status: 'online', power: 98.5 },
    { id: 'VEN-003', name: 'Industrial Complex', x: 75, y: 70, status: 'maintenance', power: 0 },
    { id: 'VEN-004', name: 'Residential Block B', x: 40, y: 80, status: 'online', power: 45.1 },
    { id: 'VEN-005', name: 'Shopping Center', x: 80, y: 25, status: 'offline', power: 0 },
  ];

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'online': return 'bg-online';
      case 'offline': return 'bg-offline';
      case 'maintenance': return 'bg-warning';
      default: return 'bg-muted';
    }
  };

  return (
    <div className="p-4">
      <div className="relative bg-gradient-to-br from-muted/30 to-muted/10 rounded-lg border-2 border-dashed border-border/50 h-[450px] overflow-hidden">
        {/* Grid Background */}
        <div 
          className="absolute inset-0 opacity-20"
          style={{
            backgroundImage: `
              linear-gradient(hsl(var(--border)) 1px, transparent 1px),
              linear-gradient(90deg, hsl(var(--border)) 1px, transparent 1px)
            `,
            backgroundSize: '40px 40px'
          }}
        />
        
        {/* VEN Markers */}
        {venLocations.map((ven) => (
          <div
            key={ven.id}
            className="absolute group cursor-pointer transform -translate-x-1/2 -translate-y-1/2"
            style={{ left: `${ven.x}%`, top: `${ven.y}%` }}
          >
            {/* VEN Marker */}
            <div className={`w-4 h-4 rounded-full ${getStatusColor(ven.status)} border-2 border-background shadow-lg animate-pulse-energy`}>
              <div className="absolute inset-0 rounded-full bg-current opacity-30 animate-ping"></div>
            </div>
            
            {/* Tooltip on Hover */}
            <Card className="absolute bottom-6 left-1/2 transform -translate-x-1/2 w-64 opacity-0 group-hover:opacity-100 transition-all duration-200 z-10 shadow-energy">
              <CardContent className="p-3">
                <div className="flex items-center justify-between mb-2">
                  <h4 className="font-semibold text-sm">{ven.name}</h4>
                  <Badge 
                    variant="outline" 
                    className={`text-xs ${
                      ven.status === 'online' ? 'border-online text-online' :
                      ven.status === 'offline' ? 'border-offline text-offline' :
                      'border-warning text-warning'
                    }`}
                  >
                    {ven.status}
                  </Badge>
                </div>
                <div className="space-y-1 text-xs">
                  <div className="flex items-center gap-1">
                    <MapPin className="h-3 w-3 text-muted-foreground" />
                    <span className="text-muted-foreground">ID:</span>
                    <span className="font-medium">{ven.id}</span>
                  </div>
                  <div className="flex items-center gap-1">
                    <Activity className="h-3 w-3 text-primary" />
                    <span className="text-muted-foreground">Power:</span>
                    <span className="font-medium text-primary">{ven.power} kW</span>
                  </div>
                </div>
              </CardContent>
            </Card>
          </div>
        ))}

        {/* Power Flow Lines (decorative) */}
        <svg className="absolute inset-0 w-full h-full pointer-events-none opacity-30">
          <defs>
            <linearGradient id="powerFlow" x1="0%" y1="0%" x2="100%" y2="0%">
              <stop offset="0%" stopColor="hsl(var(--primary))" stopOpacity="0" />
              <stop offset="50%" stopColor="hsl(var(--primary))" stopOpacity="0.8" />
              <stop offset="100%" stopColor="hsl(var(--primary))" stopOpacity="0" />
            </linearGradient>
          </defs>
          
          {/* Animated power flow lines */}
          <g stroke="url(#powerFlow)" strokeWidth="2" fill="none">
            <path d="M 25% 30% Q 50% 15% 75% 25%" className="animate-data-flow">
              <animate attributeName="stroke-dasharray" values="0,100;20,80;0,100" dur="3s" repeatCount="indefinite" />
            </path>
            <path d="M 40% 80% Q 65% 60% 75% 70%" className="animate-data-flow">
              <animate attributeName="stroke-dasharray" values="0,100;20,80;0,100" dur="2.5s" repeatCount="indefinite" />
            </path>
          </g>
        </svg>

        {/* Legend */}
        <div className="absolute bottom-4 right-4 bg-card/90 backdrop-blur-sm border rounded-lg p-3">
          <h4 className="text-sm font-semibold mb-2">VEN Status</h4>
          <div className="space-y-1 text-xs">
            <div className="flex items-center gap-2">
              <div className="w-3 h-3 rounded-full bg-online"></div>
              <span>Online</span>
            </div>
            <div className="flex items-center gap-2">
              <div className="w-3 h-3 rounded-full bg-offline"></div>
              <span>Offline</span>
            </div>
            <div className="flex items-center gap-2">
              <div className="w-3 h-3 rounded-full bg-warning"></div>
              <span>Maintenance</span>
            </div>
          </div>
        </div>

        {/* Center Grid Label */}
        <div className="absolute top-1/2 left-1/2 transform -translate-x-1/2 -translate-y-1/2 text-center">
          <div className="bg-card/80 backdrop-blur-sm border rounded-lg p-4">
            <Zap className="h-8 w-8 text-primary mx-auto mb-2" />
            <div className="text-sm font-semibold">Smart Grid Network</div>
            <div className="text-xs text-muted-foreground">Regional Coverage Area</div>
          </div>
        </div>
      </div>
    </div>
  );
};