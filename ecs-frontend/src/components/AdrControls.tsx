import { useState } from 'react';
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

export const AdrControls = () => {
  const { toast } = useToast();
  const [isEventActive, setIsEventActive] = useState(false);
  const [reductionTarget, setReductionTarget] = useState('5.0');
  const [eventDuration, setEventDuration] = useState('60');
  const [priority] = useState('medium');
  const [currentReduction, setCurrentReduction] = useState(0);

  const handleStartAdrEvent = () => {
    setIsEventActive(true);
    setCurrentReduction(0);
    
    toast({
      title: "ADR Event Started",
      description: `Targeting ${reductionTarget} MW reduction for ${eventDuration} minutes`,
    });

    // Simulate gradual load reduction
    const interval = setInterval(() => {
      setCurrentReduction(prev => {
        const newValue = prev + 0.5;
        if (newValue >= parseFloat(reductionTarget)) {
          clearInterval(interval);
          return parseFloat(reductionTarget);
        }
        return newValue;
      });
    }, 2000);
  };

  const handleStopAdrEvent = () => {
    setIsEventActive(false);
    const finalReduction = currentReduction;
    
    toast({
      title: "ADR Event Completed",
      description: `Successfully reduced ${finalReduction.toFixed(1)} MW of load`,
    });
    
    // Reset after a delay
    setTimeout(() => {
      setCurrentReduction(0);
    }, 3000);
  };

  const reductionPercentage = (currentReduction / parseFloat(reductionTarget)) * 100;

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
                Active
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
                  {currentReduction.toFixed(1)} / {reductionTarget} MW
                </span>
              </div>
              <Progress value={reductionPercentage} className="h-2" />
              <div className="text-xs text-muted-foreground">
                {reductionPercentage.toFixed(1)}% of target achieved
              </div>
            </div>

            <div className="grid grid-cols-2 gap-2 text-xs">
              <div className="bg-muted/30 p-2 rounded text-center">
                <div className="font-medium text-success">{(currentReduction / parseFloat(reductionTarget) * 238).toFixed(0)}</div>
                <div className="text-muted-foreground">VENs Responding</div>
              </div>
              <div className="bg-muted/30 p-2 rounded text-center">
                <div className="font-medium text-primary">142ms</div>
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
              disabled={!reductionTarget || parseFloat(reductionTarget) <= 0}
            >
              <Play className="h-4 w-4 mr-2" />
              Start ADR Event
            </Button>
          ) : (
            <Button 
              onClick={handleStopAdrEvent}
              variant="destructive"
              className="w-full h-9"
            >
              <Square className="h-4 w-4 mr-2" />
              Stop Event
            </Button>
          )}
          
          <Button variant="outline" size="sm" className="w-full h-8 text-xs">
            Schedule Event
          </Button>
        </div>

        {/* Recent Events */}
        <div className="space-y-2">
          <Label className="text-xs text-muted-foreground">Recent Events</Label>
          <div className="space-y-1">
            <div className="flex justify-between items-center text-xs bg-muted/20 p-2 rounded">
              <span>Peak Shaving Event</span>
              <div className="flex items-center gap-1">
                <CheckCircle className="h-3 w-3 text-success" />
                <span className="text-success">8.2 MW</span>
              </div>
            </div>
            <div className="flex justify-between items-center text-xs bg-muted/20 p-2 rounded">
              <span>Emergency Response</span>
              <div className="flex items-center gap-1">
                <CheckCircle className="h-3 w-3 text-success" />
                <span className="text-success">12.1 MW</span>
              </div>
            </div>
          </div>
        </div>
      </CardContent>
    </Card>
  );
};