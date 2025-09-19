"""
Test Mobile Responsive Design Implementation

Tests for mobile-responsive interface features including:
- CSS media queries and responsive breakpoints
- Touch-friendly interface elements
- Mobile navigation functionality
- Responsive layout adaptations
"""

import unittest
import os
import re
from pathlib import Path


class TestMobileResponsiveDesign(unittest.TestCase):
    """Test mobile responsive design implementation"""
    
    def setUp(self):
        """Set up test fixtures"""
        self.static_dir = Path('static')
        self.css_dir = self.static_dir / 'css'
        self.js_dir = self.static_dir / 'js'
        self.templates_dir = Path('templates')
    
    def test_css_files_exist(self):
        """Test that required CSS files exist"""
        required_files = [
            self.css_dir / 'style.css',
            self.css_dir / 'mobile.css'
        ]
        
        for file_path in required_files:
            self.assertTrue(file_path.exists(), f"CSS file {file_path} should exist")
    
    def test_mobile_css_content(self):
        """Test that mobile.css contains required mobile-specific styles"""
        mobile_css_path = self.css_dir / 'mobile.css'
        
        if mobile_css_path.exists():
            with open(mobile_css_path, 'r') as f:
                content = f.read()
            
            # Test for mobile-specific classes
            required_classes = [
                '.mobile-device',
                '.mobile-container',
                '.mobile-card',
                '.mobile-btn',
                '.mobile-form',
                '.mobile-chat-container',
                '.mobile-nav',
                '.touch-friendly'
            ]
            
            for css_class in required_classes:
                self.assertIn(css_class, content, 
                            f"Mobile CSS should contain {css_class} class")
    
    def test_responsive_breakpoints_in_main_css(self):
        """Test that main CSS file contains responsive breakpoints"""
        main_css_path = self.css_dir / 'style.css'
        
        if main_css_path.exists():
            with open(main_css_path, 'r') as f:
                content = f.read()
            
            # Test for media queries
            media_queries = [
                '@media (max-width: 480px)',
                '@media (min-width: 481px) and (max-width: 768px)',
                '@media (min-width: 769px) and (max-width: 1024px)',
                '@media (min-width: 1025px)'
            ]
            
            for query in media_queries:
                self.assertIn(query, content, 
                            f"CSS should contain media query: {query}")
    
    def test_touch_friendly_elements(self):
        """Test that CSS includes touch-friendly element styles"""
        css_files = [
            self.css_dir / 'style.css',
            self.css_dir / 'mobile.css'
        ]
        
        touch_friendly_found = False
        min_height_found = False
        
        for css_file in css_files:
            if css_file.exists():
                with open(css_file, 'r') as f:
                    content = f.read()
                
                if '.touch-friendly' in content:
                    touch_friendly_found = True
                
                if 'min-height: 44px' in content:
                    min_height_found = True
        
        self.assertTrue(touch_friendly_found, 
                       "CSS should include .touch-friendly class")
        self.assertTrue(min_height_found, 
                       "CSS should include minimum touch target size (44px)")
    
    def test_mobile_javascript_functions(self):
        """Test that JavaScript includes mobile-specific functions"""
        js_path = self.js_dir / 'app.js'
        
        if js_path.exists():
            with open(js_path, 'r') as f:
                content = f.read()
            
            # Test for mobile-specific functions
            required_functions = [
                'detectMobile',
                'initializeMobileFeatures',
                'initializeMobileNavigation',
                'initializeTouchGestures',
                'optimizeFormsForMobile',
                'toggleMobileNav'
            ]
            
            for function in required_functions:
                self.assertIn(f'function {function}', content, 
                            f"JavaScript should contain {function} function")
    
    def test_mobile_navigation_implementation(self):
        """Test mobile navigation implementation"""
        js_path = self.js_dir / 'app.js'
        
        if js_path.exists():
            with open(js_path, 'r') as f:
                content = f.read()
            
            # Test for mobile navigation elements
            nav_elements = [
                'mobile-nav',
                'mobile-nav-toggle',
                'mobile-nav-menu',
                'mobile-nav-item'
            ]
            
            for element in nav_elements:
                self.assertIn(element, content, 
                            f"JavaScript should reference {element} class")
    
    def test_touch_gesture_support(self):
        """Test touch gesture support implementation"""
        js_path = self.js_dir / 'app.js'
        
        if js_path.exists():
            with open(js_path, 'r') as f:
                content = f.read()
            
            # Test for touch event handlers
            touch_events = [
                'touchstart',
                'touchend',
                'touchmove'
            ]
            
            for event in touch_events:
                self.assertIn(event, content, 
                            f"JavaScript should handle {event} events")
    
    def test_pull_to_refresh_implementation(self):
        """Test pull-to-refresh functionality"""
        js_path = self.js_dir / 'app.js'
        
        if js_path.exists():
            with open(js_path, 'r') as f:
                content = f.read()
            
            # Test for pull-to-refresh functions
            refresh_functions = [
                'initializePullToRefresh',
                'performRefresh'
            ]
            
            for function in refresh_functions:
                self.assertIn(function, content, 
                            f"JavaScript should contain {function} function")
    
    def test_mobile_voice_enhancements(self):
        """Test mobile voice feature enhancements"""
        js_path = self.js_dir / 'app.js'
        
        if js_path.exists():
            with open(js_path, 'r') as f:
                content = f.read()
            
            # Test for enhanced voice functions
            self.assertIn('enhancedStartVoiceInput', content, 
                         "JavaScript should contain enhanced voice input function")
            self.assertIn('navigator.vibrate', content, 
                         "JavaScript should include haptic feedback support")
    
    def test_responsive_form_optimization(self):
        """Test responsive form optimization"""
        css_files = [
            self.css_dir / 'style.css',
            self.css_dir / 'mobile.css'
        ]
        
        form_optimizations_found = False
        
        for css_file in css_files:
            if css_file.exists():
                with open(css_file, 'r') as f:
                    content = f.read()
                
                # Test for form optimizations
                if ('font-size: 16px' in content and 
                    'mobile-form' in content):
                    form_optimizations_found = True
                    break
        
        self.assertTrue(form_optimizations_found, 
                       "CSS should include mobile form optimizations")
    
    def test_mobile_chat_optimization(self):
        """Test mobile chat interface optimization"""
        css_files = [
            self.css_dir / 'mobile.css'
        ]
        
        for css_file in css_files:
            if css_file.exists():
                with open(css_file, 'r') as f:
                    content = f.read()
                
                # Test for mobile chat classes
                chat_classes = [
                    '.mobile-chat-container',
                    '.mobile-chat-messages',
                    '.mobile-chat-input'
                ]
                
                for chat_class in chat_classes:
                    self.assertIn(chat_class, content, 
                                f"Mobile CSS should contain {chat_class}")
    
    def test_accessibility_features(self):
        """Test mobile accessibility features"""
        css_files = [
            self.css_dir / 'style.css',
            self.css_dir / 'mobile.css'
        ]
        
        accessibility_found = False
        
        for css_file in css_files:
            if css_file.exists():
                with open(css_file, 'r') as f:
                    content = f.read()
                
                # Test for accessibility features
                if ('outline:' in content and 
                    'focus' in content):
                    accessibility_found = True
                    break
        
        self.assertTrue(accessibility_found, 
                       "CSS should include accessibility features")
    
    def test_dark_mode_support(self):
        """Test dark mode support for mobile"""
        mobile_css_path = self.css_dir / 'mobile.css'
        
        if mobile_css_path.exists():
            with open(mobile_css_path, 'r') as f:
                content = f.read()
            
            # Test for dark mode media query
            self.assertIn('prefers-color-scheme: dark', content, 
                         "Mobile CSS should include dark mode support")
    
    def test_orientation_handling(self):
        """Test orientation change handling"""
        js_path = self.js_dir / 'app.js'
        mobile_css_path = self.css_dir / 'mobile.css'
        
        # Test JavaScript orientation handling
        if js_path.exists():
            with open(js_path, 'r') as f:
                js_content = f.read()
            
            self.assertIn('orientationchange', js_content, 
                         "JavaScript should handle orientation changes")
        
        # Test CSS orientation media queries
        if mobile_css_path.exists():
            with open(mobile_css_path, 'r') as f:
                css_content = f.read()
            
            self.assertIn('orientation: landscape', css_content, 
                         "CSS should include landscape orientation styles")
    
    def test_high_dpi_support(self):
        """Test high DPI display support"""
        mobile_css_path = self.css_dir / 'mobile.css'
        
        if mobile_css_path.exists():
            with open(mobile_css_path, 'r') as f:
                content = f.read()
            
            # Test for high DPI media queries
            high_dpi_queries = [
                '-webkit-min-device-pixel-ratio: 2',
                'min-resolution: 192dpi'
            ]
            
            for query in high_dpi_queries:
                self.assertIn(query, content, 
                            f"CSS should include high DPI query: {query}")


class TestMobileResponsiveIntegration(unittest.TestCase):
    """Test mobile responsive design integration"""
    
    def test_css_integration(self):
        """Test that mobile CSS is properly integrated"""
        # This would typically test that mobile.css is included in templates
        # For now, we'll test that the file exists and has content
        mobile_css_path = Path('static/css/mobile.css')
        
        if mobile_css_path.exists():
            with open(mobile_css_path, 'r') as f:
                content = f.read()
            
            self.assertGreater(len(content), 1000, 
                             "Mobile CSS should have substantial content")
    
    def test_javascript_integration(self):
        """Test that mobile JavaScript functions are integrated"""
        js_path = Path('static/js/app.js')
        
        if js_path.exists():
            with open(js_path, 'r') as f:
                content = f.read()
            
            # Test that mobile functions are called in initialization
            self.assertIn('initializeMobileFeatures', content, 
                         "Mobile features should be initialized")
            self.assertIn('detectMobile', content, 
                         "Mobile detection should be implemented")


if __name__ == '__main__':
    unittest.main()