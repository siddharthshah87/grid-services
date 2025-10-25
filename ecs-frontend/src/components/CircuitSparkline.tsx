import { LineChart, Line, ResponsiveContainer } from 'recharts';
import { useVenCircuitHistory } from '@/hooks/useApi';

interface CircuitSparklineProps {
  venId: string;
  loadId: string;
  currentPowerKw: number;
}

export const CircuitSparkline = ({ venId, loadId, currentPowerKw }: CircuitSparklineProps) => {
  const { data: history } = useVenCircuitHistory(venId, { loadId, limit: 20 });

  const chartData = history?.snapshots?.map(snap => ({
    value: snap.currentPowerKw || 0,
  })) || [];

  // If no data yet, show current value as single point
  if (chartData.length === 0) {
    chartData.push({ value: currentPowerKw });
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
