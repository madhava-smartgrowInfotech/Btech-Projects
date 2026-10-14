import { QueryClient } from "@tanstack/react-query";

/** One client for the app. Logout clears it so no record stays cached for the next user. */
export const queryClient = new QueryClient({
  defaultOptions: {
    queries: { retry: 1, refetchOnWindowFocus: false, staleTime: 15_000 },
  },
});

export const keys = {
  record: (personId: string) => ["record", personId] as const,
  risk: (personId: string) => ["risk", personId] as const,
  consents: ["consents"] as const,
  accessRequests: ["access-requests"] as const,
  reminders: ["reminders"] as const,
  hospitals: ["hospitals"] as const,
  hospitalPatients: (hospital: string, q: string) => ["hospital-patients", hospital, q] as const,
  summaries: ["summaries"] as const,
  mpiPersons: ["mpi-persons"] as const,
  audit: ["audit"] as const,
  mpiSearch: (name: string, dob: string) => ["mpi-search", name, dob] as const,
};
