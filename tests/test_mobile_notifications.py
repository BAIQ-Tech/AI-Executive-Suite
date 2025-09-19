"""
Test Mobile Notifications Implementation

Tests for mobile notification features including:
- Push notification system
- Offline sync and notification queuing
- Notification preferences and customization
- Service worker integration
"""

import unittest
import os
import re
from pathlib import Path


class TestMobileNotifications(unittest.TestCase):
    """Test mobile notification implementation"""
    
    def setUp(self):
        """Set up test fixtures"""
        self.static_dir = Path('static')
        self.js_dir = self.static_dir / 'js'
        self.templates_dir = Path('templates')
        self.notification_js_path = self.js_dir / 'mobile-notifications.js'
        self.service_worker_path = self.static_dir / 'sw.js'
        self.settings_template_path = self.templates_dir / 'mobile_notifications.html'
    
    def test_notification_service_file_exists(self):
        """Test that notification service file exists"""
        self.assertTrue(self.notification_js_path.exists(), 
                       "Mobile notifications JavaScript file should exist")
    
    def test_service_worker_exists(self):
        """Test that service worker file exists"""
        self.assertTrue(self.service_worker_path.exists(), 
                       "Service worker file should exist")
    
    def test_notification_settings_template_exists(self):
        """Test that notification settings template exists"""
        self.assertTrue(self.settings_template_path.exists(), 
                       "Notification settings template should exist")
    
    def test_notification_service_class(self):
        """Test that MobileNotificationService class is implemented"""
        if not self.notification_js_path.exists():
            self.skipTest("Notification service file not found")
        
        with open(self.notification_js_path, 'r') as f:
            content = f.read()
        
        # Test for class definition
        self.assertIn('class MobileNotificationService', content, 
                     "MobileNotificationService class should be defined")
        
        # Test for essential methods
        essential_methods = [
            'constructor',
            'init',
            'requestPermission',
            'showNotification',
            'notifyDecisionUpdate',
            'queueOfflineNotification',
            'processOfflineQueue'
        ]
        
        for method in essential_methods:
            self.assertIn(method, content, 
                         f"MobileNotificationService should have {method} method")
    
    def test_push_notification_support(self):
        """Test push notification support implementation"""
        if not self.notification_js_path.exists():
            self.skipTest("Notification service file not found")
        
        with open(self.notification_js_path, 'r') as f:
            content = f.read()
        
        # Test for push notification features
        push_features = [
            'Notification',
            'serviceWorker',
            'showNotification',
            'requestPermission'
        ]
        
        for feature in push_features:
            self.assertIn(feature, content, 
                         f"Push notification support should include {feature}")
    
    def test_offline_notification_queuing(self):
        """Test offline notification queuing functionality"""
        if not self.notification_js_path.exists():
            self.skipTest("Notification service file not found")
        
        with open(self.notification_js_path, 'r') as f:
            content = f.read()
        
        # Test for offline queuing features
        offline_features = [
            'offlineQueue',
            'queueOfflineNotification',
            'processOfflineQueue',
            'navigator.onLine',
            'localStorage'
        ]
        
        for feature in offline_features:
            self.assertIn(feature, content, 
                         f"Offline queuing should include {feature}")
    
    def test_notification_preferences(self):
        """Test notification preferences management"""
        if not self.notification_js_path.exists():
            self.skipTest("Notification service file not found")
        
        with open(self.notification_js_path, 'r') as f:
            content = f.read()
        
        # Test for preference management
        preference_features = [
            'loadPreferences',
            'savePreferences',
            'updatePreferences',
            'shouldShowNotification',
            'quietHours'
        ]
        
        for feature in preference_features:
            self.assertIn(feature, content, 
                         f"Preference management should include {feature}")
    
    def test_decision_notifications(self):
        """Test decision-specific notification functionality"""
        if not self.notification_js_path.exists():
            self.skipTest("Notification service file not found")
        
        with open(self.notification_js_path, 'r') as f:
            content = f.read()
        
        # Test for decision notification methods
        decision_methods = [
            'notifyDecisionUpdate',
            'notifyCollaborationUpdate',
            'notifySystemUpdate'
        ]
        
        for method in decision_methods:
            self.assertIn(method, content, 
                         f"Decision notifications should include {method}")
    
    def test_service_worker_implementation(self):
        """Test service worker implementation"""
        if not self.service_worker_path.exists():
            self.skipTest("Service worker file not found")
        
        with open(self.service_worker_path, 'r') as f:
            content = f.read()
        
        # Test for service worker event handlers
        sw_events = [
            'install',
            'activate',
            'fetch',
            'push',
            'notificationclick',
            'notificationclose'
        ]
        
        for event in sw_events:
            self.assertIn(f"addEventListener('{event}'", content, 
                         f"Service worker should handle {event} event")
    
    def test_background_sync(self):
        """Test background sync functionality"""
        if not self.service_worker_path.exists():
            self.skipTest("Service worker file not found")
        
        with open(self.service_worker_path, 'r') as f:
            content = f.read()
        
        # Test for background sync features
        sync_features = [
            'sync',
            'syncNotifications',
            'periodicsync'
        ]
        
        for feature in sync_features:
            self.assertIn(feature, content, 
                         f"Background sync should include {feature}")
    
    def test_notification_actions(self):
        """Test notification action handling"""
        if not self.service_worker_path.exists():
            self.skipTest("Service worker file not found")
        
        with open(self.service_worker_path, 'r') as f:
            content = f.read()
        
        # Test for notification actions
        self.assertIn('actions', content, 
                     "Service worker should support notification actions")
        self.assertIn('event.action', content, 
                     "Service worker should handle action events")
    
    def test_notification_settings_ui(self):
        """Test notification settings UI implementation"""
        if not self.settings_template_path.exists():
            self.skipTest("Notification settings template not found")
        
        with open(self.settings_template_path, 'r') as f:
            content = f.read()
        
        # Test for settings UI elements
        ui_elements = [
            'toggle-switch',
            'permission-status',
            'test-notification',
            'quiet-hours',
            'notification-types'
        ]
        
        for element in ui_elements:
            self.assertIn(element, content, 
                         f"Settings UI should include {element}")
    
    def test_permission_handling(self):
        """Test notification permission handling"""
        if not self.notification_js_path.exists():
            self.skipTest("Notification service file not found")
        
        with open(self.notification_js_path, 'r') as f:
            content = f.read()
        
        # Test for permission states
        permission_states = [
            'granted',
            'denied',
            'default'
        ]
        
        for state in permission_states:
            self.assertIn(f"'{state}'", content, 
                         f"Permission handling should include {state} state")
    
    def test_in_app_notifications(self):
        """Test in-app notification fallback"""
        if not self.notification_js_path.exists():
            self.skipTest("Notification service file not found")
        
        with open(self.notification_js_path, 'r') as f:
            content = f.read()
        
        # Test for in-app notification features
        self.assertIn('showInAppNotification', content, 
                     "Should have in-app notification fallback")
        self.assertIn('mobile-notification', content, 
                     "Should create in-app notification elements")
    
    def test_notification_types(self):
        """Test different notification types"""
        if not self.notification_js_path.exists():
            self.skipTest("Notification service file not found")
        
        with open(self.notification_js_path, 'r') as f:
            content = f.read()
        
        # Test for notification types
        notification_types = [
            'success',
            'error',
            'warning',
            'info',
            'decision'
        ]
        
        for ntype in notification_types:
            self.assertIn(f"'{ntype}'", content, 
                         f"Should support {ntype} notification type")
    
    def test_quiet_hours_functionality(self):
        """Test quiet hours functionality"""
        if not self.notification_js_path.exists():
            self.skipTest("Notification service file not found")
        
        with open(self.notification_js_path, 'r') as f:
            content = f.read()
        
        # Test for quiet hours features
        quiet_features = [
            'quietHours',
            'parseTime',
            'shouldShowNotification'
        ]
        
        for feature in quiet_features:
            self.assertIn(feature, content, 
                         f"Quiet hours should include {feature}")
    
    def test_notification_customization(self):
        """Test notification customization options"""
        if not self.notification_js_path.exists():
            self.skipTest("Notification service file not found")
        
        with open(self.notification_js_path, 'r') as f:
            content = f.read()
        
        # Test for customization features
        custom_features = [
            'icon',
            'badge',
            'vibrate',
            'requireInteraction',
            'autoClose'
        ]
        
        for feature in custom_features:
            self.assertIn(feature, content, 
                         f"Notification customization should include {feature}")


class TestNotificationIntegration(unittest.TestCase):
    """Test notification integration with main application"""
    
    def test_app_js_integration(self):
        """Test that notifications are integrated with main app"""
        app_js_path = Path('static/js/app.js')
        
        if not app_js_path.exists():
            self.skipTest("app.js file not found")
        
        with open(app_js_path, 'r') as f:
            content = f.read()
        
        # Test for notification integration
        integration_features = [
            'initializeNotifications',
            'notificationService',
            'askCEOWithNotifications',
            'askCTOWithNotifications',
            'askCFOWithNotifications'
        ]
        
        for feature in integration_features:
            self.assertIn(feature, content, 
                         f"App integration should include {feature}")
    
    def test_mobile_nav_integration(self):
        """Test notification settings in mobile navigation"""
        app_js_path = Path('static/js/app.js')
        
        if not app_js_path.exists():
            self.skipTest("app.js file not found")
        
        with open(app_js_path, 'r') as f:
            content = f.read()
        
        # Test for navigation integration
        self.assertIn('addNotificationSettingsToNav', content, 
                     "Should add notification settings to mobile nav")
        self.assertIn('mobile-notifications', content, 
                     "Should link to notification settings page")
    
    def test_app_route_exists(self):
        """Test that notification settings route exists"""
        app_py_path = Path('app.py')
        
        if not app_py_path.exists():
            self.skipTest("app.py file not found")
        
        with open(app_py_path, 'r') as f:
            content = f.read()
        
        # Test for route definition
        self.assertIn('/mobile-notifications', content, 
                     "Should have mobile notifications route")
        self.assertIn('mobile_notifications.html', content, 
                     "Should render notification settings template")


if __name__ == '__main__':
    unittest.main()