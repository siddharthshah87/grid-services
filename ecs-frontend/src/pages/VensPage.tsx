import { useNavigate } from "react-router-dom";
import { useState } from "react";
import Layout from "@/components/Layout";
import Breadcrumbs from "@/components/Breadcrumbs";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Input } from "@/components/ui/input";
import { useVens } from "@/hooks/useApi";
import { Loader2, Zap, Clock, Gauge, Search } from "lucide-react";
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table";
import { formatDistanceToNow, format } from "date-fns";

export default function VensPage() {
  const navigate = useNavigate();
  const { data: vens, isLoading } = useVens();
  const [searchQuery, setSearchQuery] = useState("");

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

  // Filter VENs by search query (ID or Name)
  const filteredVens = sortedVens.filter((ven) => {
    if (!searchQuery) return true;
    const query = searchQuery.toLowerCase();
    return (
      ven.id.toLowerCase().includes(query) ||
      ven.name.toLowerCase().includes(query)
    );
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
          <div className="flex items-center justify-between">
            <CardTitle className="flex items-center gap-2">
              <Zap className="h-5 w-5" />
              Virtual End Nodes (VENs)
            </CardTitle>
            <div className="relative w-72">
              <Search className="absolute left-2 top-2.5 h-4 w-4 text-muted-foreground" />
              <Input
                placeholder="Search by VEN ID or Name..."
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
                  <TableHead>VEN ID</TableHead>
                  <TableHead>Name</TableHead>
                  <TableHead>Status</TableHead>
                  <TableHead>Last Seen</TableHead>
                  <TableHead className="text-right">Power Usage</TableHead>
                  <TableHead className="text-right">Shed Capability</TableHead>
                  <TableHead className="text-right">Circuits</TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {filteredVens.length === 0 ? (
                  <TableRow>
                    <TableCell colSpan={7} className="text-center py-8 text-muted-foreground">
                      {searchQuery ? "No VENs found matching your search." : "No VENs available."}
                    </TableCell>
                  </TableRow>
                ) : (
                  filteredVens.map((ven) => (
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
                        <Clock className="h-3 w-3" />
                        {formatLastSeen(ven.lastSeen)}
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
