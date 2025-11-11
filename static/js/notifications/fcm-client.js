(function (window, document) {
    'use strict';

    if (!window || !document) {
        return;
    }

    var FIREBASE_SCRIPTS = [
        'https://www.gstatic.com/firebasejs/8.10.1/firebase-app.js',
        'https://www.gstatic.com/firebasejs/8.10.1/firebase-messaging.js'
    ];

    var STORAGE_TOKEN_KEY = 'arab_chat_fcm_token';
    var state = {
        firebaseLoaded: false,
        messaging: null,
        registration: null,
        currentToken: null,
        initStarted: false,
        preferences: null
    };

    function loadScript(src) {
        return new Promise(function (resolve, reject) {
            var script = document.createElement('script');
            script.src = src;
            script.async = true;
            script.onload = function () {
                resolve();
            };
            script.onerror = function () {
                reject(new Error('Failed to load script ' + src));
            };
            document.head.appendChild(script);
        });
    }

    function loadFirebaseScripts() {
        if (state.firebaseLoaded) {
            return Promise.resolve();
        }
        return Promise.all(FIREBASE_SCRIPTS.map(loadScript)).then(function () {
            state.firebaseLoaded = true;
        });
    }

    function getAppConfig() {
        var config = window.__APP_CONFIG__ || {};
        var firebaseConfig = config.firebaseConfig || {};
        if (firebaseConfig && !firebaseConfig.messagingSenderId && config.fcmWebPushSenderId) {
            firebaseConfig.messagingSenderId = config.fcmWebPushSenderId;
        }
        return {
            firebaseConfig: firebaseConfig,
            vapidKey: config.fcmWebPushPublicKey || null,
            userId: config.userId || null
        };
    }

    function getAuthToken() {
        try {
            return window.localStorage ? (localStorage.getItem('auth_token') || '') : '';
        } catch (err) {
            return '';
        }
    }

    function buildApiUrl(path) {
        if (typeof window.buildApiUrl === 'function') {
            return window.buildApiUrl(path);
        }
        var base = (window.API_BASE_URL || '/api').replace(/\/+$/, '');
        return base + '/' + path.replace(/^\/+/, '');
    }

    function postJson(url, payload) {
        var headers = { 'Content-Type': 'application/json' };
        var token = getAuthToken();
        if (token) {
            headers.Authorization = 'Token ' + token;
        }
        return fetch(url, {
            method: 'POST',
            headers: headers,
            body: JSON.stringify(payload || {}),
            credentials: 'include'
        });
    }

    function registerDeviceToken(token) {
        if (!token) {
            return Promise.resolve();
        }
        var apiUrl = buildApiUrl('device-tokens/register/');
        return postJson(apiUrl, {
            token: token,
            device_type: 'web',
            device_name: (navigator.userAgent || 'web-browser').slice(0, 200)
        }).catch(function (err) {
            console.warn('[FCM] Failed to register device token', err);
        });
    }

    function unregisterDeviceToken(token) {
        if (!token) {
            return Promise.resolve();
        }
        var apiUrl = buildApiUrl('device-tokens/unregister/');
        return postJson(apiUrl, { token: token }).catch(function (err) {
            console.warn('[FCM] Failed to unregister device token', err);
        });
    }

    function ensureServiceWorker() {
        if (!('serviceWorker' in navigator)) {
            return Promise.reject(new Error('Service workers are not supported'));
        }
        return navigator.serviceWorker.ready.then(function (registration) {
            state.registration = registration;
            return registration;
        });
    }

    function saveToken(token) {
        try {
            if (window.localStorage) {
                localStorage.setItem(STORAGE_TOKEN_KEY, token);
            }
        } catch (err) {
            // Ignore storage errors
        }
    }

    function getSavedToken() {
        try {
            return window.localStorage ? (localStorage.getItem(STORAGE_TOKEN_KEY) || null) : null;
        } catch (err) {
            return null;
        }
    }

    function notifyPreferences() {
        if (!state.preferences || !state.registration || !state.registration.active) {
            return;
        }
        try {
            state.registration.active.postMessage({
                type: 'SET_NOTIFICATION_PREFS',
                payload: state.preferences
            });
        } catch (err) {
            console.warn('[FCM] Failed to send preferences to service worker', err);
        }
    }

    function ensureFirebaseMessaging(config) {
        if (!state.firebaseLoaded) {
            return Promise.reject(new Error('Firebase scripts not loaded'));
        }

        if (typeof firebase === 'undefined' || !firebase.messaging) {
            return Promise.reject(new Error('Firebase messaging is unavailable'));
        }

        if (firebase.messaging.isSupported && !firebase.messaging.isSupported()) {
            return Promise.reject(new Error('Firebase messaging not supported in this browser'));
        }

        if (!firebase.apps || firebase.apps.length === 0) {
            firebase.initializeApp(config);
        }

        state.messaging = firebase.messaging();
        return Promise.resolve(state.messaging);
    }

    function requestPermission() {
        if (!('Notification' in window)) {
            return Promise.resolve(false);
        }
        if (Notification.permission === 'granted') {
            return Promise.resolve(true);
        }
        if (Notification.permission === 'denied') {
            return Promise.resolve(false);
        }
        return Notification.requestPermission().then(function (permission) {
            return permission === 'granted';
        });
    }

    function obtainToken(vapidKey) {
        if (!state.messaging) {
            return Promise.reject(new Error('Messaging not initialised'));
        }
        return ensureServiceWorker().then(function (registration) {
            if (state.messaging.useServiceWorker) {
                state.messaging.useServiceWorker(registration);
            }
            return state.messaging.getToken({
                vapidKey: vapidKey || undefined,
                serviceWorkerRegistration: registration
            });
        });
    }

    function handleTokenChange(newToken, options) {
        if (!newToken) {
            return;
        }
        var savedToken = getSavedToken();
        if (savedToken === newToken) {
            state.currentToken = newToken;
            notifyPreferences();
            return;
        }

        registerDeviceToken(newToken).then(function () {
            state.currentToken = newToken;
            saveToken(newToken);
            if (options && options.oldToken && options.oldToken !== newToken) {
                unregisterDeviceToken(options.oldToken);
            }
            notifyPreferences();
        });
    }

    function attachMessagingListeners(vapidKey) {
        if (!state.messaging) {
            return;
        }

        state.messaging.onTokenRefresh(function () {
            obtainToken(vapidKey)
                .then(function (refreshedToken) {
                    handleTokenChange(refreshedToken, { oldToken: state.currentToken });
                })
                .catch(function (err) {
                    console.warn('[FCM] Token refresh failed', err);
                });
        });

        state.messaging.onMessage(function (payload) {
            try {
                window.dispatchEvent(new CustomEvent('arab-chat:fcm-message', { detail: payload }));
            } catch (err) {
                console.debug('[FCM] foreground message received', payload);
            }
        });
    }

    function initialiseFCM() {
        if (state.initStarted) {
            return Promise.resolve(state.currentToken);
        }

        var config = getAppConfig();
        if (!config.userId || !config.firebaseConfig || !config.firebaseConfig.apiKey) {
            return Promise.resolve(null);
        }

        state.initStarted = true;

        return loadFirebaseScripts()
            .then(function () {
                return requestPermission();
            })
            .then(function (granted) {
                if (!granted) {
                    throw new Error('Notification permission was not granted');
                }
                return ensureFirebaseMessaging(config.firebaseConfig);
            })
            .then(function () {
                return obtainToken(config.vapidKey);
            })
            .then(function (token) {
                attachMessagingListeners(config.vapidKey);
                var previousToken = state.currentToken || getSavedToken();
                handleTokenChange(token, { oldToken: previousToken });
                return token;
            })
            .catch(function (err) {
                state.initStarted = false;
                console.warn('[FCM] Initialisation failed', err);
                return null;
            });
    }

    function updatePreferences(preferences) {
        state.preferences = preferences || {};
        notifyPreferences();
    }

    function unregisterCurrentToken() {
        var token = state.currentToken || getSavedToken();
        state.currentToken = null;
        try {
            if (window.localStorage) {
                localStorage.removeItem(STORAGE_TOKEN_KEY);
            }
        } catch (err) {
            // ignore
        }
        if (token) {
            return unregisterDeviceToken(token);
        }
        return Promise.resolve();
    }

    window.ArabChatNotifications = {
        init: initialiseFCM,
        refreshToken: initialiseFCM,
        updatePreferences: updatePreferences,
        unregister: unregisterCurrentToken,
        getCurrentToken: function () {
            return state.currentToken || getSavedToken();
        }
    };

    document.addEventListener('DOMContentLoaded', function () {
        if (!getAppConfig().userId) {
            return;
        }
        if (!('serviceWorker' in navigator)) {
            console.warn('[FCM] Service workers are required for push notifications.');
            return;
        }
        initialiseFCM();
    });
})(window, document);


