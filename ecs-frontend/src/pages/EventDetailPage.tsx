import { useParams, useNavigate } from "react-router-dom";
import Layout from "@/components/Layout";
import Breadcrumbs from "@/components/Breadcrumbs";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { useEventDetail } from "@/hooks/useApi";
import { Loader2, ArrowLeft, Calendar, Clock, Zap } from "lucide-react";
import { format } from "date-fns";
import { BarChart, Bar, PieChart, Pie, Cell, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer } from "recharts";
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table";

const COLORS = ['#0088FE', '#00C49F', '#FFBB28', '#FF8042', '#8884D8'];

export default function EventDetailPage() {
  const { eventId } = useParams<{ eventId: string }>();
  const navigate = useNavigate();
  const { data: event, isLoading } = useEventDetail(eventId || null);

  if (isLoading) {
    return (
      <Layout>
        <div className="flex justify-center py-12">
          <Loader2 className="h-8 w-8 animate-spin text-muted-foreground" />
        </div>
      </Layout>
    );
  }

  if (!event) {
    return (
      <Layout>
        <div className="text-center py-12">
          <p className="text-muted-foreground">Event not found</p>
          <Button onClick={() => navigate("/events")} className="mt-4">
            <ArrowLeft className="mr-2 h-4 w-4" />
            Back to Events
          </Button>
        </div>
      </Layout>
    );
  }

  const getStatusVariant = (status: string) => {
    switch (status) {
      case "active": return "default";
      case "completed": return "secondary";
      case "cancelled": return "destructive";
      default: return "outline";
    }
  };

  // Calculate metrics
  const totalShed = event.vens?.reduce((sum, ven) => sum + (ven.shedKw || 0), 0) || 0;
  const participatingVens = event.vens?.length || 0;
  const duration = Math.round((new Date(event.endTime).getTime() - new Date(event.startTime).getTime()) / 60000);

  // Prepare chart data
  const shedByVen = event.vens?.map(ven => ({
    name: ven.venName || ven.venId,
    shedKw: ven.shedKw || 0,
  })) || [];

  const statusBreakdown = event.vens?.reduce((acc, ven) => {
    const status = ven.status || 'unknown';
    acc[status] = (acc[status] || 0) + 1;
    return acc;
  }, {} as Record<string, number>) || {};

  const statusPieData = Object.entries(statusBreakdown).map(([name, value]) => ({
    name,
    value,
  }));

  return (
    <Layout>
      <Breadcrumbs
        items={[
          { label: "Dashboard", path: "/dashboard" },
          { label: "Events", path: "/events" },
          { label: event.id },
        ]}
      />

      <div className="flex items-center justify-between mb-6">
        <div>
          <h1 className="text-3xl font-bold">Event Details</h1>
          <p className="text-muted-foreground font-mono text-sm">{event.id}</p>
        </div>
        <Button variant="outline" onClick={() => navigate("/events")}>
          <ArrowLeft className="mr-2 h-4 w-4" />
          Back to Events
        </Button>
      </div>

      {/* Overview Cards */}
      <div className="grid grid-cols-1 md:grid-cols-5 gap-4 mb-6">
        <Card>
          <CardHeader className="pb-2">
            <CardTitle className="text-sm font-medium text-muted-foreground">Status</CardTitle>
          </CardHeader>
          <CardContent>
            <Badge variant={getStatusVariant(event.status)}>{event.status}</Badge>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="pb-2">
            <CardTitle className="text-sm font-medium text-muted-foreground flex items-center gap-2">
              <Zap className="h-4 w-4" />
              Target Reduction
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">
              {event.requestedReductionKw.toFixed(2)} kW
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="pb-2">
            <CardTitle className="text-sm font-medium text-muted-foreground flex items-center gap-2">
              <Zap className="h-4 w-4" />
              Actual Shed
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">
              {totalShed.toFixed(2)} kW
            </div>
            <div className="text-xs text-muted-foreground">
              {((totalShed / event.requestedReductionKw) * 100).toFixed(1)}% of target
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="pb-2">
            <CardTitle className="text-sm font-medium text-muted-foreground flex items-center gap-2">
              <Clock className="h-4 w-4" />
              Duration
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">
              {duration} min
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="pb-2">
            <CardTitle className="text-sm font-medium text-muted-foreground">Participating VENs</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">
              {participatingVens}
            </div>
          </CardContent>
        </Card>
      </div>

      {/* Timeline */}
      <Card className="mb-6">
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <Calendar className="h-5 w-5" />
            Event Timeline
          </CardTitle>
        </CardHeader>
        <CardContent>
          <div className="space-y-2">
            <div className="flex items-center gap-3">
              <Clock className="h-4 w-4 text-muted-foreground" />
              <div>
                <div className="font-medium">Start Time</div>
                <div className="text-sm text-muted-foreground">{format(new Date(event.startTime), 'PPpp')}</div>
              </div>
            </div>
            <div className="flex items-center gap-3">
              <Clock className="h-4 w-4 text-muted-foreground" />
              <div>
                <div className="font-medium">End Time</div>
                <div className="text-sm text-muted-foreground">{format(new Date(event.endTime), 'PPpp')}</div>
              </div>
            </div>
          </div>
        </CardContent>
      </Card>

      {/* Charts */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-6 mb-6">
        <Card>
          <CardHeader>
            <CardTitle>Shed Power by VEN</CardTitle>
          </CardHeader>
          <CardContent>
            <ResponsiveContainer width="100%" height={300}>
              <BarChart data={shedByVen}>
                <CartesianGrid strokeDasharray="3 3" />
                <XAxis dataKey="name" />
                <YAxis label={{ value: 'Shed Power (kW)', angle: -90, position: 'insideLeft' }} />
                <Tooltip
                  contentStyle={{ 
                    backgroundColor: 'hsl(var(--popover))', 
                    border: '1px solid hsl(var(--border))',
                    borderRadius: '0.5rem',
                    backdropFilter: 'blur(8px)'
                  }}
                  labelStyle={{ color: 'hsl(var(--popover-foreground))', fontWeight: 600 }}
                  cursor={{ fill: 'hsl(var(--muted) / 0.2)' }}
                />
                <Legend 
                  wrapperStyle={{ color: 'hsl(var(--foreground))' }}
                  iconType="rect"
                />
                <Bar dataKey="shedKw" fill="#8884d8" name="Shed Power (kW)" activeBar={{ opacity: 0.8 }} />
              </BarChart>
            </ResponsiveContainer>
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle>VEN Status Distribution</CardTitle>
          </CardHeader>
          <CardContent>
            <ResponsiveContainer width="100%" height={300}>
              <PieChart>
                <Pie
                  data={statusPieData}
                  cx="50%"
                  cy="50%"
                  labelLine={false}
                  label={(entry) => `${entry.name}: ${entry.value}`}
                  outerRadius={80}
                  fill="#8884d8"
                  dataKey="value"
                >
                  {statusPieData.map((_, index) => (
                    <Cell key={`cell-${index}`} fill={COLORS[index % COLORS.length]} />
                  ))}
                </Pie>
                <Tooltip
                  contentStyle={{ 
                    backgroundColor: 'hsl(var(--popover))', 
                    border: '1px solid hsl(var(--border))',
                    borderRadius: '0.5rem',
                    backdropFilter: 'blur(8px)'
                  }}
                  labelStyle={{ color: 'hsl(var(--popover-foreground))', fontWeight: 600 }}
                  itemStyle={{ color: 'hsl(var(--popover-foreground))' }}
                />
              </PieChart>
            </ResponsiveContainer>
          </CardContent>
        </Card>
      </div>

      {/* VEN Participation Table */}
      <Card>
        <CardHeader>
          <CardTitle>VEN Participation Details</CardTitle>
        </CardHeader>
        <CardContent>
          <Table>
            <TableHeader>
              <TableRow>
                <TableHead>VEN ID</TableHead>
                <TableHead>VEN Name</TableHead>
                <TableHead>Status</TableHead>
                <TableHead className="text-right">Shed Power</TableHead>
                <TableHead className="text-right">% of Target</TableHead>
              </TableRow>
            </TableHeader>
            <TableBody>
              {event.vens?.map((ven) => (
                <TableRow
                  key={ven.venId}
                  className="cursor-pointer hover:bg-muted/50"
                  onClick={() => navigate(`/vens/${ven.venId}`)}
                >
                  <TableCell className="font-mono text-sm">{ven.venId}</TableCell>
                  <TableCell>{ven.venName || "N/A"}</TableCell>
                  <TableCell>
                    <Badge variant={ven.status === 'accepted' ? 'default' : 'secondary'}>
                      {ven.status}
                    </Badge>
                  </TableCell>
                  <TableCell className="text-right font-mono">
                      {(ven.shedKw || 0).toFixed(2)} kW
                    </TableCell>
                    <TableCell className="text-right">
                      {((ven.shedKw || 0) / event.requestedReductionKw * 100).toFixed(1)}%
                    </TableCell>
                </TableRow>
              ))}
            </TableBody>
          </Table>
        </CardContent>
      </Card>
    </Layout>
  );
}
