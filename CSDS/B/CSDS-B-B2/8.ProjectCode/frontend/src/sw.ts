/// <reference lib="webworker" />
/**
 * SignalScout service worker:
 *  - precaches the app so the dashboard and the phone probe open without a connection;
 *  - serves single-page routes from the cached index.html (never API calls);
 *  - keeps map tiles you have already viewed (7 days, bounded);
 *  - uploads the probe's queued readings on Background Sync, even after the page is closed.
 */
import { cleanupOutdatedCaches, createHandlerBoundToURL, precacheAndRoute } from "workbox-precaching";
import { NavigationRoute, registerRoute } from "workbox-routing";
import { CacheFirst } from "workbox-strategies";
import { ExpirationPlugin } from "workbox-expiration";
import { flushQueue } from "./lib/probe/sync-core";

declare let self: ServiceWorkerGlobalScope & { __WB_MANIFEST: Array<{ url: string; revision: string | null }> };

precacheAndRoute(self.__WB_MANIFEST);
cleanupOutdatedCaches();

registerRoute(new NavigationRoute(createHandlerBoundToURL("/index.html"), { denylist: [/^\/api\//, /^\/docs/, /^\/openapi\.json/, /^\/redoc/] }));

registerRoute(
  ({ url }) => url.hostname.endsWith("tile.openstreetmap.org"),
  new CacheFirst({ cacheName: "map-tiles", plugins: [new ExpirationPlugin({ maxEntries: 800, maxAgeSeconds: 7 * 24 * 3600 })] }),
);

self.addEventListener("sync", (event: Event) => {
  const e = event as Event & { tag: string; waitUntil(p: Promise<unknown>): void };
  if (e.tag === "probe-sync") e.waitUntil(flushQueue());
});

self.addEventListener("message", (event) => {
  if (event.data?.type === "SKIP_WAITING") void self.skipWaiting();
});

self.addEventListener("activate", (event) => event.waitUntil(self.clients.claim()));
