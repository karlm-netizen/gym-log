// Gym-Log Service Worker â€” Netz zuerst (Updates erreichen den Nutzer sofort),
// Cache nur als Offline-RÃ¼ckfall. Assets einzeln cachen, damit eine fehlende
// Datei nicht die ganze Offline-Funktion killt (Lektion aus Dranbleiben).
const CACHE = 'gymlog-v39';
const ASSETS = ['./', './index.html', './manifest.webmanifest', './icon-192.png', './icon-512.png', './icon-180.png',
  './icon-maskable-192.png', './icon-maskable-512.png',
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

/* ---------- Push: Antwort auf eine Meldung (23.08.2026) ----------
   Uebernommen aus angel-log, samt der dort teuer gelernten Feinheiten.

   ⚠️ **Ohne Nutzlast.** Der Bot schickt einen leeren Anstoss, der Text steht hier
   fest. Zwei Gruende: der Meldetext ginge sonst durch die Server von Apple bzw.
   Google -- dort muss nicht liegen, was jemand an der App auszusetzen hat. Und eine
   Nutzlast muesste verschluesselt werden (aes128gcm, ECDH je Empfaenger); ohne sie
   genuegt die VAPID-Signatur, und das ist deutlich weniger, was schiefgehen kann.

   ⚠️ **showNotification ist Pflicht, nicht Kuer.** Wer ein Push-Ereignis empfaengt
   und nichts anzeigt, wird von den Browsern nach ein paar Malen von der Zustellung
   ausgeschlossen ("silent push").

   ⚠️ **Der Titel IST die Nachricht.** Am iPhone setzt iOS den Namen der Verknuepfung
   ohnehin ueber jede Nachricht -- ihn im Titel zu wiederholen ergab bei angel-log am
   13.08.2026 drei Zeilen, von denen zwei dasselbe sagten. */
self.addEventListener('push', e => {
  let daten = {};
  try { if (e.data) daten = e.data.json(); } catch { daten = {}; }
  const text = daten.text || 'Neue Antwort auf deine Meldung.';
  e.waitUntil(self.registration.showNotification(text, {
    icon: './icon-192.png',
    badge: './icon-192.png',
    /* Gleiches `tag`: eine zweite Antwort ersetzt die erste, statt den
       Sperrbildschirm zuzustellen. */
    tag: 'gym-ticket',
    data: { url: './' }
  }));
});

/* Tippen auf die Nachricht: ein offenes Fenster nach vorn holen, sonst eines oeffnen.
   ⚠️ Ohne das Suchen nach einem offenen Fenster oeffnet iOS eine ZWEITE Instanz der
   App -- mit eigenem Zustand, und der Satz, den man gerade eintippt, waere im anderen. */
self.addEventListener('notificationclick', e => {
  e.notification.close();
  e.waitUntil((async () => {
    const ziel = new URL((e.notification.data && e.notification.data.url) || './', self.location.href).href;
    const fenster = await self.clients.matchAll({ type: 'window', includeUncontrolled: true });
    for (const f of fenster){
      if (f.url.startsWith(self.registration.scope) && 'focus' in f) {
        /* Das offene Fenster weiss nichts von der Mitteilung -- ohne diese Nachricht
           holt focus() nur die Startseite nach vorn, auf der nichts steht. Ob wirklich
           gesprungen wird, entscheidet die App: laeuft ein Training, bleibt sie stehen. */
        if ('postMessage' in f) { try { f.postMessage({ typ: 'postfach' }); } catch (e) {} }
        return f.focus();
      }
    }
    if (self.clients.openWindow) return self.clients.openWindow(ziel + '#postfach');
  })());
});
