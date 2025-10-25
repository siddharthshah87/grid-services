import { Dialog, DialogContent, DialogDescription, DialogHeader, DialogTitle, DialogFooter } from '@/components/ui/dialog';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from '@/components/ui/table';
import { format } from 'date-fns';
import { ArrowRight, Zap, TrendingDown, Activity } from 'lucide-react';
import type { VenEventAck } from '@/hooks/useApi';

interface VenEventDetailDialogProps {
  event: VenEventAck | null;
  venName: string;
  open: boolean;
  onOpenChange: (open: boolean) => void;
  onViewEvent: () => void;
}

export const VenEventDetailDialog = ({
  event,
  venName,
  open,
  onOpenChange,
  onViewEvent
}: VenEventDetailDialogProps) => {
  if (!event) return null;

  const totalShed = event.circuitsCurtailed?.reduce((sum, c) => sum + c.curtailed_kw, 0) || 0;
  const totalOriginal = event.circuitsCurtailed?.reduce((sum, c) => sum + c.original_kw, 0) || 0;
  const shedPercentage = totalOriginal > 0 ? (totalShed / totalOriginal) * 100 : 0;

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="max-w-3xl max-h-[90vh] overflow-y-auto">
        <DialogHeader>
          <DialogTitle className="flex items-center gap-2">
            <Activity className="h-5 w-5 text-primary" />
            Event Participation Detail
          </DialogTitle>
          <DialogDescription>
            {venName} • {event.timestamp ? format(new Date(event.timestamp), 'PPpp') : 'N/A'}
          </DialogDescription>
        </DialogHeader>

        <div className="space-y-6">
          {/* Event Summary */}
          <div className="grid grid-cols-2 gap-4">
            <Card>
              <CardHeader className="pb-3">
                <CardTitle className="text-sm text-muted-foreground">Event ID</CardTitle>
              </CardHeader>
              <CardContent>
                <div className="font-mono text-lg">{event.eventId}</div>
              </CardContent>
            </Card>

            <Card>
              <CardHeader className="pb-3">
                <CardTitle className="text-sm text-muted-foreground">Status</CardTitle>
              </CardHeader>
              <CardContent>
                <Badge variant={event.status === 'accepted' ? 'default' : 'secondary'} className="text-sm">
                  {event.status}
                </Badge>
              </CardContent>
            </Card>
          </div>

          {/* Shed Summary */}
          <Card>
            <CardHeader className="pb-3">
              <CardTitle className="text-sm flex items-center gap-2">
                <TrendingDown className="h-4 w-4 text-primary" />
                Load Shed Summary
              </CardTitle>
            </CardHeader>
            <CardContent>
              <div className="grid grid-cols-3 gap-4">
                <div className="text-center p-3 bg-muted/30 rounded-lg">
                  <div className="text-sm text-muted-foreground mb-1">Original Load</div>
                  <div className="text-xl font-bold">{totalOriginal.toFixed(2)} kW</div>
                </div>
                <div className="text-center p-3 bg-primary/10 rounded-lg">
                  <div className="text-sm text-muted-foreground mb-1">Total Shed</div>
                  <div className="text-xl font-bold text-primary">{totalShed.toFixed(2)} kW</div>
                </div>
                <div className="text-center p-3 bg-muted/30 rounded-lg">
                  <div className="text-sm text-muted-foreground mb-1">Reduction</div>
                  <div className="text-xl font-bold">{shedPercentage.toFixed(1)}%</div>
                </div>
              </div>
            </CardContent>
          </Card>

          {/* Per-Load Breakdown */}
          <Card>
            <CardHeader className="pb-3">
              <CardTitle className="text-sm flex items-center gap-2">
                <Zap className="h-4 w-4 text-primary" />
                Load-by-Load Curtailment
              </CardTitle>
            </CardHeader>
            <CardContent>
              {event.circuitsCurtailed && event.circuitsCurtailed.length > 0 ? (
                <Table>
                  <TableHeader>
                    <TableRow>
                      <TableHead>Load Name</TableHead>
                      <TableHead className="text-right">Original (kW)</TableHead>
                      <TableHead className="text-right">Curtailed (kW)</TableHead>
                      <TableHead className="text-right">Final (kW)</TableHead>
                      <TableHead className="text-right">Reduction %</TableHead>
                    </TableRow>
                  </TableHeader>
                  <TableBody>
                    {event.circuitsCurtailed.map((circuit, idx) => {
                      const reductionPercent = circuit.original_kw > 0 
                        ? (circuit.curtailed_kw / circuit.original_kw) * 100 
                        : 0;
                      
                      return (
                        <TableRow key={idx}>
                          <TableCell className="font-medium">
                            <div className="flex items-center gap-2">
                              {circuit.name}
                              {circuit.critical && (
                                <Badge variant="destructive" className="text-xs">Critical</Badge>
                              )}
                            </div>
                          </TableCell>
                          <TableCell className="text-right">{circuit.original_kw.toFixed(2)}</TableCell>
                          <TableCell className="text-right font-semibold text-primary">
                            {circuit.curtailed_kw.toFixed(2)}
                          </TableCell>
                          <TableCell className="text-right">{circuit.final_kw.toFixed(2)}</TableCell>
                          <TableCell className="text-right">
                            <Badge variant="outline">{reductionPercent.toFixed(1)}%</Badge>
                          </TableCell>
                        </TableRow>
                      );
                    })}
                  </TableBody>
                </Table>
              ) : (
                <div className="text-center py-8 text-muted-foreground">
                  No load curtailment data available
                </div>
              )}
            </CardContent>
          </Card>
        </div>

        <DialogFooter>
          <Button variant="outline" onClick={() => onOpenChange(false)}>
            Close
          </Button>
          <Button onClick={onViewEvent} className="gap-2">
            View Full Event Details
            <ArrowRight className="h-4 w-4" />
          </Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  );
};
