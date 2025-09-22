import { Badge } from '@/components/ui/badge';
import { Card, CardContent } from '@/components/ui/card';
import { ScrollArea } from '@/components/ui/scroll-area';
import { Button } from '@/components/ui/button';
import { Dialog, DialogContent, DialogDescription, DialogHeader, DialogTitle } from '@/components/ui/dialog';
import { apiGet } from '@/lib/api';
import { useState } from 'react';
import type { Ven } from '@/hooks/useApi';
import {
  MapPin, 
  Zap, 
  CheckCircle, 
  AlertTriangle, 
  Settings,
  Activity
} from 'lucide-react';
import { useVenSummary } from '@/hooks/useApi';

export const VenList = () => {
  const { data: vens, isLoading } = useVenSummary();
  const [open, setOpen] = useState(false);
  const [detail, setDetail] = useState<Ven | null>(null);
  const [loadingDetail, setLoadingDetail] = useState(false);

  const handleDetails = async (id: string) => {
    try {
      setLoadingDetail(true);
      const ven = await apiGet<Ven>(`/api/vens/${id}`);
      setDetail(ven);
      setOpen(true);
    } finally {
      setLoadingDetail(false);
    }
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
    <ScrollArea className="h-[500px]">
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
      <Dialog open={open} onOpenChange={setOpen}>
        <DialogContent className="max-w-xl">
          <DialogHeader>
            <DialogTitle>VEN Details</DialogTitle>
            <DialogDescription>Full information for the selected VEN</DialogDescription>
          </DialogHeader>
          {loadingDetail && <div className="text-sm text-muted-foreground">Loading…</div>}
          {detail && (
            <div className="space-y-3 text-sm">
              <div className="grid grid-cols-2 gap-2">
                <div><span className="text-muted-foreground">Name</span><div className="font-medium">{detail.name}</div></div>
                <div><span className="text-muted-foreground">ID</span><div className="font-medium">{detail.id}</div></div>
                <div><span className="text-muted-foreground">Status</span><div className="font-medium capitalize">{detail.status}</div></div>
                <div><span className="text-muted-foreground">Location</span><div className="font-medium">{detail.location.lat.toFixed(4)}, {detail.location.lon.toFixed(4)}</div></div>
              </div>
              <div className="grid grid-cols-2 gap-2">
                <div><span className="text-muted-foreground">Current Power</span><div className="font-medium">{detail.metrics.currentPowerKw.toFixed(1)} kW</div></div>
                <div><span className="text-muted-foreground">Controllable</span><div className="font-medium">{detail.metrics.shedAvailabilityKw.toFixed(1)} kW</div></div>
              </div>
              <div className="pt-2 border-t">
                <div className="font-semibold mb-2">Loads</div>
                <div className="space-y-1">
                  {(detail.loads || []).map(l => (
                    <div key={l.id} className="grid grid-cols-5 gap-2 text-xs bg-muted/20 p-2 rounded">
                      <div className="font-medium">{l.type}</div>
                      <div><span className="text-muted-foreground">Cap</span> {l.capacityKw} kW</div>
                      <div><span className="text-muted-foreground">Shed</span> {l.shedCapabilityKw} kW</div>
                      <div><span className="text-muted-foreground">Now</span> {l.currentPowerKw} kW</div>
                      <div className="truncate">{l.name || ''}</div>
                    </div>
                  ))}
                  {(detail.loads || []).length === 0 && (
                    <div className="text-muted-foreground text-xs">No loads available</div>
                  )}
                </div>
              </div>
            </div>
          )}
        </DialogContent>
      </Dialog>
    </ScrollArea>
  );
};
