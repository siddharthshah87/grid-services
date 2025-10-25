import { useNavigate } from "react-router-dom";
import { useState } from "react";
import Layout from "@/components/Layout";
import Breadcrumbs from "@/components/Breadcrumbs";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Input } from "@/components/ui/input";
import { useEventsHistory } from "@/hooks/useApi";
import { Loader2, Calendar, Clock, Search } from "lucide-react";
import { format } from "date-fns";
import { AdrControls } from "@/components/AdrControls";
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table";

export default function EventsPage() {
  const navigate = useNavigate();
  const { data: events, isLoading } = useEventsHistory();
  const [searchQuery, setSearchQuery] = useState("");

  // Sort events by startTime (most recent first)
  const sortedEvents = [...(events || [])].sort((a, b) => {
    const dateA = new Date(a.startTime).getTime();
    const dateB = new Date(b.startTime).getTime();
    return dateB - dateA; // Most recent first
  });

  // Filter events by search query (Event ID)
  const filteredEvents = sortedEvents.filter((event) => {
    if (!searchQuery) return true;
    const query = searchQuery.toLowerCase();
    return event.id.toLowerCase().includes(query);
  });

  const getStatusVariant = (status: string) => {
    switch (status) {
      case "active":
        return "default";
      case "completed":
        return "secondary";
      case "cancelled":
        return "destructive";
      default:
        return "outline";
    }
  };

  return (
    <Layout>
      <Breadcrumbs items={[{ label: "Dashboard", path: "/dashboard" }, { label: "Events" }]} />

      {/* ADR Event Control - Compact */}
      <div className="mb-6">
        <AdrControls compact />
      </div>

      {/* Events History Table */}
      <Card>
        <CardHeader>
          <div className="flex flex-col gap-4 md:flex-row md:items-center md:justify-between">
            <CardTitle className="flex items-center gap-2">
              <Calendar className="h-5 w-5" />
              Demand Response Events
            </CardTitle>
            <div className="relative w-full md:w-72">
              <Search className="absolute left-2 top-2.5 h-4 w-4 text-muted-foreground" />
              <Input
                placeholder="Search by Event ID..."
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
                className="pl-8"
              />
            </div>
          </div>
        </CardHeader>
        <CardContent>
          {isLoading ? (
            <div className="flex justify-center py-8">
              <Loader2 className="h-8 w-8 animate-spin text-muted-foreground" />
            </div>
          ) : (
            <>
              {/* Mobile Card View */}
              <div className="md:hidden space-y-3">
                {filteredEvents.length === 0 ? (
                  <div className="text-center py-8 text-muted-foreground">
                    {searchQuery ? "No events found matching your search." : "No events available."}
                  </div>
                ) : (
                  filteredEvents.map((event) => (
                    <Card 
                      key={event.id}
                      className="cursor-pointer hover:bg-muted/50 transition-colors"
                      onClick={() => navigate(`/events/${event.id}`)}
                    >
                      <CardContent className="p-4">
                        <div className="flex items-start justify-between mb-3">
                          <div className="flex-1 min-w-0">
                            <p className="text-xs text-muted-foreground font-mono truncate mb-1.5 leading-relaxed">{event.id}</p>
                            <div className="flex items-center gap-2 text-xs text-muted-foreground">
                              <Clock className="h-3 w-3" />
                              <span className="leading-relaxed">{format(new Date(event.startTime), 'MMM dd, HH:mm')}</span>
                            </div>
                          </div>
                          <Badge variant={getStatusVariant(event.status)} className="ml-2 shrink-0">
                            {event.status}
                          </Badge>
                        </div>
                        
                        <div className="grid grid-cols-2 gap-3 text-sm leading-relaxed">
                          <div>
                            <div className="text-muted-foreground mb-1 text-xs">Target</div>
                            <div className="font-mono text-sm font-medium">
                              {event.requestedReductionKw.toFixed(2)} kW
                            </div>
                          </div>
                          
                          <div>
                            <div className="text-muted-foreground mb-1 text-xs">Actual</div>
                            <div className="font-mono text-sm font-medium">
                              {event.actualReductionKw?.toFixed(2) || '0.00'} kW
                            </div>
                          </div>
                          
                          <div>
                            <div className="text-muted-foreground mb-1 text-xs">Duration</div>
                            <div className="font-medium text-sm">
                              {Math.round((new Date(event.endTime.endsWith('Z') ? event.endTime : event.endTime + 'Z').getTime() - new Date(event.startTime.endsWith('Z') ? event.startTime : event.startTime + 'Z').getTime()) / 60000)} min
                            </div>
                          </div>
                          
                          <div>
                            <div className="text-muted-foreground mb-1 text-xs">End Time</div>
                            <div className="text-sm leading-relaxed">
                              {format(new Date(event.endTime), 'MMM dd, HH:mm')}
                            </div>
                          </div>
                        </div>
                      </CardContent>
                    </Card>
                  ))
                )}
              </div>

              {/* Desktop Table View */}
              <div className="hidden md:block">
                <Table>
                  <TableHeader>
                    <TableRow>
                      <TableHead>Event ID</TableHead>
                      <TableHead>Status</TableHead>
                      <TableHead>Start Time</TableHead>
                      <TableHead>End Time</TableHead>
                      <TableHead className="text-right">Target Reduction</TableHead>
                      <TableHead className="text-right">Actual Reduction</TableHead>
                      <TableHead className="text-right">Duration</TableHead>
                    </TableRow>
                  </TableHeader>
                  <TableBody>
                    {filteredEvents.length === 0 ? (
                      <TableRow>
                        <TableCell colSpan={7} className="text-center py-8 text-muted-foreground">
                          {searchQuery ? "No events found matching your search." : "No events available."}
                        </TableCell>
                      </TableRow>
                    ) : (
                      filteredEvents.map((event) => (
                        <TableRow
                          key={event.id}
                          className="cursor-pointer hover:bg-muted/50"
                          onClick={() => navigate(`/events/${event.id}`)}
                        >
                        <TableCell className="font-mono text-sm">{event.id}</TableCell>
                        <TableCell>
                          <Badge variant={getStatusVariant(event.status)}>
                            {event.status}
                          </Badge>
                        </TableCell>
                        <TableCell>
                          <div className="flex items-center gap-1 text-sm">
                            <Clock className="h-3 w-3 text-muted-foreground" />
                            {format(new Date(event.startTime), 'PPp')}
                          </div>
                        </TableCell>
                        <TableCell>
                          <div className="flex items-center gap-1 text-sm">
                            <Clock className="h-3 w-3 text-muted-foreground" />
                            {format(new Date(event.endTime), 'PPp')}
                          </div>
                        </TableCell>
                        <TableCell className="text-right font-mono">
                          {event.requestedReductionKw.toFixed(2)} kW
                        </TableCell>
                        <TableCell className="text-right font-mono">
                          {event.actualReductionKw?.toFixed(2) || '0.00'} kW
                        </TableCell>
                        <TableCell className="text-right">
                          {Math.round((new Date(event.endTime.endsWith('Z') ? event.endTime : event.endTime + 'Z').getTime() - new Date(event.startTime.endsWith('Z') ? event.startTime : event.startTime + 'Z').getTime()) / 60000)} min
                        </TableCell>
                      </TableRow>
                      ))
                    )}
                  </TableBody>
                </Table>
              </div>
            </>
          )}
        </CardContent>
      </Card>
    </Layout>
  );
}
