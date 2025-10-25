import { LineChart, Line, ResponsiveContainer } from 'recharts';
import { useVenCircuitHistory } from '@/hooks/useApi';
import { useMemo } from 'react';

interface CircuitSparklineProps {
  venId: string;
  loadId: string;
  currentPowerKw: number;
}

export const CircuitSparkline = ({ venId, loadId, currentPowerKw }: CircuitSparklineProps) => {
  // Get last hour of data for sparkline - memoize to prevent query key changes on every render
  const startTime = useMemo(() => new Date(Date.now() - 60 * 60 * 1000).toISOString(), []);
  
  const { data: history } = useVenCircuitHistory(venId, { loadId, start: startTime, limit: 100 });

  const chartData = history?.snapshots?.map(snap => ({
    value: snap.currentPowerKw || 0,
  })) || [];

  // If no data or insufficient data points, show a placeholder
  if (chartData.length < 2) {
    return (
      <div className="w-24 h-8 flex items-center justify-center">
        <span className="text-xs text-muted-foreground">—</span>
      </div>
    );
  }

  return (
    <div className="w-24 h-8">
      <ResponsiveContainer width="100%" height="100%">
        <LineChart data={chartData}>
          <Line 
            type="monotone" 
            dataKey="value" 
            stroke="hsl(var(--primary))" 
            strokeWidth={1.5}
            dot={false}
            isAnimationActive={false}
          />
        </LineChart>
      </ResponsiveContainer>
    </div>
  );
};
