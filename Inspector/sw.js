// Service Worker for בודק אוטובוס
const CACHE_NAME = 'bus-inspector-v1';

self.addEventListener('install', (event) => {
  self.skipWaiting();
});

self.addEventListener('activate', (event) => {
  event.waitUntil(clients.claim());
});

// Listen for notification display messages from the app
self.addEventListener('message', (event) => {
  if (event.data && event.data.type === 'SHOW_NOTIFICATION') {
    const { stationName, stationId } = event.data;
    event.waitUntil(
      self.registration.showNotification('בודק אוטובוס 🚌', {
        body: `נראה שאתה ב${stationName}. יש בודק?`,
        icon: '/icon.png',
        badge: '/icon.png',
        tag: `station-${stationId}`,   // prevents duplicate notifications for same station
        renotify: false,
        data: { stationId },
        actions: [
          { action: 'inspector', title: '🚨 יש בודק' },
          { action: 'clear',     title: '✅ נקי' }
        ]
      })
    );
  }
});

// Handle notification click - open the app
self.addEventListener('notificationclick', (event) => {
  event.notification.close();
  const stationId = event.notification.data && event.notification.data.stationId;

  event.waitUntil(
    clients.matchAll({ type: 'window', includeUncontrolled: true }).then((clientList) => {
      // If app is already open, focus it and send station info
      for (const client of clientList) {
        if (client.url.includes(self.location.origin)) {
          client.focus();
          client.postMessage({ type: 'OPEN_PROMPT', stationId });
          return;
        }
      }
      // Otherwise open the app
      return clients.openWindow(`/?station=${stationId}`);
    })
  );
});
