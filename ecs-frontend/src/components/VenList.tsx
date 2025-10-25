import { Badge } from '@/components/ui/badge';
import { Card, CardContent } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { useNavigate } from 'react-router-dom';
import { Zap, Activity, ArrowRight } from 'lucide-react';
import { useVenSummary } from '@/hooks/useApi';
import { formatDistanceToNow, format } from 'date-fns';

interface VenListProps {
  limit?: number; // Optional limit on number of VENs to display
}

export const VenList = ({ limit }: VenListProps) => {
  const navigate = useNavigate();
  const { data: vens, isLoading } = useVenSummary();

  const handleDetails = (id: string) => {
    navigate(`/vens/${id}`);
  };

  const formatLastSeen = (dateString: string | undefined) => {
    if (!dateString) return "Never";
    
    try {
      const date = new Date(dateString);
      const now = new Date();
      
      // If timestamp is in the future, show the actual timestamp
      if (date > now) {
        return format(date, "yyyy/MM/dd - HH:mm:ss");
      }
      
      return formatDistanceToNow(date, { addSuffix: true });
    } catch {
      // If parsing fails, show the raw string
      return dateString;
    }
  };

  // Sort VENs by lastSeen timestamp (most recent first, push invalid/missing to bottom)
  const sortedVens = [...(vens || [])].sort((a, b) => {
    // Handle missing timestamps - push to bottom
    if (!a.lastSeen && !b.lastSeen) return 0;
    if (!a.lastSeen) return 1;
    if (!b.lastSeen) return -1;
    
    const dateA = new Date(a.lastSeen).getTime();
    const dateB = new Date(b.lastSeen).getTime();
    
    // Handle invalid dates - push to bottom
    if (isNaN(dateA) && isNaN(dateB)) return 0;
    if (isNaN(dateA)) return 1;
    if (isNaN(dateB)) return -1;
    
    return dateB - dateA; // Most recent first
  });

  // Apply limit if specified
  const displayedVens = limit ? sortedVens.slice(0, limit) : sortedVens;
  const hasMore = limit && sortedVens.length > limit;

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
      <div className="p-3 md:p-4 space-y-3">
        {(displayedVens || []).map((ven) => (
          <Card key={ven.id} className="transition-all duration-200 hover:shadow-energy border-l-4 border-l-primary/30">
            <CardContent className="p-5 md:p-4">
              <div className="flex items-center justify-between mb-3">
                <div>
                  <h3 className="font-semibold text-foreground leading-tight">{ven.name}</h3>
                  <p className="text-sm text-muted-foreground leading-relaxed">{ven.id}</p>
                </div>
                {getStatusBadge(ven.status)}
              </div>
              
              <div className="grid grid-cols-2 gap-4 mb-3">
                <div className="space-y-1">
                  <div className="flex items-center gap-2 text-sm leading-relaxed">
                    <Zap className="h-3 w-3 text-primary" />
                    <span className="text-muted-foreground">Controllable:</span>
                    <span className="font-medium text-primary">{ven.controllablePower} kW</span>
                  </div>
                  <div className="flex items-center gap-2 text-sm leading-relaxed">
                    <Activity className="h-3 w-3 text-success" />
                    <span className="text-muted-foreground">Current:</span>
                    <span className="font-medium text-success">{ven.currentPower} kW</span>
                  </div>
                </div>
                <div className="space-y-1">
                  <div className="flex flex-wrap items-center gap-x-2 text-sm leading-relaxed">
                    <span className="text-muted-foreground">Location:</span>
                    <span className="font-medium">{ven.location}</span>
                  </div>
                  <div className="flex flex-wrap items-center gap-x-2 text-sm leading-relaxed">
                    <span className="text-muted-foreground">Last Seen:</span>
                    <span className="font-medium">{formatLastSeen(ven.lastSeen)}</span>
                  </div>
                </div>
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
        {hasMore && (
          <div className="pt-2">
            <Button 
              variant="outline" 
              className="w-full h-10"
              onClick={() => navigate('/vens')}
            >
              View All {sortedVens.length} VENs
              <ArrowRight className="h-4 w-4 ml-2" />
            </Button>
          </div>
        )}
      </div>
    </>
  );
};