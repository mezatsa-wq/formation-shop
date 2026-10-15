"use strict";

/* =========================================================
   FOR MASHOP — PWA + PUSH NOTIFICATIONS
   Cache, offline, réception push et clic sur notification.
   ========================================================= */

const CACHE_VERSION = "formashop-pwa-v2";
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
  "/cart/",
  "/cart/create-order/",
  "/orders/",
  "/checkout/",
  "/login/",
  "/logout/",
  "/register/",
  "/password-reset/",
  "/documents/",
  "/payments/",
  "/notifications/"
];

/* =========================================================
   OUTILS
   ========================================================= */

function isSensitivePath(pathname) {
  return NEVER_CACHE.some((prefix) => pathname.startsWith(prefix));
}

function safeNotificationUrl(value) {
  if (typeof value !== "string" || !value.startsWith("/")) {
    return "/";
  }

  try {
    const url = new URL(value, self.location.origin);

    if (url.origin !== self.location.origin) {
      return "/";
    }

    return url.pathname + url.search + url.hash;
  } catch {
    return "/";
  }
}

async function cleanupOldCaches() {
  const keys = await caches.keys();

  await Promise.all(
    keys
      .filter((key) => key.startsWith("formashop-pwa-"))
      .filter((key) => ![
        STATIC_CACHE,
        IMAGE_CACHE,
        PAGE_CACHE
      ].includes(key))
      .map((key) => caches.delete(key))
  );
}

/* =========================================================
   INSTALLATION
   ========================================================= */

self.addEventListener("install", (event) => {
  event.waitUntil(
    (async () => {
      const cache = await caches.open(STATIC_CACHE);

      /*
       * Un fichier statique manquant ne doit pas empêcher
       * l'installation du service worker.
       */
      await Promise.all(
        STATIC_ASSETS.map(async (asset) => {
          try {
            const response = await fetch(asset, {
              cache: "reload"
            });

            if (response.ok) {
              await cache.put(asset, response);
            } else {
              console.warn(
                "[FormaShop PWA] Ressource non mise en cache :",
                asset,
                response.status
              );
            }
          } catch (error) {
            console.warn(
              "[FormaShop PWA] Ressource inaccessible :",
              asset,
              error
            );
          }
        })
      );

      await self.skipWaiting();
    })()
  );
});

/* =========================================================
   ACTIVATION
   ========================================================= */

self.addEventListener("activate", (event) => {
  event.waitUntil(
    (async () => {
      await cleanupOldCaches();
      await self.clients.claim();

      /*
       * Les pages ouvertes peuvent détecter que la nouvelle
       * version du service worker est active.
       */
      const clients = await self.clients.matchAll({
        type: "window",
        includeUncontrolled: true
      });

      for (const client of clients) {
        client.postMessage({
          type: "FORMASHOP_SW_READY",
          version: CACHE_VERSION
        });
      }
    })()
  );
});

/* =========================================================
   MESSAGES DEPUIS LES PAGES
   ========================================================= */

self.addEventListener("message", (event) => {
  if (event.data?.type === "SKIP_WAITING") {
    event.waitUntil(self.skipWaiting());
  }

  if (event.data?.type === "GET_VERSION") {
    if (event.ports && event.ports[0]) {
      event.ports[0].postMessage({
        version: CACHE_VERSION
      });
    }
  }
});

/* =========================================================
   CACHE ET NAVIGATION HORS LIGNE
   ========================================================= */

self.addEventListener("fetch", (event) => {
  const request = event.request;

  if (request.method !== "GET") {
    return;
  }

  const url = new URL(request.url);

  if (url.origin !== self.location.origin) {
    return;
  }

  /*
   * Ne jamais mettre en cache les données privées,
   * les comptes, les commandes ou les paiements.
   */
  if (isSensitivePath(url.pathname)) {
    return;
  }

  /*
   * Fichiers statiques : cache d'abord, réseau ensuite.
   */
  if (url.pathname.startsWith("/static/")) {
    event.respondWith(
      (async () => {
        const cache = await caches.open(STATIC_CACHE);
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
        } catch {
          return new Response(
            "Ressource indisponible hors ligne.",
            {
              status: 503,
              headers: {
                "Content-Type": "text/plain; charset=utf-8"
              }
            }
          );
        }
      })()
    );

    return;
  }

  /*
   * Images publiques : cache dédié.
   * Les documents privés ne sont pas mis en cache.
   */
  if (
    request.destination === "image" &&
    !url.pathname.startsWith("/media/documents/")
  ) {
    event.respondWith(
      (async () => {
        const cache = await caches.open(IMAGE_CACHE);
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
        } catch {
          return new Response("", {
            status: 503,
            statusText: "Image indisponible hors ligne"
          });
        }
      })()
    );

    return;
  }

  /*
   * Navigation : réseau en priorité.
   * En cas de coupure, page hors ligne publique.
   */
  if (request.mode === "navigate") {
    event.respondWith(
      (async () => {
        try {
          return await fetch(request);
        } catch {
          if (isSensitivePath(url.pathname)) {
            return new Response(
              "<!doctype html>" +
              "<html lang='fr'>" +
              "<meta charset='utf-8'>" +
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

          const offline = await caches.match(OFFLINE_URL);

          if (offline) {
            return offline;
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
        }
      })()
    );
  }
});

/* =========================================================
   RÉCEPTION DES NOTIFICATIONS PUSH
   ========================================================= */

self.addEventListener("push", (event) => {
  event.waitUntil(
    (async () => {
      let data = {};

      try {
        if (event.data) {
          data = event.data.json();
        }
      } catch {
        try {
          data = {
            title: "FormaShop",
            body: event.data
              ? event.data.text()
              : "Une nouveauté vous attend."
          };
        } catch {
          data = {};
        }
      }

      const title =
        typeof data.title === "string" && data.title.trim()
          ? data.title
          : "FormaShop";

      const options = {
        body:
          typeof data.body === "string" && data.body.trim()
            ? data.body
            : "Ouvrez FormaShop pour en savoir plus.",

        icon: "/static/pwa/icon-192.png",
        badge: "/static/pwa/icon-192.png",

        data: {
          url: safeNotificationUrl(data.url)
        },

        tag:
          typeof data.tag === "string" && data.tag.trim()
            ? data.tag
            : "formashop-notification",

        renotify: false,
        silent: false
      };

      if (typeof data.image === "string") {
        const imageUrl = new URL(
          data.image,
          self.location.origin
        );

        if (imageUrl.origin === self.location.origin) {
          options.image = imageUrl.href;
        }
      }

      if (Array.isArray(data.actions)) {
        options.actions = data.actions
          .filter((action) =>
            action &&
            typeof action.action === "string" &&
            typeof action.title === "string"
          )
          .slice(0, 2);
      }

      await self.registration.showNotification(title, options);
    })()
  );
});

/* =========================================================
   CLIC SUR UNE NOTIFICATION
   ========================================================= */

self.addEventListener("notificationclick", (event) => {
  event.notification.close();

  event.waitUntil(
    (async () => {
      const targetUrl = new URL(
        safeNotificationUrl(event.notification.data?.url),
        self.location.origin
      );

      const clients = await self.clients.matchAll({
        type: "window",
        includeUncontrolled: true
      });

      for (const client of clients) {
        if (client.url.startsWith(self.location.origin)) {
          if ("navigate" in client) {
            await client.navigate(targetUrl.href);
          }

          if ("focus" in client) {
            await client.focus();
          }

          return;
        }
      }

      if (self.clients.openWindow) {
        await self.clients.openWindow(targetUrl.href);
      }
    })()
  );
});

/* =========================================================
   FERMETURE D'UNE NOTIFICATION
   ========================================================= */

self.addEventListener("notificationclose", (event) => {
  /*
   * Point d'extension possible pour mesurer les notifications
   * ignorées, si FormaShop ajoute ultérieurement une API dédiée.
   */
  event.waitUntil(Promise.resolve());
});