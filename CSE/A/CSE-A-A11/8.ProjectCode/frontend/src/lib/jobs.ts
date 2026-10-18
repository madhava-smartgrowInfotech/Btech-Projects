import { useCallback, useEffect, useRef, useState } from "react";

import { api, errorMessage } from "@/lib/api";
import type { Job } from "@/lib/types";

/**
 * Starts a background job on the API (`start` returns its id) and polls it, exposing the agents' progress
 * messages while it runs. Resolves with the finished job; rejects with a readable message on failure.
 */
export function useJob<T = Record<string, unknown>>() {
  const [messages, setMessages] = useState<string[]>([]);
  const [running, setRunning] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const alive = useRef(true);

  useEffect(() => {
    alive.current = true;
    return () => {
      alive.current = false;
    };
  }, []);

  const run = useCallback(async (start: () => Promise<string>): Promise<Job<T> | null> => {
    setError(null);
    setMessages([]);
    setRunning(true);
    try {
      const id = await start();
      for (;;) {
        const job = (await api.get<Job<T>>(`/jobs/${id}`)).data;
        if (!alive.current) return null;
        setMessages(job.messages);
        if (job.status === "done") return job;
        if (job.status === "error") throw new Error(job.error ?? "The job failed.");
        await new Promise((r) => setTimeout(r, 350));
      }
    } catch (e) {
      if (alive.current) setError(errorMessage(e));
      return null;
    } finally {
      if (alive.current) setRunning(false);
    }
  }, []);

  return { run, running, messages, error, clearError: () => setError(null) };
}
