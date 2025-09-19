"""
Test Mobile Voice Features Implementation

Tests for enhanced mobile voice features including:
- Improved speech-to-text integration
- Text-to-speech for AI responses
- Offline voice command caching
- Voice command shortcuts
"""

import unittest
import os
import re
from pathlib import Path


class TestMobileVoiceFeatures(unittest.TestCase):
    """Test mobile voice features implementation"""
    
    def setUp(self):
        """Set up test fixtures"""
        self.js_dir = Path('static/js')
        self.app_js_path = self.js_dir / 'app.js'
    
    def test_enhanced_voice_functions_exist(self):
        """Test that enhanced voice functions are implemented"""
        if not self.app_js_path.exists():
            self.skipTest("app.js file not found")
        
        with open(self.app_js_path, 'r') as f:
            content = f.read()
        
        # Test for enhanced voice functions
        enhanced_functions = [
            'initializeEnhancedVoice',
            'enhancedStartVoiceInput',
            'handleEnhancedVoiceInput',
            'enhancedSpeakResponse',
            'initializeEnhancedTTS'
        ]
        
        for function in enhanced_functions:
            self.assertIn(f'function {function}', content, 
                         f"Enhanced voice function {function} should exist")
    
    def test_speech_recognition_enhancements(self):
        """Test speech recognition enhancements for mobile"""
        if not self.app_js_path.exists():
            self.skipTest("app.js file not found")
        
        with open(self.app_js_path, 'r') as f:
            content = f.read()
        
        # Test for mobile-specific speech recognition features
        features = [
            'interimResults = true',
            'maxAlternatives = 3',
            'confidence',
            'haptic feedback',
            'navigator.vibrate'
        ]
        
        for feature in features:
            self.assertIn(feature, content, 
                         f"Speech recognition should include {feature}")
    
    def test_text_to_speech_enhancements(self):
        """Test text-to-speech enhancements for mobile"""
        if not self.app_js_path.exists():
            self.skipTest("app.js file not found")
        
        with open(self.app_js_path, 'r') as f:
            content = f.read()
        
        # Test for TTS enhancements
        tts_features = [
            'cleanTextForSpeech',
            'selectBestVoice',
            'speakInChunks',
            'loadVoicesWithRetry'
        ]
        
        for feature in tts_features:
            self.assertIn(feature, content, 
                         f"TTS should include {feature} function")
    
    def test_voice_command_shortcuts(self):
        """Test voice command shortcuts implementation"""
        if not self.app_js_path.exists():
            self.skipTest("app.js file not found")
        
        with open(self.app_js_path, 'r') as f:
            content = f.read()
        
        # Test for voice commands
        self.assertIn('voiceCommands', content, 
                     "Voice commands object should exist")
        
        # Test for specific commands
        commands = [
            'clear',
            'switch to ceo',
            'switch to cto',
            'switch to cfo',
            'dashboard',
            'help',
            'stop'
        ]
        
        for command in commands:
            self.assertIn(f"'{command}'", content, 
                         f"Voice command '{command}' should be implemented")
    
    def test_offline_voice_caching(self):
        """Test offline voice command caching"""
        if not self.app_js_path.exists():
            self.skipTest("app.js file not found")
        
        with open(self.app_js_path, 'r') as f:
            content = f.read()
        
        # Test for offline caching features
        offline_features = [
            'offlineVoiceCache',
            'cacheVoiceCommand',
            'processOfflineVoiceCache',
            'navigator.onLine'
        ]
        
        for feature in offline_features:
            self.assertIn(feature, content, 
                         f"Offline voice caching should include {feature}")
    
    def test_confidence_scoring(self):
        """Test confidence scoring for voice recognition"""
        if not self.app_js_path.exists():
            self.skipTest("app.js file not found")
        
        with open(self.app_js_path, 'r') as f:
            content = f.read()
        
        # Test for confidence-based features
        confidence_features = [
            'confidence',
            'showConfirmationDialog',
            'confirmVoiceInput',
            'retryVoiceInput'
        ]
        
        for feature in confidence_features:
            self.assertIn(feature, content, 
                         f"Confidence scoring should include {feature}")
    
    def test_haptic_feedback_support(self):
        """Test haptic feedback support for mobile"""
        if not self.app_js_path.exists():
            self.skipTest("app.js file not found")
        
        with open(self.app_js_path, 'r') as f:
            content = f.read()
        
        # Test for haptic feedback
        self.assertIn('navigator.vibrate', content, 
                     "Haptic feedback should be implemented")
        
        # Test for different vibration patterns
        vibration_patterns = [
            'vibrate(50)',
            'vibrate(100)',
            'vibrate(200)',
            'vibrate([100, 50, 100])',
            'vibrate([50, 50, 50])'
        ]
        
        vibration_found = False
        for pattern in vibration_patterns:
            if pattern in content:
                vibration_found = True
                break
        
        self.assertTrue(vibration_found, 
                       "At least one vibration pattern should be implemented")
    
    def test_language_support(self):
        """Test multi-language support for voice features"""
        if not self.app_js_path.exists():
            self.skipTest("app.js file not found")
        
        with open(self.app_js_path, 'r') as f:
            content = f.read()
        
        # Test for language mapping
        self.assertIn('updateVoiceRecognitionLanguage', content, 
                     "Voice recognition language update should exist")
        
        # Test for language codes
        language_codes = ['en-US', 'ja-JP', 'zh-CN']
        for code in language_codes:
            self.assertIn(code, content, 
                         f"Language code {code} should be supported")
    
    def test_error_handling(self):
        """Test error handling for voice features"""
        if not self.app_js_path.exists():
            self.skipTest("app.js file not found")
        
        with open(self.app_js_path, 'r') as f:
            content = f.read()
        
        # Test for error handling
        error_cases = [
            'no-speech',
            'audio-capture',
            'not-allowed',
            'network'
        ]
        
        for error_case in error_cases:
            self.assertIn(error_case, content, 
                         f"Error case '{error_case}' should be handled")
    
    def test_voice_ui_feedback(self):
        """Test voice UI feedback features"""
        if not self.app_js_path.exists():
            self.skipTest("app.js file not found")
        
        with open(self.app_js_path, 'r') as f:
            content = f.read()
        
        # Test for UI feedback functions
        ui_functions = [
            'resetVoiceButton',
            'showMobileAlert',
            'showConfirmationDialog',
            'speaking-indicator'
        ]
        
        for function in ui_functions:
            self.assertIn(function, content, 
                         f"Voice UI feedback should include {function}")
    
    def test_agent_specific_voices(self):
        """Test agent-specific voice selection"""
        if not self.app_js_path.exists():
            self.skipTest("app.js file not found")
        
        with open(self.app_js_path, 'r') as f:
            content = f.read()
        
        # Test for agent-specific voice selection
        self.assertIn('getAgentPitch', content, 
                     "Agent-specific pitch should be implemented")
        
        # Test for voice selection logic
        agents = ['ceo', 'cto', 'cfo']
        for agent in agents:
            self.assertIn(f"case '{agent}'", content, 
                         f"Voice selection for {agent} should exist")
    
    def test_speech_chunking(self):
        """Test speech chunking for long text"""
        if not self.app_js_path.exists():
            self.skipTest("app.js file not found")
        
        with open(self.app_js_path, 'r') as f:
            content = f.read()
        
        # Test for speech chunking
        self.assertIn('speakInChunks', content, 
                     "Speech chunking should be implemented")
        
        # Test for chunk processing
        chunk_features = [
            'chunks.length',
            'speakNextChunk',
            'chunkIndex'
        ]
        
        for feature in chunk_features:
            self.assertIn(feature, content, 
                         f"Speech chunking should include {feature}")


class TestVoiceIntegration(unittest.TestCase):
    """Test voice feature integration with mobile interface"""
    
    def test_mobile_voice_initialization(self):
        """Test that mobile voice features are properly initialized"""
        app_js_path = Path('static/js/app.js')
        
        if not app_js_path.exists():
            self.skipTest("app.js file not found")
        
        with open(app_js_path, 'r') as f:
            content = f.read()
        
        # Test that enhanced voice is used for mobile
        self.assertIn('if (isMobile)', content, 
                     "Mobile detection should trigger enhanced voice")
        self.assertIn('initializeEnhancedVoice', content, 
                     "Enhanced voice should be initialized for mobile")
    
    def test_voice_button_enhancements(self):
        """Test voice button enhancements for mobile"""
        app_js_path = Path('static/js/app.js')
        
        if not app_js_path.exists():
            self.skipTest("app.js file not found")
        
        with open(app_js_path, 'r') as f:
            content = f.read()
        
        # Test for button state management
        button_features = [
            'recording',
            'resetVoiceButton',
            'voice-input-btn'
        ]
        
        for feature in button_features:
            self.assertIn(feature, content, 
                         f"Voice button should include {feature}")


if __name__ == '__main__':
    unittest.main()