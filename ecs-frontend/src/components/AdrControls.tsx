import { useMemo, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { Progress } from '@/components/ui/progress';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';
import { Separator } from '@/components/ui/separator';
import { useToast } from '@/hooks/use-toast';
import { 
  Play, 
  Square, 
  AlertTriangle, 
  CheckCircle,
  Clock,
  Zap,
  Target
} from 'lucide-react';
import { useCreateEvent, useCurrentEvent, useStopEvent, useEventsHistory, Event } from '@/hooks/useApi';

interface AdrControlsProps {
  compact?: boolean;
}

export const AdrControls = ({ compact = false }: AdrControlsProps) => {
  const navigate = useNavigate();
  const { toast } = useToast();
  const [reductionTarget, setReductionTarget] = useState('5.0'); // MW
  const [eventDuration, setEventDuration] = useState('60'); // minutes
  const [priority] = useState('medium');

  const { data: currentEvent, isLoading: loadingCurrent } = useCurrentEvent(true);
  const createEvent = useCreateEvent();
  const stopEvent = useStopEvent();
  const { data: eventsHistory } = useEventsHistory();

  const openEventDetail = (eventId: string) => {
    navigate(`/events/${eventId}`);
  };

  const isEventActive = !!currentEvent && currentEvent.status !== 'completed' && currentEvent.status !== 'cancelled';
  const currentReductionMw = (currentEvent?.currentReductionKw ?? 0) / 1000;
  const targetReductionMw = (currentEvent?.requestedReductionKw ?? parseFloat(reductionTarget) * 1000) / 1000;
  const reductionPercentage = targetReductionMw > 0 ? (currentReductionMw / targetReductionMw) * 100 : 0;

  const handleStartAdrEvent = () => {
    const now = new Date();
    const end = new Date(now.getTime() + parseInt(eventDuration) * 60000);
    const requestedReductionKw = parseFloat(reductionTarget) * 1000;
    createEvent.mutate(
      { startTime: now.toISOString(), endTime: end.toISOString(), requestedReductionKw },
      {
        onSuccess: (evt) => {
          toast({
            title: "ADR Event Started",
            description: `Targeting ${(evt.requestedReductionKw / 1000).toFixed(1)} MW for ${eventDuration} minutes`,
          });
        },
        onError: (err: any) => {
          toast({ title: "Failed to start ADR Event", description: String(err?.message || err), variant: 'destructive' });
        },
      }
    );
  };

  const handleStopAdrEvent = () => {
    if (!currentEvent?.id) return;
    stopEvent.mutate(currentEvent.id, {
      onSuccess: () => {
        toast({
          title: "ADR Event Stopping",
          description: `Requested to stop event ${currentEvent.id}`,
        });
      },
      onError: (err: any) => {
        toast({ title: "Failed to stop ADR Event", description: String(err?.message || err), variant: 'destructive' });
      },
    });
  };

  // Compact horizontal layout for Events page
  if (compact) {
    return (
      <Card>
        <CardContent className="pt-6">
          <div className="flex items-center gap-4 flex-wrap">
            {/* Title and Status */}
            <div className="flex items-center gap-3">
              <div className="flex items-center gap-2">
                <Target className="h-5 w-5 text-primary" />
                <span className="font-semibold">ADR Event Control</span>
              </div>
              <Badge 
                variant="outline" 
                className={isEventActive ? 'border-warning text-warning' : 'border-success text-success'}
              >
                {isEventActive ? (
                  <>
                    <Clock className="h-3 w-3 mr-1" />
                    {currentEvent?.status || 'Active'}
                  </>
                ) : (
                  <>
                    <CheckCircle className="h-3 w-3 mr-1" />
                    Ready
                  </>
                )}
              </Badge>
            </div>

            <Separator orientation="vertical" className="h-8" />

            {/* Controls */}
            {!isEventActive ? (
              <>
                <div className="flex items-center gap-2">
                  <Label htmlFor="compact-reduction-target" className="text-sm whitespace-nowrap">
                    Target (MW):
                  </Label>
                  <Input
                    id="compact-reduction-target"
                    type="number"
                    value={reductionTarget}
                    onChange={(e) => setReductionTarget(e.target.value)}
                    className="h-9 w-24"
                    min="0"
                    max="15.8"
                    step="0.1"
                  />
                </div>
                
                <div className="flex items-center gap-2">
                  <Label htmlFor="compact-duration" className="text-sm whitespace-nowrap">
                    Duration:
                  </Label>
                  <Select value={eventDuration} onValueChange={setEventDuration}>
                    <SelectTrigger className="h-9 w-32">
                      <SelectValue />
                    </SelectTrigger>
                    <SelectContent>
                      <SelectItem value="15">15 min</SelectItem>
                      <SelectItem value="30">30 min</SelectItem>
                      <SelectItem value="60">1 hour</SelectItem>
                      <SelectItem value="120">2 hours</SelectItem>
                      <SelectItem value="240">4 hours</SelectItem>
                    </SelectContent>
                  </Select>
                </div>

                <Button 
                  onClick={handleStartAdrEvent}
                  className="h-9 bg-gradient-primary"
                  disabled={!reductionTarget || parseFloat(reductionTarget) <= 0 || createEvent.isPending}
                >
                  <Play className="h-4 w-4 mr-2" />
                  {createEvent.isPending ? 'Starting…' : 'Start Event'}
                </Button>
              </>
            ) : (
              <>
                <div className="flex items-center gap-4 text-sm">
                  <div>
                    <span className="text-muted-foreground">Progress: </span>
                    <span className="font-medium">
                      {currentReductionMw.toFixed(1)} / {targetReductionMw.toFixed(1)} MW
                    </span>
                    <span className="text-muted-foreground ml-2">
                      ({reductionPercentage.toFixed(1)}%)
                    </span>
                  </div>
                  <div>
                    <span className="text-muted-foreground">VENs: </span>
                    <span className="font-medium text-success">{currentEvent?.vensResponding ?? 0}</span>
                  </div>
                </div>

                <Button 
                  onClick={handleStopAdrEvent}
                  variant="destructive"
                  className="h-9"
                  disabled={stopEvent.isPending}
                >
                  <Square className="h-4 w-4 mr-2" />
                  {stopEvent.isPending ? 'Stopping…' : 'Stop Event'}
                </Button>
              </>
            )}
          </div>
        </CardContent>
      </Card>
    );
  }

  // Original full layout for Dashboard
  return (
    <Card>
      <CardHeader>
        <CardTitle className="text-sm flex items-center gap-2">
          <Target className="h-4 w-4 text-primary" />
          ADR Event Control
        </CardTitle>
        <CardDescription>
          Manage automated demand response events
        </CardDescription>
      </CardHeader>
      <CardContent className="space-y-4">
        {/* Event Status */}
        <div className="flex items-center justify-between">
          <span className="text-sm text-muted-foreground">Event Status</span>
          <Badge 
            variant="outline" 
            className={isEventActive ? 'border-warning text-warning' : 'border-success text-success'}
          >
            {isEventActive ? (
              <>
                <Clock className="h-3 w-3 mr-1" />
                {currentEvent?.status || 'Active'}
              </>
            ) : (
              <>
                <CheckCircle className="h-3 w-3 mr-1" />
                Ready
              </>
            )}
          </Badge>
        </div>

        {/* Event Configuration */}
        {!isEventActive && (
          <div className="space-y-3">
            <div className="space-y-2">
              <Label htmlFor="reduction-target" className="text-xs">
                Reduction Target (MW)
              </Label>
              <Input
                id="reduction-target"
                type="number"
                value={reductionTarget}
                onChange={(e) => setReductionTarget(e.target.value)}
                className="h-8"
                min="0"
                max="15.8"
                step="0.1"
              />
            </div>
            
            <div className="space-y-2">
              <Label htmlFor="duration" className="text-xs">
                Duration (minutes)
              </Label>
              <Select value={eventDuration} onValueChange={setEventDuration}>
                <SelectTrigger className="h-8">
                  <SelectValue />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="15">15 minutes</SelectItem>
                  <SelectItem value="30">30 minutes</SelectItem>
                  <SelectItem value="60">1 hour</SelectItem>
                  <SelectItem value="120">2 hours</SelectItem>
                  <SelectItem value="240">4 hours</SelectItem>
                </SelectContent>
              </Select>
            </div>
          </div>
        )}

        {/* Active Event Progress */}
        {isEventActive && (
          <div className="space-y-3">
            <div className="space-y-2">
              <div className="flex justify-between text-sm">
                <span className="text-muted-foreground">Load Reduction Progress</span>
                <span className="font-medium">
                  {currentReductionMw.toFixed(1)} / {targetReductionMw.toFixed(1)} MW
                </span>
              </div>
              <Progress value={reductionPercentage} className="h-2" />
              <div className="text-xs text-muted-foreground">
                {reductionPercentage.toFixed(1)}% of target achieved
              </div>
            </div>

            <div className="grid grid-cols-2 gap-2 text-xs">
              <div className="bg-muted/30 p-2 rounded text-center">
                <div className="font-medium text-success">{currentEvent?.vensResponding ?? 0}</div>
                <div className="text-muted-foreground">VENs Responding</div>
              </div>
              <div className="bg-muted/30 p-2 rounded text-center">
                <div className="font-medium text-primary">{currentEvent?.avgResponseMs ?? 0}ms</div>
                <div className="text-muted-foreground">Avg Response</div>
              </div>
            </div>
          </div>
        )}

        <Separator />

        {/* Control Buttons */}
        <div className="space-y-2">
          {!isEventActive ? (
            <Button 
              onClick={handleStartAdrEvent}
              className="w-full h-9 bg-gradient-primary"
              disabled={!reductionTarget || parseFloat(reductionTarget) <= 0 || createEvent.isPending}
            >
              <Play className="h-4 w-4 mr-2" />
              {createEvent.isPending ? 'Starting…' : 'Start ADR Event'}
            </Button>
          ) : (
            <Button 
              onClick={handleStopAdrEvent}
              variant="destructive"
              className="w-full h-9"
              disabled={stopEvent.isPending}
            >
              <Square className="h-4 w-4 mr-2" />
              {stopEvent.isPending ? 'Stopping…' : 'Stop Event'}
            </Button>
          )}
          
          <Button variant="outline" size="sm" className="w-full h-8 text-xs opacity-50 cursor-not-allowed" disabled>
            Schedule Event (coming soon)
          </Button>
        </div>

        {/* Recent Events */}
        <div className="space-y-2">
          <Label className="text-xs text-muted-foreground">Recent Events</Label>
          <div className="space-y-1">
            {(eventsHistory || []).slice(0, 5).map((evt) => {
              const isCompleted = evt.status === 'completed';
              const isOngoing = evt.status === 'active';
              const icon = isCompleted ? <CheckCircle className="h-3 w-3 text-success" /> : <Zap className="h-3 w-3 text-warning" />;
              const start = new Date(evt.startTime);
              return (
                <button
                  key={evt.id}
                  className="w-full text-left flex justify-between items-center text-xs bg-muted/20 hover:bg-muted/30 p-2 rounded transition-colors cursor-pointer"
                  onClick={() => openEventDetail(evt.id)}
                >
                  <span className="flex items-center gap-1">
                    {icon}
                    <span className="text-muted-foreground">{start.toLocaleString()}</span>
                  </span>
                  <span className={isCompleted ? 'text-success' : 'text-warning'}>
                    {(evt.requestedReductionKw / 1000).toFixed(1)} MW
                  </span>
                </button>
              );
            })}
            {(!eventsHistory || eventsHistory.length === 0) && (
              <div className="text-xs text-muted-foreground bg-muted/20 p-2 rounded">No recent events</div>
            )}
          </div>
        </div>
      </CardContent>
    </Card>
  );
};
