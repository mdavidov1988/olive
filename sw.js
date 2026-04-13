const CACHE_NAME = 'olive-v2';

self.addEventListener('install', e => {
    e.waitUntil(
        caches.open(CACHE_NAME).then(c =>
            c.addAll([
                './',
                './index.html',
                './manifest.json',
                'https://cdn.tailwindcss.com',
                'https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap',
            ])
        )
    );
    self.skipWaiting();
});

self.addEventListener('activate', e => {
    e.waitUntil(
        caches.keys().then(keys =>
            Promise.all(keys.filter(k => k !== CACHE_NAME).map(k => caches.delete(k)))
        )
    );
    self.clients.claim();
});

self.addEventListener('fetch', e => {
    e.respondWith(
        caches.match(e.request).then(cached => {
            const fetchPromise = fetch(e.request).then(res => {
                if (res && res.status === 200) {
                    const clone = res.clone();
                    caches.open(CACHE_NAME).then(c => c.put(e.request, clone));
                }
                return res;
            }).catch(() => cached);
            return cached || fetchPromise;
        })
    );
});
