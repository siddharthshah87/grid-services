import { useParams, useNavigate } from "react-router-dom";
import Layout from "@/components/Layout";
import Breadcrumbs from "@/components/Breadcrumbs";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { useVenDetail, useVenCircuitHistory, useVenEventHistory } from "@/hooks/useApi";
import { Loader2, ArrowLeft, Zap, MapPin, Gauge, Clock } from "lucide-react";
import { LineChart, Line, BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer } from "recharts";
import { format } from "date-fns";
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table";

export default function VenDetailPage() {
  const { venId } = useParams<{ venId: string }>();
  const navigate = useNavigate();
  const { data: ven, isLoading } = useVenDetail(venId || null);
  const { data: circuitHistory } = useVenCircuitHistory(venId || null, { limit: 100 });
  const { data: eventHistory } = useVenEventHistory(venId || null);

  if (isLoading) {
    return (
      <Layout>
        <div className="flex justify-center py-12">
          <Loader2 className="h-8 w-8 animate-spin text-muted-foreground" />
        </div>
      </Layout>
    );
  }

  if (!ven) {
    return (
      <Layout>
        <div className="text-center py-12">
          <p className="text-muted-foreground">VEN not found</p>
          <Button onClick={() => navigate("/vens")} className="mt-4">
            <ArrowLeft className="mr-2 h-4 w-4" />
            Back to VENs
          </Button>
        </div>
      </Layout>
    );
  }

  const getStatusVariant = (status: string) => {
    switch (status) {
      case "online": return "default";
      case "offline": return "secondary";
      case "curtailing": return "destructive";
      default: return "outline";
    }
  };

  // Prepare power history chart data
  const powerChartData = circuitHistory?.snapshots?.map(ch => {
    try {
      return {
        time: format(new Date(ch.timestamp), 'HH:mm:ss'),
        power: ch.currentPowerKw || 0,
        capacity: ch.shedCapabilityKw || 0,
      };
    } catch (error) {
      return null;
    }
  }).filter(Boolean) || [];

  // Prepare load breakdown chart data
  const loadBreakdown = ven?.loads?.map(load => ({
    name: load.name || load.type || 'Unknown',
    current: load.currentPowerKw || 0,
    capacity: load.capacityKw || 0,
    shedCapability: load.shedCapabilityKw || 0,
  })) || [];

  return (
    <Layout>
      <Breadcrumbs
        items={[
          { label: "Dashboard", path: "/dashboard" },
          { label: "VENs", path: "/vens" },
          { label: ven.name || ven.id },
        ]}
      />

      <div className="flex items-center justify-between mb-6">
        <div>
          <h1 className="text-3xl font-bold">{ven.name}</h1>
          <p className="text-muted-foreground font-mono text-sm">{ven.id}</p>
        </div>
        <Button variant="outline" onClick={() => navigate("/vens")}>
          <ArrowLeft className="mr-2 h-4 w-4" />
          Back to VENs
        </Button>
      </div>

      {/* Overview Cards */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-4 mb-6">
        <Card>
          <CardHeader className="pb-2">
            <CardTitle className="text-sm font-medium text-muted-foreground">Status</CardTitle>
          </CardHeader>
          <CardContent>
            <Badge variant={getStatusVariant(ven.status)}>{ven.status}</Badge>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="pb-2">
            <CardTitle className="text-sm font-medium text-muted-foreground flex items-center gap-2">
              <Gauge className="h-4 w-4" />
              Current Power
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">
              {(ven.metrics?.currentPowerKw || 0).toFixed(2)} kW
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="pb-2">
            <CardTitle className="text-sm font-medium text-muted-foreground flex items-center gap-2">
              <Zap className="h-4 w-4" />
              Shed Capability
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">
              {(ven.metrics?.shedAvailabilityKw || 0).toFixed(2)} kW
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="pb-2">
            <CardTitle className="text-sm font-medium text-muted-foreground flex items-center gap-2">
              <MapPin className="h-4 w-4" />
              Location
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="text-sm">
              {ven.location?.lat && ven.location?.lon
                ? `${ven.location.lat.toFixed(4)}, ${ven.location.lon.toFixed(4)}`
                : "N/A"}
            </div>
          </CardContent>
        </Card>
      </div>

      {/* Tabs */}
      <Tabs defaultValue="loads" className="space-y-4">
        <TabsList>
          <TabsTrigger value="loads">Loads & Circuits</TabsTrigger>
          <TabsTrigger value="power">Power History</TabsTrigger>
          <TabsTrigger value="events">Event History</TabsTrigger>
        </TabsList>

        <TabsContent value="loads" className="space-y-4">
          <Card>
            <CardHeader>
              <CardTitle>Load Distribution</CardTitle>
            </CardHeader>
            <CardContent>
              <ResponsiveContainer width="100%" height={300}>
                <BarChart data={loadBreakdown}>
                  <CartesianGrid strokeDasharray="3 3" />
                  <XAxis dataKey="name" />
                  <YAxis label={{ value: 'Power (kW)', angle: -90, position: 'insideLeft' }} />
                  <Tooltip />
                  <Legend />
                  <Bar dataKey="current" fill="#8884d8" name="Current Power" />
                  <Bar dataKey="capacity" fill="#82ca9d" name="Capacity" />
                  <Bar dataKey="shedCapability" fill="#ffc658" name="Shed Capability" />
                </BarChart>
              </ResponsiveContainer>
            </CardContent>
          </Card>

          <Card>
            <CardHeader>
              <CardTitle>Circuit Details</CardTitle>
            </CardHeader>
            <CardContent>
              <Table>
                <TableHeader>
                  <TableRow>
                    <TableHead>Load ID</TableHead>
                    <TableHead>Name</TableHead>
                    <TableHead>Type</TableHead>
                    <TableHead>Status</TableHead>
                    <TableHead className="text-right">Current Power</TableHead>
                    <TableHead className="text-right">Capacity</TableHead>
                    <TableHead className="text-right">Shed Capability</TableHead>
                  </TableRow>
                </TableHeader>
                <TableBody>
                  {ven.loads?.map((load) => (
                    <TableRow key={load.id}>
                      <TableCell className="font-mono text-sm">{load.id}</TableCell>
                      <TableCell>{load.name || "N/A"}</TableCell>
                      <TableCell>
                        <Badge variant="outline">{load.type || "Unknown"}</Badge>
                      </TableCell>
                      <TableCell>
                        <Badge variant="default">
                          Active
                        </Badge>
                      </TableCell>
                      <TableCell className="text-right font-mono">
                        {(load.currentPowerKw || 0).toFixed(2)} kW
                      </TableCell>
                      <TableCell className="text-right font-mono">
                        {(load.capacityKw || 0).toFixed(2)} kW
                      </TableCell>
                      <TableCell className="text-right font-mono">
                        {(load.shedCapabilityKw || 0).toFixed(2)} kW
                      </TableCell>
                    </TableRow>
                  ))}
                </TableBody>
              </Table>
            </CardContent>
          </Card>
        </TabsContent>

        <TabsContent value="power">
          <Card>
            <CardHeader>
              <CardTitle>Power Usage Over Time</CardTitle>
            </CardHeader>
            <CardContent>
              <ResponsiveContainer width="100%" height={400}>
                <LineChart data={powerChartData}>
                  <CartesianGrid strokeDasharray="3 3" />
                  <XAxis dataKey="time" />
                  <YAxis label={{ value: 'Power (kW)', angle: -90, position: 'insideLeft' }} />
                  <Tooltip />
                  <Legend />
                  <Line type="monotone" dataKey="power" stroke="#8884d8" name="Current Power" />
                  <Line type="monotone" dataKey="capacity" stroke="#82ca9d" name="Shed Capability" />
                </LineChart>
              </ResponsiveContainer>
            </CardContent>
          </Card>
        </TabsContent>

        <TabsContent value="events">
          <Card>
            <CardHeader>
              <CardTitle>Event Participation History</CardTitle>
            </CardHeader>
            <CardContent>
              <Table>
                <TableHeader>
                  <TableRow>
                    <TableHead>Event ID</TableHead>
                    <TableHead>Timestamp</TableHead>
                    <TableHead>Status</TableHead>
                    <TableHead className="text-right">Circuits Curtailed</TableHead>
                  </TableRow>
                </TableHeader>
                <TableBody>
                  {eventHistory?.map((evt) => (
                    <TableRow
                      key={`${evt.eventId}-${evt.timestamp}`}
                      className="cursor-pointer hover:bg-muted/50"
                      onClick={() => navigate(`/events/${evt.eventId}`)}
                    >
                      <TableCell className="font-mono text-sm">{evt.eventId}</TableCell>
                      <TableCell>
                        <div className="flex items-center gap-2">
                          <Clock className="h-3 w-3 text-muted-foreground" />
                          {evt.timestamp ? format(new Date(evt.timestamp), 'PPpp') : 'N/A'}
                        </div>
                      </TableCell>
                      <TableCell>
                        <Badge variant={evt.status === 'accepted' ? 'default' : 'secondary'}>
                          {evt.status}
                        </Badge>
                      </TableCell>
                      <TableCell className="text-right">
                        <Badge variant="outline">{evt.circuits?.length || 0}</Badge>
                      </TableCell>
                    </TableRow>
                  ))}
                </TableBody>
              </Table>
            </CardContent>
          </Card>
        </TabsContent>
      </Tabs>
    </Layout>
  );
}
