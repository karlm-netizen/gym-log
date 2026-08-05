// Gym-Log Service Worker â€” Netz zuerst (Updates erreichen den Nutzer sofort),
// Cache nur als Offline-RÃ¼ckfall. Assets einzeln cachen, damit eine fehlende
// Datei nicht die ganze Offline-Funktion killt (Lektion aus Dranbleiben).
const CACHE = 'gymlog-v14';
const ASSETS = ['./', './index.html', './manifest.webmanifest', './icon.svg', './icon-192.png', './icon-512.png',
  './brock.png',
  './brock-1.png', './brock-2.png', './brock-3.png', './brock-4.png', './brock-5.png',
  './brock-6.png', './brock-7.png', './brock-8.png', './brock-9.png'];

self.addEventListener('install', e => {
  e.waitUntil(
    caches.open(CACHE)
      .then(c => Promise.all(ASSETS.map(a => c.add(a).catch(() => {}))))
      .then(() => self.skipWaiting())
  );
});

self.addEventListener('activate', e => {
  e.waitUntil(
    caches.keys()
      .then(ks => Promise.all(ks.filter(k => k !== CACHE).map(k => caches.delete(k))))
      .then(() => self.clients.claim())
  );
});

self.addEventListener('fetch', e => {
  if (e.request.method !== 'GET') return;
  e.respondWith(
    fetch(e.request)
      .then(r => { const cp = r.clone(); caches.open(CACHE).then(c => c.put(e.request, cp)); return r; })
      .catch(() => caches.match(e.request).then(m => m || caches.match('./index.html')))
  );
});
