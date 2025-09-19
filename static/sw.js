/**
 * Service Worker for AI Executive Suite
 * 
 * Handles background notifications, offline caching, and push notifications
 */

const CACHE_NAME = 'ai-executive-suite-v1';
const NOTIFICATION_TAG_PREFIX = 'ai-exec-';

// Files to cache for offline functionality
const CACHE_FILES = [
    '/',
    '/static/css/style.css',
    '/static/css/mobile.css',
    '/static/js/app.js',
    '/static/js/mobile-notifications.js',
    '/static/icons/icon-192x192.png',
    '/static/icons/icon-512x512.png'
];

// Install event - cache resources
self.addEventListener('install', (event) => {
    console.log('Service Worker installing...');
    
    event.waitUntil(
        caches.open(CACHE_NAME)
            .then((cache) => {
                console.log('Caching app shell');
                return cache.addAll(CACHE_FILES);
            })
            .then(() => {
                // Skip waiting to activate immediately
                return self.skipWaiting();
            })
    );
});

// Activate event - clean up old caches
self.addEventListener('activate', (event) => {
    console.log('Service Worker activating...');
    
    event.waitUntil(
        caches.keys().then((cacheNames) => {
            return Promise.all(
                cacheNames.map((cacheName) => {
                    if (cacheName !== CACHE_NAME) {
                        console.log('Deleting old cache:', cacheName);
                        return caches.delete(cacheName);
                    }
                })
            );
        }).then(() => {
            // Claim all clients immediately
            return self.clients.claim();
        })
    );
});

// Fetch event - serve from cache when offline
self.addEventListener('fetch', (event) => {
    // Skip non-GET requests
    if (event.request.method !== 'GET') {
        return;
    }
    
    // Skip external requests
    if (!event.request.url.startsWith(self.location.origin)) {
        return;
    }
    
    event.respondWith(
        caches.match(event.request)
            .then((response) => {
                // Return cached version or fetch from network
                return response || fetch(event.request).catch(() => {
                    // If both cache and network fail, return offline page
                    if (event.request.destination === 'document') {
                        return caches.match('/offline.html');
                    }
                });
            })
    );
});

// Push event - handle push notifications
self.addEventListener('push', (event) => {
    console.log('Push notification received');
    
    let notificationData = {
        title: 'AI Executive Suite',
        body: 'You have a new update',
        icon: '/static/icons/icon-192x192.png',
        badge: '/static/icons/badge-72x72.png',
        tag: NOTIFICATION_TAG_PREFIX + 'default',
        requireInteraction: false,
        actions: [
            {
                action: 'view',
                title: 'View',
                icon: '/static/icons/view-icon.png'
            },
            {
                action: 'dismiss',
                title: 'Dismiss',
                icon: '/static/icons/dismiss-icon.png'
            }
        ]
    };
    
    // Parse push data if available
    if (event.data) {
        try {
            const pushData = event.data.json();
            notificationData = { ...notificationData, ...pushData };
        } catch (error) {
            console.error('Failed to parse push data:', error);
        }
    }
    
    event.waitUntil(
        self.registration.showNotification(notificationData.title, notificationData)
    );
});

// Notification click event
self.addEventListener('notificationclick', (event) => {
    console.log('Notification clicked:', event.notification);
    
    const notification = event.notification;
    const action = event.action;
    
    // Close the notification
    notification.close();
    
    // Handle different actions
    if (action === 'dismiss') {
        // Just close the notification
        return;
    }
    
    // Default action or 'view' action - open the app
    event.waitUntil(
        clients.matchAll({ type: 'window', includeUncontrolled: true })
            .then((clientList) => {
                // Check if app is already open
                for (const client of clientList) {
                    if (client.url.includes(self.location.origin) && 'focus' in client) {
                        // Focus existing window
                        client.focus();
                        
                        // Send message to client about notification click
                        client.postMessage({
                            type: 'notification-click',
                            notification: {
                                title: notification.title,
                                body: notification.body,
                                tag: notification.tag,
                                data: notification.data
                            }
                        });
                        
                        return;
                    }
                }
                
                // Open new window if app is not open
                if (clients.openWindow) {
                    return clients.openWindow('/').then((client) => {
                        if (client) {
                            // Send message to new client
                            client.postMessage({
                                type: 'notification-click',
                                notification: {
                                    title: notification.title,
                                    body: notification.body,
                                    tag: notification.tag,
                                    data: notification.data
                                }
                            });
                        }
                    });
                }
            })
    );
});

// Notification close event
self.addEventListener('notificationclose', (event) => {
    console.log('Notification closed:', event.notification);
    
    // Send message to clients about notification close
    event.waitUntil(
        clients.matchAll({ type: 'window', includeUncontrolled: true })
            .then((clientList) => {
                clientList.forEach((client) => {
                    client.postMessage({
                        type: 'notification-close',
                        notification: {
                            title: event.notification.title,
                            tag: event.notification.tag
                        }
                    });
                });
            })
    );
});

// Background sync event
self.addEventListener('sync', (event) => {
    console.log('Background sync triggered:', event.tag);
    
    if (event.tag === 'notification-sync') {
        event.waitUntil(syncNotifications());
    }
});

// Sync notifications with server
async function syncNotifications() {
    try {
        // Check for new notifications from server
        const response = await fetch('/api/notifications/sync', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                lastSync: await getLastSyncTime()
            })
        });
        
        if (response.ok) {
            const data = await response.json();
            
            // Show new notifications
            if (data.notifications && data.notifications.length > 0) {
                for (const notification of data.notifications) {
                    await self.registration.showNotification(notification.title, {
                        body: notification.body,
                        icon: notification.icon || '/static/icons/icon-192x192.png',
                        badge: '/static/icons/badge-72x72.png',
                        tag: NOTIFICATION_TAG_PREFIX + notification.id,
                        data: notification.data,
                        requireInteraction: notification.requireInteraction || false,
                        actions: notification.actions || []
                    });
                }
            }
            
            // Update last sync time
            await setLastSyncTime(Date.now());
        }
    } catch (error) {
        console.error('Failed to sync notifications:', error);
    }
}

// Helper functions for sync time management
async function getLastSyncTime() {
    try {
        const cache = await caches.open(CACHE_NAME);
        const response = await cache.match('/last-sync-time');
        if (response) {
            const text = await response.text();
            return parseInt(text, 10);
        }
    } catch (error) {
        console.error('Failed to get last sync time:', error);
    }
    return 0;
}

async function setLastSyncTime(timestamp) {
    try {
        const cache = await caches.open(CACHE_NAME);
        await cache.put('/last-sync-time', new Response(timestamp.toString()));
    } catch (error) {
        console.error('Failed to set last sync time:', error);
    }
}

// Message event - handle messages from main thread
self.addEventListener('message', (event) => {
    console.log('Service Worker received message:', event.data);
    
    const { type, data } = event.data;
    
    switch (type) {
        case 'show-notification':
            self.registration.showNotification(data.title, data.options);
            break;
        case 'clear-notifications':
            clearAllNotifications();
            break;
        case 'sync-notifications':
            syncNotifications();
            break;
        default:
            console.log('Unknown message type:', type);
    }
});

// Clear all notifications
async function clearAllNotifications() {
    try {
        const notifications = await self.registration.getNotifications();
        notifications.forEach(notification => notification.close());
    } catch (error) {
        console.error('Failed to clear notifications:', error);
    }
}

// Periodic background sync (if supported)
self.addEventListener('periodicsync', (event) => {
    console.log('Periodic sync triggered:', event.tag);
    
    if (event.tag === 'notification-check') {
        event.waitUntil(syncNotifications());
    }
});

// Error handling
self.addEventListener('error', (event) => {
    console.error('Service Worker error:', event.error);
});

self.addEventListener('unhandledrejection', (event) => {
    console.error('Service Worker unhandled rejection:', event.reason);
});

console.log('Service Worker loaded successfully');