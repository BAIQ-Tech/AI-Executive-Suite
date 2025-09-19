/**
 * Mobile Notifications Service
 * 
 * Handles push notifications, offline sync, and notification management
 * for the AI Executive Suite mobile interface.
 */

class MobileNotificationService {
    constructor() {
        this.isSupported = 'Notification' in window && 'serviceWorker' in navigator;
        this.permission = this.isSupported ? Notification.permission : 'denied';
        this.notificationQueue = [];
        this.offlineQueue = [];
        this.preferences = this.loadPreferences();
        this.serviceWorkerRegistration = null;
        
        this.init();
    }
    
    async init() {
        if (!this.isSupported) {
            console.warn('Notifications not supported in this browser');
            return;
        }
        
        // Register service worker for background notifications
        await this.registerServiceWorker();
        
        // Set up offline/online event listeners
        this.setupOfflineHandling();
        
        // Set up periodic sync for offline notifications
        this.setupPeriodicSync();
        
        console.log('Mobile notification service initialized');
    }
    
    async registerServiceWorker() {
        try {
            this.serviceWorkerRegistration = await navigator.serviceWorker.register('/sw.js');
            console.log('Service Worker registered successfully');
            
            // Listen for messages from service worker
            navigator.serviceWorker.addEventListener('message', (event) => {
                this.handleServiceWorkerMessage(event.data);
            });
            
        } catch (error) {
            console.error('Service Worker registration failed:', error);
        }
    }
    
    async requestPermission() {
        if (!this.isSupported) {
            throw new Error('Notifications not supported');
        }
        
        if (this.permission === 'granted') {
            return true;
        }
        
        if (this.permission === 'denied') {
            throw new Error('Notification permission denied');
        }
        
        if (this.permission === 'default') {
            // Permission not yet requested
        }
        
        // Request permission
        const permission = await Notification.requestPermission();
        this.permission = permission;
        
        if (permission === 'granted') {
            this.savePreferences();
            return true;
        } else {
            throw new Error('Notification permission not granted');
        }
    }
    
    async showNotification(title, options = {}) {
        try {
            // Check if we have permission
            if (this.permission !== 'granted') {
                await this.requestPermission();
            }
            
            // Check user preferences
            if (!this.shouldShowNotification(options.type)) {
                return null;
            }
            
            // Default notification options
            const defaultOptions = {
                icon: '/static/icons/icon-192x192.png',
                badge: '/static/icons/badge-72x72.png',
                vibrate: [200, 100, 200],
                requireInteraction: false,
                silent: false,
                ...options
            };
            
            // If offline, queue the notification
            if (!navigator.onLine) {
                this.queueOfflineNotification(title, defaultOptions);
                return null;
            }
            
            // Show notification
            let notification;
            if (this.serviceWorkerRegistration) {
                // Use service worker for persistent notifications
                notification = await this.serviceWorkerRegistration.showNotification(title, defaultOptions);
            } else {
                // Fallback to regular notification
                notification = new Notification(title, defaultOptions);
            }
            
            // Set up click handler
            if (notification && options.onClick) {
                notification.onclick = options.onClick;
            }
            
            // Auto-close after specified time
            if (options.autoClose && notification) {
                setTimeout(() => {
                    notification.close();
                }, options.autoClose);
            }
            
            return notification;
            
        } catch (error) {
            console.error('Failed to show notification:', error);
            // Fallback to in-app notification
            this.showInAppNotification(title, options);
            return null;
        }
    }
    
    showInAppNotification(title, options = {}) {
        const notification = document.createElement('div');
        notification.className = `mobile-notification ${options.type || 'info'}`;
        notification.style.cssText = `
            position: fixed;
            top: 20px;
            left: 10px;
            right: 10px;
            background: ${this.getNotificationColor(options.type)};
            color: white;
            padding: 15px;
            border-radius: 8px;
            box-shadow: 0 4px 12px rgba(0,0,0,0.3);
            z-index: 10000;
            animation: slideDown 0.3s ease;
            cursor: pointer;
        `;
        
        notification.innerHTML = `
            <div style="display: flex; align-items: center; gap: 10px;">
                <div style="font-size: 1.2rem;">${this.getNotificationIcon(options.type)}</div>
                <div style="flex: 1;">
                    <div style="font-weight: 600; margin-bottom: 2px;">${title}</div>
                    ${options.body ? `<div style="font-size: 0.9rem; opacity: 0.9;">${options.body}</div>` : ''}
                </div>
                <button onclick="this.parentElement.parentElement.remove()" 
                        style="background: none; border: none; color: white; font-size: 1.2rem; cursor: pointer;">
                    ×
                </button>
            </div>
        `;
        
        // Add click handler
        if (options.onClick) {
            notification.addEventListener('click', (e) => {
                if (e.target.tagName !== 'BUTTON') {
                    options.onClick();
                    notification.remove();
                }
            });
        }
        
        document.body.appendChild(notification);
        
        // Auto-remove after specified time
        const autoClose = options.autoClose || 5000;
        setTimeout(() => {
            if (document.body.contains(notification)) {
                notification.style.animation = 'slideUp 0.3s ease';
                setTimeout(() => notification.remove(), 300);
            }
        }, autoClose);
        
        return notification;
    }
    
    getNotificationColor(type) {
        const colors = {
            'success': 'rgba(72, 187, 120, 0.95)',
            'error': 'rgba(245, 101, 101, 0.95)',
            'warning': 'rgba(237, 137, 54, 0.95)',
            'info': 'rgba(102, 126, 234, 0.95)',
            'decision': 'rgba(102, 126, 234, 0.95)'
        };
        return colors[type] || colors.info;
    }
    
    getNotificationIcon(type) {
        const icons = {
            'success': '✅',
            'error': '❌',
            'warning': '⚠️',
            'info': 'ℹ️',
            'decision': '🤖'
        };
        return icons[type] || icons.info;
    }
    
    // Decision-specific notifications
    async notifyDecisionUpdate(decision, type = 'created') {
        const titles = {
            'created': '🤖 New Decision',
            'updated': '📝 Decision Updated',
            'completed': '✅ Decision Completed',
            'rejected': '❌ Decision Rejected'
        };
        
        const title = titles[type] || 'Decision Update';
        const body = `${decision.executive_type.toUpperCase()}: ${decision.decision.substring(0, 100)}...`;
        
        return await this.showNotification(title, {
            body,
            type: 'decision',
            icon: '/static/icons/decision-icon.png',
            tag: `decision-${decision.id}`,
            data: { decisionId: decision.id, type },
            actions: [
                {
                    action: 'view',
                    title: 'View Decision',
                    icon: '/static/icons/view-icon.png'
                },
                {
                    action: 'dismiss',
                    title: 'Dismiss',
                    icon: '/static/icons/dismiss-icon.png'
                }
            ],
            onClick: () => {
                window.focus();
                // Navigate to decision
                if (window.switchAgent) {
                    window.switchAgent(decision.executive_type);
                }
            }
        });
    }
    
    async notifyCollaborationUpdate(collaboration) {
        const title = '👥 Collaboration Update';
        const body = `New comment on decision: ${collaboration.decision_title}`;
        
        return await this.showNotification(title, {
            body,
            type: 'info',
            tag: `collaboration-${collaboration.decision_id}`,
            data: { collaborationId: collaboration.id },
            onClick: () => {
                window.focus();
                // Navigate to collaboration
                window.location.href = `/collaboration/decision/${collaboration.decision_id}`;
            }
        });
    }
    
    async notifySystemUpdate(message, type = 'info') {
        const title = '🔔 System Update';
        
        return await this.showNotification(title, {
            body: message,
            type,
            tag: 'system-update',
            autoClose: 8000
        });
    }
    
    // Offline notification handling
    queueOfflineNotification(title, options) {
        this.offlineQueue.push({
            title,
            options,
            timestamp: Date.now()
        });
        
        // Store in localStorage for persistence
        localStorage.setItem('notificationQueue', JSON.stringify(this.offlineQueue));
        
        // Show in-app notification about queuing
        this.showInAppNotification('📱 Notification Queued', {
            body: 'Will be delivered when online',
            type: 'info',
            autoClose: 3000
        });
    }
    
    async processOfflineQueue() {
        if (!navigator.onLine || this.offlineQueue.length === 0) {
            return;
        }
        
        const queue = [...this.offlineQueue];
        this.offlineQueue = [];
        localStorage.removeItem('notificationQueue');
        
        for (const item of queue) {
            // Check if notification is still relevant (not too old)
            const age = Date.now() - item.timestamp;
            if (age < 24 * 60 * 60 * 1000) { // 24 hours
                await this.showNotification(item.title, item.options);
                // Small delay between notifications
                await new Promise(resolve => setTimeout(resolve, 500));
            }
        }
        
        if (queue.length > 0) {
            this.showInAppNotification('📱 Offline Notifications Delivered', {
                body: `${queue.length} notifications delivered`,
                type: 'success',
                autoClose: 3000
            });
        }
    }
    
    setupOfflineHandling() {
        // Load queued notifications from localStorage
        const stored = localStorage.getItem('notificationQueue');
        if (stored) {
            try {
                this.offlineQueue = JSON.parse(stored);
            } catch (error) {
                console.error('Failed to load notification queue:', error);
                localStorage.removeItem('notificationQueue');
            }
        }
        
        // Process queue when coming online
        window.addEventListener('online', () => {
            setTimeout(() => this.processOfflineQueue(), 1000);
        });
        
        // Show offline status
        window.addEventListener('offline', () => {
            this.showInAppNotification('📱 Offline Mode', {
                body: 'Notifications will be queued until online',
                type: 'warning',
                autoClose: 5000
            });
        });
    }
    
    setupPeriodicSync() {
        // Check for updates every 5 minutes when app is active
        setInterval(() => {
            if (document.visibilityState === 'visible' && navigator.onLine) {
                this.checkForUpdates();
            }
        }, 5 * 60 * 1000);
        
        // Check when app becomes visible
        document.addEventListener('visibilitychange', () => {
            if (document.visibilityState === 'visible' && navigator.onLine) {
                this.checkForUpdates();
            }
        });
    }
    
    async checkForUpdates() {
        try {
            // Check for new decisions
            const response = await fetch('/api/notifications/check', {
                method: 'GET',
                headers: {
                    'Content-Type': 'application/json'
                }
            });
            
            if (response.ok) {
                const updates = await response.json();
                
                // Process decision updates
                if (updates.decisions && updates.decisions.length > 0) {
                    for (const decision of updates.decisions) {
                        await this.notifyDecisionUpdate(decision, 'updated');
                    }
                }
                
                // Process collaboration updates
                if (updates.collaborations && updates.collaborations.length > 0) {
                    for (const collaboration of updates.collaborations) {
                        await this.notifyCollaborationUpdate(collaboration);
                    }
                }
            }
        } catch (error) {
            console.error('Failed to check for updates:', error);
        }
    }
    
    // Notification preferences
    loadPreferences() {
        const stored = localStorage.getItem('notificationPreferences');
        if (stored) {
            try {
                return JSON.parse(stored);
            } catch (error) {
                console.error('Failed to load notification preferences:', error);
            }
        }
        
        // Default preferences
        return {
            enabled: true,
            decisions: true,
            collaborations: true,
            system: true,
            sound: true,
            vibration: true,
            quietHours: {
                enabled: false,
                start: '22:00',
                end: '08:00'
            }
        };
    }
    
    savePreferences() {
        localStorage.setItem('notificationPreferences', JSON.stringify(this.preferences));
    }
    
    updatePreferences(newPreferences) {
        this.preferences = { ...this.preferences, ...newPreferences };
        this.savePreferences();
    }
    
    shouldShowNotification(type) {
        if (!this.preferences.enabled) {
            return false;
        }
        
        // Check type-specific preferences
        if (type === 'decision' && !this.preferences.decisions) {
            return false;
        }
        if (type === 'collaboration' && !this.preferences.collaborations) {
            return false;
        }
        if (type === 'system' && !this.preferences.system) {
            return false;
        }
        
        // Check quiet hours
        if (this.preferences.quietHours.enabled) {
            const now = new Date();
            const currentTime = now.getHours() * 100 + now.getMinutes();
            const startTime = this.parseTime(this.preferences.quietHours.start);
            const endTime = this.parseTime(this.preferences.quietHours.end);
            
            if (startTime > endTime) {
                // Quiet hours span midnight
                if (currentTime >= startTime || currentTime <= endTime) {
                    return false;
                }
            } else {
                // Normal quiet hours
                if (currentTime >= startTime && currentTime <= endTime) {
                    return false;
                }
            }
        }
        
        return true;
    }
    
    parseTime(timeString) {
        const [hours, minutes] = timeString.split(':').map(Number);
        return hours * 100 + minutes;
    }
    
    // Service worker message handling
    handleServiceWorkerMessage(data) {
        switch (data.type) {
            case 'notification-click':
                this.handleNotificationClick(data.notification);
                break;
            case 'notification-close':
                this.handleNotificationClose(data.notification);
                break;
            default:
                console.log('Unknown service worker message:', data);
        }
    }
    
    handleNotificationClick(notification) {
        // Bring app to foreground
        if (window.focus) {
            window.focus();
        }
        
        // Handle notification-specific actions
        if (notification.data) {
            const { decisionId, type } = notification.data;
            
            if (decisionId) {
                // Navigate to decision
                if (window.switchAgent) {
                    // Determine agent type from decision
                    // This would need to be enhanced based on your data structure
                    window.switchAgent('ceo'); // Default to CEO
                }
            }
        }
    }
    
    handleNotificationClose(notification) {
        // Handle notification close if needed
        console.log('Notification closed:', notification);
    }
    
    // Public API methods
    async enable() {
        try {
            await this.requestPermission();
            this.preferences.enabled = true;
            this.savePreferences();
            return true;
        } catch (error) {
            console.error('Failed to enable notifications:', error);
            return false;
        }
    }
    
    disable() {
        this.preferences.enabled = false;
        this.savePreferences();
    }
    
    getPreferences() {
        return { ...this.preferences };
    }
    
    clearAllNotifications() {
        // Clear service worker notifications
        if (this.serviceWorkerRegistration) {
            this.serviceWorkerRegistration.getNotifications().then(notifications => {
                notifications.forEach(notification => notification.close());
            });
        }
        
        // Clear in-app notifications
        const inAppNotifications = document.querySelectorAll('.mobile-notification');
        inAppNotifications.forEach(notification => notification.remove());
    }
    
    // Test notification
    async testNotification() {
        return await this.showNotification('🧪 Test Notification', {
            body: 'This is a test notification to verify the system is working.',
            type: 'info',
            autoClose: 5000
        });
    }
}

// Global notification service instance
let mobileNotificationService = null;

// Initialize notification service when DOM is ready
document.addEventListener('DOMContentLoaded', () => {
    if (window.isMobile) {
        mobileNotificationService = new MobileNotificationService();
        
        // Make it globally available
        window.notificationService = mobileNotificationService;
    }
});

// Export for use in other modules
if (typeof module !== 'undefined' && module.exports) {
    module.exports = MobileNotificationService;
}