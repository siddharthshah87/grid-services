import { useEffect, useRef } from 'react';

interface UsePollingOptions {
  enabled?: boolean;
  interval?: number; // milliseconds
  onError?: (error: Error) => void;
}

/**
 * Hook for polling data at regular intervals
 * @param callback - Function to call on each poll
 * @param options - Polling configuration
 */
export function usePolling(
  callback: () => void | Promise<void>,
  options: UsePollingOptions = {}
) {
  const { enabled = true, interval = 10000, onError } = options;
  const savedCallback = useRef(callback);
  const intervalRef = useRef<NodeJS.Timeout>();

  // Update callback ref when it changes
  useEffect(() => {
    savedCallback.current = callback;
  }, [callback]);

  useEffect(() => {
    if (!enabled) {
      if (intervalRef.current) {
        clearInterval(intervalRef.current);
      }
      return;
    }

    const tick = async () => {
      try {
        await savedCallback.current();
      } catch (error) {
        console.error('[Polling] Error:', error);
        onError?.(error as Error);
      }
    };

    // Call immediately on mount/enable
    tick();

    // Then set up interval
    intervalRef.current = setInterval(tick, interval);

    return () => {
      if (intervalRef.current) {
        clearInterval(intervalRef.current);
      }
    };
  }, [enabled, interval, onError]);
}
