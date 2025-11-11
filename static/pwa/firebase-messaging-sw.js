/* global firebase */
// Service worker خاص بإشعارات Firebase Cloud Messaging

const FIREBASE_SCRIPTS = [
  'https://www.gstatic.com/firebasejs/8.10.1/firebase-app.js',
  'https://www.gstatic.com/firebasejs/8.10.1/firebase-messaging.js',
];

let firebaseApp = null;
let messaging = null;
let firebaseConfig = null;
let notificationPreferences = {
  sound: true,
  vibrate: true,
};

function initialiseFirebase(config) {
  if (firebaseApp || !config || !config.apiKey) {
    return;
  }
  try {
    self.importScripts(...FIREBASE_SCRIPTS);
    firebaseApp = firebase.initializeApp(config);
    messaging = firebase.messaging();
    messaging.onBackgroundMessage((payload) => {
      const { notification, data } = payload;
      if (notification) {
        const notificationOptions = {
          body: notification.body || data?.body || '',
          icon: notification.icon || data?.icon || '/static/pwa/icons/icon-192.png',
          data: { ...(data || {}) },
          tag: data?.type || 'arab-chat',
        };
        if (data?.title && !notification.title) {
          notificationOptions.title = data.title;
        }
        if (notificationPreferences.vibrate !== false) {
          notificationOptions.vibrate = [200, 100, 200];
        }
        if (notificationPreferences.sound === false) {
          notificationOptions.silent = true;
        }
        const soundKey = notification.sound || data?.sound;
        if (soundKey === 'call_incoming') {
          notificationOptions.renotify = true;
          notificationOptions.requireInteraction = true;
          notificationOptions.actions = [
            { action: 'accept_call', title: 'رد', icon: '/static/pwa/icons/icon-192.png' },
            { action: 'reject_call', title: 'رفض' },
          ];
        }
        if (soundKey && soundKey !== 'default') {
          notificationOptions.data.sound = soundKey;
        }
        if (data?.requireInteraction && data.requireInteraction !== 'false') {
          notificationOptions.requireInteraction = true;
        }
        if (data?.url) {
          notificationOptions.data = notificationOptions.data || {};
          notificationOptions.data.url = data.url;
        }
        self.registration.showNotification(notification.title || data?.title || 'Arab Chat', notificationOptions);
      }
    });
  } catch (error) {
    console.error('[FCM SW] Failed to initialise Firebase', error);
  }
}

self.addEventListener('install', (event) => {
  event.waitUntil(self.skipWaiting());
});

self.addEventListener('activate', (event) => {
  event.waitUntil(self.clients.claim());
});

self.addEventListener('message', (event) => {
  const { data } = event;
  if (!data || typeof data !== 'object') {
    return;
  }

  if (data.type === 'FCM_INIT') {
    firebaseConfig = data.payload?.config || null;
    initialiseFirebase(firebaseConfig);
  }

  if (data.type === 'SET_NOTIFICATION_PREFS') {
    notificationPreferences = {
      ...notificationPreferences,
      ...(data.payload || {}),
    };
  }

  if (data.type === 'FCM_DELETE_TOKEN' && messaging) {
    messaging.deleteToken().catch((error) => console.warn('[FCM SW] deleteToken failed', error));
  }
});

self.addEventListener('notificationclick', (event) => {
  event.notification.close();
  const targetUrl = event.notification.data?.url || '/';
  if (event.action === 'accept_call' || event.action === 'reject_call') {
    const action = event.action === 'accept_call' ? 'accept' : 'reject';
    event.waitUntil(
      self.clients.matchAll({ type: 'window', includeUncontrolled: true }).then((clientList) => {
        clientList.forEach((client) => {
          client.postMessage({ type: 'CALL_ACTION', action, payload: event.notification.data || {} });
          if (action === 'accept' && targetUrl) {
            client.postMessage({ type: 'OPEN_URL', url: targetUrl });
          }
        });
        if (action === 'accept' && targetUrl && self.clients.openWindow) {
          return self.clients.openWindow(targetUrl);
        }
        return undefined;
      })
    );
    return;
  }

  event.waitUntil(
    self.clients.matchAll({ type: 'window', includeUncontrolled: true }).then((clientList) => {
      for (const client of clientList) {
        if ('focus' in client) {
          client.focus();
          if (targetUrl) {
            client.postMessage({ type: 'OPEN_URL', url: targetUrl });
          }
          return;
        }
      }
      if (self.clients.openWindow && targetUrl) {
        return self.clients.openWindow(targetUrl);
      }
    })
  );
});

self.addEventListener('push', (event) => {
  if (event.data) {
    try {
      const payload = event.data.json();
      if (!firebaseApp && payload?.data?.firebaseConfig) {
        initialiseFirebase(JSON.parse(payload.data.firebaseConfig));
      }
      if (!messaging && firebaseConfig) {
        initialiseFirebase(firebaseConfig);
      }
    } catch (error) {
      console.warn('[FCM SW] push event parse failed', error);
    }
  }
});

