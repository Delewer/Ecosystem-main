self.addEventListener('install', event => {
  event.waitUntil(caches.open('ecosystem-static-v1').then(cache => cache.addAll(['/','/estudy/'])));
});

self.addEventListener('fetch', event => {
  event.respondWith(
    caches.match(event.request).then(response => response || fetch(event.request))
  );
});
