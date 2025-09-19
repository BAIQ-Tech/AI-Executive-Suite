/**
 * Personality Configuration JavaScript
 * Handles the personality profile management interface
 */

class PersonalityConfig {
    constructor() {
        this.currentTab = 'profiles';
        this.profiles = [];
        this.publicProfiles = [];
        this.sharedProfiles = [];
        this.expertiseDomains = [];
        this.currentProfileId = null;
        
        this.init();
    }
    
    init() {
        this.setupEventListeners();
        this.setupSliders();
        this.setupTagInput();
        this.loadProfiles();
        this.loadConfigurationOptions();
    }
    
    setupEventListeners() {
        // Tab navigation
        document.querySelectorAll('.nav-btn').forEach(btn => {
            btn.addEventListener('click', (e) => {
                this.switchTab(e.target.dataset.tab);
            });
        });
        
        // Profile form submission
        document.getElementById('profile-form').addEventListener('submit', (e) => {
            e.preventDefault();
            this.createProfile();
        });
        
        // Filter controls
        document.getElementById('executive-type-filter').addEventListener('change', () => {
            this.filterProfiles();
        });
        
        document.getElementById('refresh-profiles').addEventListener('click', () => {
            this.loadProfiles();
        });
        
        // Public library filters
        document.getElementById('public-executive-filter').addEventListener('change', () => {
            this.filterPublicProfiles();
        });
        
        document.getElementById('public-industry-filter').addEventListener('change', () => {
            this.filterPublicProfiles();
        });
        
        // Test profile button
        document.getElementById('test-profile').addEventListener('click', () => {
            this.testCurrentProfile();
        });
        
        // Modal controls
        document.querySelectorAll('.modal-close').forEach(btn => {
            btn.addEventListener('click', () => {
                this.closeModal();
            });
        });
        
        document.getElementById('run-test').addEventListener('click', () => {
            this.runProfileTest();
        });
        
        // Executive type change handler
        document.getElementById('executive-type').addEventListener('change', (e) => {
            this.updateExpertiseDomains(e.target.value);
        });
    }
    
    setupSliders() {
        // Setup all range sliders to update their value displays
        document.querySelectorAll('input[type="range"]').forEach(slider => {
            const valueDisplay = slider.parentElement.querySelector('.slider-value');
            
            slider.addEventListener('input', (e) => {
                valueDisplay.textContent = e.target.value;
            });
        });
    }
    
    setupTagInput() {
        const expertiseInput = document.getElementById('expertise-input');
        const tagsContainer = document.getElementById('expertise-tags');
        
        expertiseInput.addEventListener('keypress', (e) => {
            if (e.key === 'Enter' || e.key === ',') {
                e.preventDefault();
                this.addExpertiseDomain(expertiseInput.value.trim());
                expertiseInput.value = '';
            }
        });
        
        expertiseInput.addEventListener('blur', () => {
            if (expertiseInput.value.trim()) {
                this.addExpertiseDomain(expertiseInput.value.trim());
                expertiseInput.value = '';
            }
        });
    }
    
    switchTab(tabName) {
        // Update navigation
        document.querySelectorAll('.nav-btn').forEach(btn => {
            btn.classList.remove('active');
        });
        document.querySelector(`[data-tab="${tabName}"]`).classList.add('active');
        
        // Update content
        document.querySelectorAll('.tab-content').forEach(content => {
            content.classList.remove('active');
        });
        document.getElementById(`${tabName}-tab`).classList.add('active');
        
        this.currentTab = tabName;
        
        // Load data for the tab
        switch (tabName) {
            case 'profiles':
                this.loadProfiles();
                break;
            case 'public':
                this.loadPublicProfiles();
                break;
            case 'shared':
                this.loadSharedProfiles();
                break;
        }
    }
    
    async loadProfiles() {
        try {
            const response = await fetch('/api/personality/profiles');
            const data = await response.json();
            
            if (data.success) {
                this.profiles = data.profiles;
                this.renderProfiles();
            } else {
                this.showMessage('Error loading profiles: ' + data.error, 'error');
            }
        } catch (error) {
            console.error('Error loading profiles:', error);
            this.showMessage('Failed to load profiles', 'error');
        }
    }
    
    async loadPublicProfiles() {
        try {
            const response = await fetch('/api/personality/profiles/public');
            const data = await response.json();
            
            if (data.success) {
                this.publicProfiles = data.profiles;
                this.renderPublicProfiles();
            } else {
                this.showMessage('Error loading public profiles: ' + data.error, 'error');
            }
        } catch (error) {
            console.error('Error loading public profiles:', error);
            this.showMessage('Failed to load public profiles', 'error');
        }
    }
    
    async loadSharedProfiles() {
        try {
            const response = await fetch('/api/personality/profiles/shared');
            const data = await response.json();
            
            if (data.success) {
                this.sharedProfiles = data.shares;
                this.renderSharedProfiles();
            } else {
                this.showMessage('Error loading shared profiles: ' + data.error, 'error');
            }
        } catch (error) {
            console.error('Error loading shared profiles:', error);
            this.showMessage('Failed to load shared profiles', 'error');
        }
    }
    
    async loadConfigurationOptions() {
        try {
            const response = await fetch('/api/personality/config/options');
            const data = await response.json();
            
            if (data.success) {
                this.configOptions = data.options;
            }
        } catch (error) {
            console.error('Error loading configuration options:', error);
        }
    }
    
    renderProfiles() {
        const grid = document.getElementById('profiles-grid');
        const filter = document.getElementById('executive-type-filter').value;
        
        let filteredProfiles = this.profiles;
        if (filter) {
            filteredProfiles = this.profiles.filter(p => p.executive_type === filter);
        }
        
        if (filteredProfiles.length === 0) {
            grid.innerHTML = '<div class="loading">No profiles found</div>';
            return;
        }
        
        grid.innerHTML = filteredProfiles.map(profile => this.createProfileCard(profile, true)).join('');
        this.attachProfileCardEvents();
    }
    
    renderPublicProfiles() {
        const grid = document.getElementById('public-profiles-grid');
        
        if (this.publicProfiles.length === 0) {
            grid.innerHTML = '<div class="loading">No public profiles available</div>';
            return;
        }
        
        grid.innerHTML = this.publicProfiles.map(profile => this.createProfileCard(profile, false)).join('');
        this.attachPublicProfileEvents();
    }
    
    renderSharedProfiles() {
        const grid = document.getElementById('shared-profiles-grid');
        
        if (this.sharedProfiles.length === 0) {
            grid.innerHTML = '<div class="loading">No profiles shared with you</div>';
            return;
        }
        
        grid.innerHTML = this.sharedProfiles.map(share => 
            this.createProfileCard(share.profile, false, share)
        ).join('');
        this.attachSharedProfileEvents();
    }
    
    createProfileCard(profile, isOwned = false, shareInfo = null) {
        const usageText = profile.usage_count > 0 ? `${profile.usage_count} uses` : 'New';
        const defaultBadge = profile.is_default ? '<span class="badge badge-success">Default</span>' : '';
        const publicBadge = profile.is_public ? '<span class="badge badge-info">Public</span>' : '';
        
        return `
            <div class="profile-card" data-profile-id="${profile.id}">
                <div class="profile-header">
                    <h3 class="profile-name">${profile.name} ${defaultBadge} ${publicBadge}</h3>
                    <span class="profile-type">${profile.executive_type.toUpperCase()}</span>
                </div>
                <div class="profile-info">
                    <p class="profile-description">${profile.description || 'No description'}</p>
                    <div class="profile-meta">
                        <span class="industry">${profile.industry_specialization}</span>
                        <span class="experience">${profile.experience_level}</span>
                        <span class="usage-count">${usageText}</span>
                    </div>
                    ${shareInfo ? `<div class="share-info">Shared by: ${shareInfo.sharer.name}</div>` : ''}
                </div>
                <div class="profile-actions">
                    <button class="btn btn-sm btn-secondary test-btn">Test</button>
                    <button class="btn btn-sm btn-secondary clone-btn">Clone</button>
                    ${isOwned ? `
                        <button class="btn btn-sm btn-primary edit-btn">Edit</button>
                        <button class="btn btn-sm btn-secondary share-btn">Share</button>
                        <button class="btn btn-sm btn-danger delete-btn">Delete</button>
                    ` : ''}
                </div>
            </div>
        `;
    }
    
    attachProfileCardEvents() {
        document.querySelectorAll('.profile-card').forEach(card => {
            const profileId = card.dataset.profileId;
            
            card.querySelector('.test-btn').addEventListener('click', () => {
                this.testProfile(profileId);
            });
            
            card.querySelector('.clone-btn').addEventListener('click', () => {
                this.cloneProfile(profileId);
            });
            
            const editBtn = card.querySelector('.edit-btn');
            if (editBtn) {
                editBtn.addEventListener('click', () => {
                    this.editProfile(profileId);
                });
            }
            
            const shareBtn = card.querySelector('.share-btn');
            if (shareBtn) {
                shareBtn.addEventListener('click', () => {
                    this.shareProfile(profileId);
                });
            }
            
            const deleteBtn = card.querySelector('.delete-btn');
            if (deleteBtn) {
                deleteBtn.addEventListener('click', () => {
                    this.deleteProfile(profileId);
                });
            }
        });
    }
    
    attachPublicProfileEvents() {
        document.querySelectorAll('.profile-card').forEach(card => {
            const profileId = card.dataset.profileId;
            
            card.querySelector('.test-btn').addEventListener('click', () => {
                this.testProfile(profileId);
            });
            
            card.querySelector('.clone-btn').addEventListener('click', () => {
                this.cloneProfile(profileId);
            });
        });
    }
    
    attachSharedProfileEvents() {
        document.querySelectorAll('.profile-card').forEach(card => {
            const profileId = card.dataset.profileId;
            
            card.querySelector('.test-btn').addEventListener('click', () => {
                this.testProfile(profileId);
            });
            
            card.querySelector('.clone-btn').addEventListener('click', () => {
                this.cloneProfile(profileId);
            });
        });
    }
    
    async createProfile() {
        try {
            const formData = this.getFormData();
            
            const response = await fetch('/api/personality/profiles', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify(formData)
            });
            
            const data = await response.json();
            
            if (data.success) {
                this.showMessage('Profile created successfully!', 'success');
                this.resetForm();
                this.switchTab('profiles');
            } else {
                if (data.errors) {
                    this.showMessage('Validation errors: ' + data.errors.join(', '), 'error');
                } else {
                    this.showMessage('Error creating profile: ' + data.error, 'error');
                }
            }
        } catch (error) {
            console.error('Error creating profile:', error);
            this.showMessage('Failed to create profile', 'error');
        }
    }
    
    async testProfile(profileId) {
        this.currentProfileId = profileId;
        document.getElementById('test-modal').classList.add('show');
    }
    
    async runProfileTest() {
        try {
            const scenario = document.getElementById('test-scenario').value;
            
            const response = await fetch(`/api/personality/profiles/${this.currentProfileId}/test`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({ scenario })
            });
            
            const data = await response.json();
            
            if (data.success) {
                const resultsDiv = document.getElementById('test-results');
                const responseDiv = document.getElementById('test-response');
                
                responseDiv.innerHTML = `
                    <div class="test-scenario">
                        <strong>Scenario:</strong> ${data.test_result.scenario}
                    </div>
                    <div class="test-response">
                        <strong>Response:</strong> ${data.test_result.sample_response}
                    </div>
                    <div class="personality-influence">
                        <strong>Personality Influence:</strong>
                        <ul>
                            <li>Communication Style: ${data.test_result.personality_influence.communication_style}</li>
                            <li>Decision Making: ${data.test_result.personality_influence.decision_making_approach}</li>
                            <li>Expertise: ${data.test_result.personality_influence.expertise_domains.join(', ')}</li>
                        </ul>
                    </div>
                `;
                
                resultsDiv.style.display = 'block';
            } else {
                this.showMessage('Error testing profile: ' + data.error, 'error');
            }
        } catch (error) {
            console.error('Error testing profile:', error);
            this.showMessage('Failed to test profile', 'error');
        }
    }
    
    async cloneProfile(profileId) {
        try {
            const name = prompt('Enter a name for the cloned profile:');
            if (!name) return;
            
            const response = await fetch(`/api/personality/profiles/${profileId}/clone`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({ name })
            });
            
            const data = await response.json();
            
            if (data.success) {
                this.showMessage('Profile cloned successfully!', 'success');
                this.loadProfiles();
            } else {
                this.showMessage('Error cloning profile: ' + data.error, 'error');
            }
        } catch (error) {
            console.error('Error cloning profile:', error);
            this.showMessage('Failed to clone profile', 'error');
        }
    }
    
    async deleteProfile(profileId) {
        if (!confirm('Are you sure you want to delete this profile?')) {
            return;
        }
        
        try {
            const response = await fetch(`/api/personality/profiles/${profileId}`, {
                method: 'DELETE'
            });
            
            const data = await response.json();
            
            if (data.success) {
                this.showMessage('Profile deleted successfully!', 'success');
                this.loadProfiles();
            } else {
                this.showMessage('Error deleting profile: ' + data.error, 'error');
            }
        } catch (error) {
            console.error('Error deleting profile:', error);
            this.showMessage('Failed to delete profile', 'error');
        }
    }
    
    getFormData() {
        const form = document.getElementById('profile-form');
        const formData = new FormData(form);
        
        const data = {
            name: formData.get('name'),
            description: formData.get('description'),
            executive_type: formData.get('executive_type'),
            industry_specialization: formData.get('industry_specialization'),
            communication_style: formData.get('communication_style'),
            decision_making_style: formData.get('decision_making_style'),
            risk_tolerance: formData.get('risk_tolerance'),
            experience_level: formData.get('experience_level'),
            background_context: formData.get('background_context'),
            is_default: formData.get('is_default') === 'on',
            is_public: formData.get('is_public') === 'on',
            expertise_domains: this.expertiseDomains,
            tone_preferences: {
                formality: parseFloat(formData.get('formality')),
                enthusiasm: parseFloat(formData.get('enthusiasm')),
                directness: parseFloat(formData.get('directness')),
                technical_depth: parseFloat(formData.get('technical_depth'))
            },
            personality_traits: {
                analytical: parseFloat(formData.get('analytical')),
                collaborative: parseFloat(formData.get('collaborative')),
                innovative: parseFloat(formData.get('innovative')),
                detail_oriented: parseFloat(formData.get('detail_oriented')),
                decisive: parseFloat(formData.get('decisive'))
            }
        };
        
        return data;
    }
    
    resetForm() {
        document.getElementById('profile-form').reset();
        this.expertiseDomains = [];
        this.updateExpertiseDomainsDisplay();
        
        // Reset sliders to default values
        document.querySelectorAll('input[type="range"]').forEach(slider => {
            const valueDisplay = slider.parentElement.querySelector('.slider-value');
            valueDisplay.textContent = slider.value;
        });
    }
    
    addExpertiseDomain(domain) {
        if (domain && !this.expertiseDomains.includes(domain)) {
            this.expertiseDomains.push(domain);
            this.updateExpertiseDomainsDisplay();
        }
    }
    
    removeExpertiseDomain(domain) {
        this.expertiseDomains = this.expertiseDomains.filter(d => d !== domain);
        this.updateExpertiseDomainsDisplay();
    }
    
    updateExpertiseDomainsDisplay() {
        const container = document.getElementById('expertise-tags');
        container.innerHTML = this.expertiseDomains.map(domain => `
            <span class="tag">
                ${domain}
                <button type="button" class="tag-remove" onclick="personalityConfig.removeExpertiseDomain('${domain}')">&times;</button>
            </span>
        `).join('');
    }
    
    updateExpertiseDomains(executiveType) {
        if (this.configOptions && this.configOptions.common_expertise_domains) {
            const commonDomains = this.configOptions.common_expertise_domains[executiveType] || [];
            
            // Clear current domains and add common ones for this executive type
            this.expertiseDomains = [...commonDomains];
            this.updateExpertiseDomainsDisplay();
        }
    }
    
    filterProfiles() {
        this.renderProfiles();
    }
    
    filterPublicProfiles() {
        // Implementation for filtering public profiles
        this.renderPublicProfiles();
    }
    
    testCurrentProfile() {
        // Test the profile being created/edited
        const formData = this.getFormData();
        
        // Create a temporary test scenario
        const testScenario = 'What should be our strategy for the next quarter?';
        
        // Show test modal with current form data
        document.getElementById('test-scenario').value = testScenario;
        document.getElementById('test-modal').classList.add('show');
        
        // Simulate test response based on form data
        setTimeout(() => {
            const resultsDiv = document.getElementById('test-results');
            const responseDiv = document.getElementById('test-response');
            
            responseDiv.innerHTML = `
                <div class="test-scenario">
                    <strong>Scenario:</strong> ${testScenario}
                </div>
                <div class="test-response">
                    <strong>Simulated Response:</strong> Based on the ${formData.name || 'current'} profile configuration, 
                    I would approach this with a ${formData.communication_style} communication style, 
                    focusing on ${formData.expertise_domains.join(', ')} expertise areas.
                </div>
                <div class="personality-influence">
                    <strong>Profile Configuration:</strong>
                    <ul>
                        <li>Communication Style: ${formData.communication_style}</li>
                        <li>Decision Making: ${formData.decision_making_style}</li>
                        <li>Risk Tolerance: ${formData.risk_tolerance}</li>
                        <li>Experience Level: ${formData.experience_level}</li>
                    </ul>
                </div>
            `;
            
            resultsDiv.style.display = 'block';
        }, 500);
    }
    
    closeModal() {
        document.querySelectorAll('.modal').forEach(modal => {
            modal.classList.remove('show');
        });
        
        // Reset test results
        document.getElementById('test-results').style.display = 'none';
    }
    
    showMessage(message, type = 'info') {
        // Create or update message element
        let messageEl = document.querySelector('.message');
        if (!messageEl) {
            messageEl = document.createElement('div');
            messageEl.className = 'message';
            document.querySelector('.container').insertBefore(messageEl, document.querySelector('.personality-nav'));
        }
        
        messageEl.className = `message ${type}`;
        messageEl.textContent = message;
        
        // Auto-hide after 5 seconds
        setTimeout(() => {
            if (messageEl.parentNode) {
                messageEl.parentNode.removeChild(messageEl);
            }
        }, 5000);
    }
}

// Initialize the personality configuration when the page loads
let personalityConfig;
document.addEventListener('DOMContentLoaded', () => {
    personalityConfig = new PersonalityConfig();
});