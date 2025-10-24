import { Badge } from '@/components/ui/badge';
import { Card, CardContent } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { useState } from 'react';
import {
  MapPin, 
  Zap, 
  CheckCircle, 
  AlertTriangle, 
  Settings,
  Activity
} from 'lucide-react';
import { useVenSummary } from '@/hooks/useApi';
import { VenDetailDialog } from './VenDetailDialog';

export const VenList = () => {
  const { data: vens, isLoading } = useVenSummary();
  const [selectedVenId, setSelectedVenId] = useState<string | null>(null);
  const [detailOpen, setDetailOpen] = useState(false);

  const handleDetails = (id: string) => {
    setSelectedVenId(id);
    setDetailOpen(true);
  };

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
    <>
      <div className="p-4 space-y-3">
        {(vens || []).map((ven) => (
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
                  onClick={() => handleDetails(ven.id)}
                >
                  Details
                </Button>
                <Button 
                  size="sm" 
                  variant="outline"
                  className="text-xs h-7"
                  onClick={() => window.dispatchEvent(new CustomEvent('focus-ven', { detail: { id: ven.id } }))}
                >
                  View on Map
                </Button>
              </div>
            </CardContent>
          </Card>
        ))}
        {isLoading && (
          <div className="p-4 text-sm text-muted-foreground">Loading VENs…</div>
        )}
      </div>
      
      <VenDetailDialog 
        venId={selectedVenId}
        open={detailOpen}
        onOpenChange={(open) => {
          setDetailOpen(open);
          if (!open) setSelectedVenId(null);
        }}
      />
    </>
  );
};
