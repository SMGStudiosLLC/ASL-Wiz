const CACHE_NAME = 'asl-practice-v1';
const urlsToCache = [
    '/',
    '/index.html',
    '/assets/css/style.css',
    '/assets/js/app.js',
    '/assets/js/words.js',
    '/assets/images/blank.gif',
    '/assets/images/goodjob.png',
    '/assets/images/tryagain.png'
];

// Add all letter images to cache
const letters = 'abcdefghijklmnopqrstuvwxyz';
for (let letter of letters) {
    urlsToCache.push(`/assets/images/${letter}.gif`);
    urlsToCache.push(`/assets/images/${letter}${letter}.gif`);
}

self.addEventListener('install', event => {
    event.waitUntil(
        caches.open(CACHE_NAME)
            .then(cache => {
                return cache.addAll(urlsToCache);
            })
    );
});

self.addEventListener('fetch', event => {
    event.respondWith(
        caches.match(event.request)
            .then(response => {
                // Return cached version or fetch from network
                return response || fetch(event.request);
            }
        )
    );
});
