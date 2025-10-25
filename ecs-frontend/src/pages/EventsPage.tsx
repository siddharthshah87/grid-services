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
          <div className="flex items-center justify-between">
            <CardTitle className="flex items-center gap-2">
              <Calendar className="h-5 w-5" />
              Demand Response Events
            </CardTitle>
            <div className="relative w-72">
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
            <Table>
              <TableHeader>
                <TableRow>
                  <TableHead>Event ID</TableHead>
                  <TableHead>Status</TableHead>
                  <TableHead>Start Time</TableHead>
                  <TableHead>End Time</TableHead>
                  <TableHead className="text-right">Target Reduction</TableHead>
                  <TableHead className="text-right">Duration</TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {filteredEvents.length === 0 ? (
                  <TableRow>
                    <TableCell colSpan={6} className="text-center py-8 text-muted-foreground">
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
                    <TableCell className="text-right">
                      {Math.round((new Date(event.endTime).getTime() - new Date(event.startTime).getTime()) / 60000)} min
                    </TableCell>
                  </TableRow>
                  ))
                )}
              </TableBody>
            </Table>
          )}
        </CardContent>
      </Card>
    </Layout>
  );
}
