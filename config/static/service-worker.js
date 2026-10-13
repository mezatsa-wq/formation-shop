"use strict";

const CACHE_VERSION = "formashop-pwa-v1";
const STATIC_CACHE = `${CACHE_VERSION}-static`;
const IMAGE_CACHE = `${CACHE_VERSION}-images`;
const PAGE_CACHE = `${CACHE_VERSION}-pages`;

const OFFLINE_URL = "/offline/";

const STATIC_ASSETS = [
  OFFLINE_URL,
  "/static/css/style.css",
  "/static/pwa/icon-192.png",
  "/static/pwa/icon-512.png",
  "/static/pwa/icon-maskable-512.png"
];

const NEVER_CACHE = [
  "/accounts/",
  "/admin/",
  "/admin-dashboard/",
  "/cart/create-order/",
  "/orders/",
  "/checkout/",
  "/login/",
  "/logout/",
  "/register/",
  "/password-reset/",
  "/documents/"
];

function isSensitivePath(pathname) {
  return NEVER_CACHE.some((prefix) => pathname.startsWith(prefix));
}

function isPublicCatalogPath(pathname) {
  return pathname === "/" ||
    pathname === "/products/" ||
    pathname === "/courses/";
}

self.addEventListener("install", (event) => {
  event.waitUntil(
    caches.open(STATIC_CACHE)
      .then((cache) => cache.addAll(STATIC_ASSETS))
      .then(() => self.skipWaiting())
  );
});

self.addEventListener("activate", (event) => {
  event.waitUntil(
    caches.keys()
      .then((keys) => Promise.all(
        keys
          .filter((key) => key.startsWith("formashop-pwa-"))
          .filter((key) => ![
            STATIC_CACHE,
            IMAGE_CACHE,
            PAGE_CACHE
          ].includes(key))
          .map((key) => caches.delete(key))
      ))
      .then(() => self.clients.claim())
  );
});

self.addEventListener("message", (event) => {
  if (event.data && event.data.type === "SKIP_WAITING") {
    self.skipWaiting();
  }
});

self.addEventListener("fetch", (event) => {
  const request = event.request;

  if (request.method !== "GET") {
    return;
  }

  const url = new URL(request.url);

  if (url.origin !== self.location.origin) {
    return;
  }

  if (isSensitivePath(url.pathname)) {
    // Toujours laisser le serveur gérer ces routes.
    // Aucune commande ou opération financière n'est mise en cache.
    return;
  }

  if (url.pathname.startsWith("/static/")) {
    event.respondWith(
      caches.open(STATIC_CACHE).then(async (cache) => {
        const cached = await cache.match(request);

        if (cached) {
          return cached;
        }

        try {
          const response = await fetch(request);

          if (response.ok) {
            await cache.put(request, response.clone());
          }

          return response;
        } catch (error) {
          return new Response("", {
            status: 503,
            statusText: "Ressource indisponible hors ligne"
          });
        }
      })
    );
    return;
  }

  // Mise en cache des images publiques uniquement.
  if (
    request.destination === "image" &&
    !url.pathname.startsWith("/media/documents/")
  ) {
    event.respondWith(
      caches.open(IMAGE_CACHE).then(async (cache) => {
        const cached = await cache.match(request);

        if (cached) {
          return cached;
        }

        try {
          const response = await fetch(request);

          if (response.ok && response.type === "basic") {
            await cache.put(request, response.clone());
          }

          return response;
        } catch (error) {
          return new Response("", {
            status: 503,
            statusText: "Image indisponible hors ligne"
          });
        }
      })
    );
    return;
  }

  if (request.mode === "navigate") {
    event.respondWith(
      fetch(request).catch(async () => {
        // Ne jamais afficher une page privée périmée en remplacement
        // d'une page de compte, de commande ou de paiement.
        if (isSensitivePath(url.pathname)) {
          return new Response(
            "<!doctype html><html lang='fr'><meta charset='utf-8'>" +
            "<meta name='viewport' content='width=device-width,initial-scale=1'>" +
            "<title>Hors ligne — FormaShop</title>" +
            "<body style='background:#070b16;color:#fff;font:16px sans-serif;padding:2rem'>" +
            "<h1>Vous êtes hors ligne</h1>" +
            "<p>Reconnectez-vous pour accéder à votre compte ou poursuivre votre commande.</p>" +
            "<a style='color:#a99aff' href='/'>Retour à l’accueil</a>" +
            "</body></html>",
            {
              status: 503,
              headers: {
                "Content-Type": "text/html; charset=utf-8"
              }
            }
          );
        }

        const cachedOffline = await caches.match(OFFLINE_URL);

        if (cachedOffline) {
          return cachedOffline;
        }

        return new Response(
          "Vous êtes hors ligne. Reconnectez-vous puis réessayez.",
          {
            status: 503,
            headers: {
              "Content-Type": "text/plain; charset=utf-8"
            }
          }
        );
      })
    );
  }
});
