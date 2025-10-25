import { useNavigate } from "react-router-dom";
import Layout from "@/components/Layout";
import Breadcrumbs from "@/components/Breadcrumbs";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { useVens } from "@/hooks/useApi";
import { Loader2, Zap, MapPin, Gauge } from "lucide-react";
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table";

export default function VensPage() {
  const navigate = useNavigate();
  const { data: vens, isLoading } = useVens();

  // Sort VENs by lastSeen timestamp (most recent first), fall back to createdAt
  const sortedVens = [...(vens || [])].sort((a, b) => {
    const dateA = new Date(a.lastSeen || a.createdAt).getTime();
    const dateB = new Date(b.lastSeen || b.createdAt).getTime();
    return dateB - dateA; // Most recent first
  });

  const getStatusVariant = (status: string) => {
    switch (status) {
      case "online":
        return "default";
      case "offline":
        return "secondary";
      case "curtailing":
        return "destructive";
      default:
        return "outline";
    }
  };

  return (
    <Layout>
      <Breadcrumbs items={[{ label: "Dashboard", path: "/dashboard" }, { label: "VENs" }]} />

      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <Zap className="h-5 w-5" />
            Virtual End Nodes (VENs)
          </CardTitle>
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
                  <TableHead>VEN ID</TableHead>
                  <TableHead>Name</TableHead>
                  <TableHead>Status</TableHead>
                  <TableHead>Location</TableHead>
                  <TableHead className="text-right">Power Usage</TableHead>
                  <TableHead className="text-right">Shed Capability</TableHead>
                  <TableHead className="text-right">Circuits</TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {sortedVens?.map((ven) => (
                  <TableRow
                    key={ven.id}
                    className="cursor-pointer hover:bg-muted/50"
                    onClick={() => navigate(`/vens/${ven.id}`)}
                  >
                    <TableCell className="font-mono text-sm">{ven.id}</TableCell>
                    <TableCell className="font-medium">{ven.name}</TableCell>
                    <TableCell>
                      <Badge variant={getStatusVariant(ven.status)}>
                        {ven.status}
                      </Badge>
                    </TableCell>
                    <TableCell>
                      <div className="flex items-center gap-1 text-sm text-muted-foreground">
                        <MapPin className="h-3 w-3" />
                        {ven.location?.lat && ven.location?.lon
                          ? `${ven.location.lat.toFixed(4)}, ${ven.location.lon.toFixed(4)}`
                          : "N/A"}
                      </div>
                    </TableCell>
                    <TableCell className="text-right">
                      <div className="flex items-center justify-end gap-1">
                        <Gauge className="h-3 w-3 text-muted-foreground" />
                        <span className="font-mono">
                          {(ven.metrics?.currentPowerKw || 0).toFixed(2)} kW
                        </span>
                      </div>
                    </TableCell>
                    <TableCell className="text-right font-mono">
                      {(ven.metrics?.shedAvailabilityKw || 0).toFixed(2)} kW
                    </TableCell>
                    <TableCell className="text-right">
                      <Badge variant="outline">{ven.loads?.length || 0}</Badge>
                    </TableCell>
                  </TableRow>
                ))}
              </TableBody>
            </Table>
          )}
        </CardContent>
      </Card>
    </Layout>
  );
}
