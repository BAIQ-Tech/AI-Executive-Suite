/**
 * AI Quality Feedback Form JavaScript
 */

class FeedbackForm {
    constructor() {
        this.form = document.getElementById('feedback-form');
        this.resultDiv = document.getElementById('feedback-result');
        
        this.init();
    }
    
    init() {
        this.setupEventListeners();
    }
    
    setupEventListeners() {
        this.form.addEventListener('submit', (e) => {
            e.preventDefault();
            this.submitFeedback();
        });
        
        // Add visual feedback for rating selection
        const ratingInputs = document.querySelectorAll('input[name="rating"]');
        ratingInputs.forEach(input => {
            input.addEventListener('change', (e) => {
                this.updateRatingVisual(e.target);
            });
        });
        
        const accuracyInputs = document.querySelectorAll('input[name="accuracy_rating"]');
        accuracyInputs.forEach(input => {
            input.addEventListener('change', (e) => {
                this.updateAccuracyVisual(e.target);
            });
        });
    }
    
    updateRatingVisual(selectedInput) {
        const ratingOptions = document.querySelectorAll('.rating-option');
        ratingOptions.forEach(option => {
            option.classList.remove('selected');
        });
        selectedInput.closest('.rating-option').classList.add('selected');
    }
    
    updateAccuracyVisual(selectedInput) {
        const accuracyOptions = document.querySelectorAll('.accuracy-option');
        accuracyOptions.forEach(option => {
            option.classList.remove('selected');
        });
        selectedInput.closest('.accuracy-option').classList.add('selected');
    }
    
    async submitFeedback() {
        const formData = new FormData(this.form);
        const decisionId = document.getElementById('decision-id').value;
        
        // Get executive type from URL or form (you might need to pass this)
        const executiveType = this.getExecutiveTypeFromContext();
        
        const feedbackData = {
            decision_id: decisionId,
            executive_type: executiveType,
            rating: formData.get('rating'),
            accuracy_rating: formData.get('accuracy_rating'),
            feedback_text: formData.get('feedback_text'),
            response_time: this.getResponseTime()
        };
        
        try {
            const response = await fetch('/ai-quality/api/feedback', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify(feedbackData)
            });
            
            const result = await response.json();
            
            if (result.success) {
                this.showSuccess();
            } else {
                this.showError(result.error);
            }
        } catch (error) {
            console.error('Error submitting feedback:', error);
            this.showError('Failed to submit feedback. Please try again.');
        }
    }
    
    getExecutiveTypeFromContext() {
        // Try to get executive type from URL parameters or page context
        const urlParams = new URLSearchParams(window.location.search);
        return urlParams.get('executive_type') || 'ceo'; // Default to CEO
    }
    
    getResponseTime() {
        // Try to get response time from page context or calculate from page load
        const urlParams = new URLSearchParams(window.location.search);
        return parseFloat(urlParams.get('response_time')) || 0.0;
    }
    
    showSuccess() {
        this.form.style.display = 'none';
        this.resultDiv.style.display = 'block';
    }
    
    showError(message) {
        alert(`Error: ${message}`);
    }
}

// Initialize feedback form when DOM is loaded
document.addEventListener('DOMContentLoaded', () => {
    new FeedbackForm();
});

// Add CSS for selected states
const style = document.createElement('style');
style.textContent = `
    .rating-option.selected {
        border-color: #007bff !important;
        background-color: #e3f2fd !important;
    }
    
    .accuracy-option.selected {
        border-color: #28a745 !important;
        background-color: #e8f5e8 !important;
    }
`;
document.head.appendChild(style);