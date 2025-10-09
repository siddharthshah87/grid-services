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
