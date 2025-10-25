import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { apiDelete, apiGet, apiPatch, apiPost } from "@/lib/api";

// Types aligned to backend responses (selected fields)
export interface BackendNetworkStats {
  venCount: number;
  controllablePowerKw: number;
  potentialLoadReductionKw: number;
  householdUsageKw: number;
  onlineVens?: number;
  currentLoadReductionKw?: number;
  networkEfficiency?: number;
  averageHousePower?: number;
  totalHousePowerToday?: number;
}

export interface VenSummaryItem {
  id: string;
  name: string;
  location: string;
  status: "online" | "offline" | "maintenance" | string;
  controllablePower: number; // kW
  currentPower: number; // kW
  address: string;
  lastSeen: string;
  responseTime: number; // ms
}

export interface Event {
  id: string;
  status: string;
  startTime: string;
  endTime: string;
  requestedReductionKw: number;
  actualReductionKw: number;
  // Enriched optional metrics
  currentReductionKw?: number;
  vensResponding?: number;
  avgResponseMs?: number;
}

export interface VenLocation { lat: number; lon: number }
export interface VenMetrics { currentPowerKw: number; shedAvailabilityKw: number; activeEventId?: string | null; shedLoadIds?: string[] }
export interface Load {
  id: string;
  type: string;
  capacityKw: number;
  shedCapabilityKw: number;
  currentPowerKw: number;
  name?: string;
}
export interface Ven {
  id: string;
  name: string;
  status: string;
  location: VenLocation;
  metrics: VenMetrics;
  createdAt: string;
  lastSeen?: string;
  loads?: Load[];
}

export function useNetworkStats() {
  return useQuery({
    queryKey: ["networkStats"],
    queryFn: () => apiGet<BackendNetworkStats>("/api/stats/network"),
    refetchInterval: 10000,
  });
}

export function useVenSummary() {
  return useQuery({
    queryKey: ["venSummary"],
    queryFn: () => apiGet<VenSummaryItem[]>("/api/vens/summary"),
    refetchInterval: 15000,
  });
}

export function useCurrentEvent(pollActive: boolean = false) {
  return useQuery({
    queryKey: ["currentEvent"],
    queryFn: () => apiGet<Event | null>("/api/events/current"),
    refetchInterval: (data) => (pollActive && data ? 2000 : false),
  });
}

export function useCreateEvent() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (payload: { startTime: string; endTime: string; requestedReductionKw: number }) =>
      apiPost<Event>("/api/events", payload),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ["currentEvent"] });
    },
  });
}

export function useEventsHistory(params?: { start?: string; end?: string }) {
  const qp: string[] = [];
  if (params?.start) qp.push(`start=${encodeURIComponent(params.start)}`);
  if (params?.end) qp.push(`end=${encodeURIComponent(params.end)}`);
  const qs = qp.length ? `?${qp.join("&")}` : "";
  return useQuery({
    queryKey: ["eventsHistory", params?.start ?? null, params?.end ?? null],
    queryFn: () => apiGet<Event[]>(`/api/events/history${qs}`),
  });
}

export function useVens() {
  return useQuery({
    queryKey: ["vens"],
    queryFn: () => apiGet<Ven[]>("/api/vens"),
    refetchInterval: 15000,
  });
}

export function useStopEvent() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (eventId: string) => apiPost(`/api/events/${eventId}/stop`, {}),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ["currentEvent"] });
    },
  });
}

// VEN Details
export interface CircuitSnapshot {
  timestamp: string;
  loadId: string;
  name?: string;
  type?: string;
  capacityKw?: number;
  currentPowerKw: number;
  shedCapabilityKw: number;
  enabled: boolean;
  priority?: number;
}

export interface CircuitHistoryResponse {
  venId: string;
  loadId?: string;
  snapshots: CircuitSnapshot[];
  totalCount: number;
}

export interface VenEventAck {
  eventId: string;
  venId: string;
  timestamp: string;
  status: string;
  circuits: Array<{
    loadId: string;
    curtailedKw: number;
  }>;
}

export function useVenDetail(venId: string | null) {
  return useQuery({
    queryKey: ["ven", venId],
    queryFn: () => apiGet<Ven>(`/api/vens/${venId}`),
    enabled: !!venId,
    refetchInterval: 10000,
  });
}

export function useVenCircuitHistory(venId: string | null, params?: { loadId?: string; start?: string; end?: string; limit?: number }) {
  const qp: string[] = [];
  if (params?.loadId) qp.push(`load_id=${encodeURIComponent(params.loadId)}`);
  if (params?.start) qp.push(`start=${encodeURIComponent(params.start)}`);
  if (params?.end) qp.push(`end=${encodeURIComponent(params.end)}`);
  if (params?.limit) qp.push(`limit=${params.limit}`);
  const qs = qp.length ? `?${qp.join("&")}` : "";
  
  return useQuery({
    queryKey: ["venCircuitHistory", venId, params],
    queryFn: () => apiGet<CircuitHistoryResponse>(`/api/vens/${venId}/circuits/history${qs}`),
    enabled: !!venId,
    staleTime: 30000, // Consider data fresh for 30 seconds
    retry: 1, // Only retry once on failure
  });
}

export function useVenEventHistory(venId: string | null) {
  return useQuery({
    queryKey: ["venEventHistory", venId],
    queryFn: () => apiGet<VenEventAck[]>(`/api/vens/${venId}/events`),
    enabled: !!venId,
  });
}

// Event Details
export interface EventDetail extends Event {
  vens?: Array<{
    venId: string;
    venName: string;
    shedKw: number;
    status: string;
  }>;
}

export function useEventDetail(eventId: string | null) {
  return useQuery({
    queryKey: ["event", eventId],
    queryFn: () => apiGet<EventDetail>(`/api/events/${eventId}`),
    enabled: !!eventId,
    refetchInterval: 10000,
  });
}
