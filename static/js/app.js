// Global state
let currentAgent = 'ceo';
let voiceModeEnabled = false;
let recognition = null;
let speechSynthesis = window.speechSynthesis;
let currentVoices = [];
let currentLanguage = 'en';

// Mobile-specific state
let isMobile = false;
let touchStartY = 0;
let touchEndY = 0;
let isRefreshing = false;
let swipeThreshold = 50;

// Multilingual translations
const translations = {
    ja: {
        title: 'AI役員スイート',
        subtitle: 'AI CEO、CTO、CFOとコミュニケーション',
        ceo: 'CEO - 戦略的リーダーシップ',
        cto: 'CTO - 技術的リーダーシップ', 
        cfo: 'CFO - 財務リーダーシップ',
        dashboard: 'エグゼクティブダッシュボード',
        vision: 'ビジョン',
        mission: 'ミッション',
        principles: '原則',
        techStack: '技術スタック',
        budgetStatus: '予算状況',
        financialHealth: '財務健全性',
        askCEO: 'CEOに質問',
        askCTO: 'CTOに質問',
        askCFO: 'CFOに質問',
        speak: '話す',
        talkModeOn: '🎤 トークモード: ON',
        talkModeOff: '🎤 トークモード: OFF',
        voiceReady: '音声認識準備完了',
        listening: '聞いています...',
        thinking: '考えています...',
        analyzing: '分析中...',
        calculating: '計算中...',
        speaking: '話しています...',
        decision: '決定',
        rationale: '根拠',
        priority: '優先度',
        category: 'カテゴリー',
        impact: '影響度',
        financialImpact: '財務影響',
        riskLevel: 'リスクレベル',
        decisionId: '決定ID',
        recentDecisions: '最近の決定',
        contextPlaceholder: 'ビジネス状況や必要な決定を説明してください...',
        techContextPlaceholder: '技術的課題や必要な決定を説明してください...',
        finContextPlaceholder: '財務的決定が必要な状況を説明してください...',
        optionsLabel: 'オプション（任意、1行に1つ）',
        techOptionsLabel: '技術的オプション（任意、1行に1つ）',
        finOptionsLabel: '財務オプション（任意、1行に1つ）',
        financialImpactPlaceholder: '財務影響（円）'
    },
    zh: {
        title: 'AI高管套件',
        subtitle: '与您的AI CEO、CTO和CFO沟通',
        ceo: 'CEO - 战略领导',
        cto: 'CTO - 技术领导',
        cfo: 'CFO - 财务领导',
        dashboard: '高管仪表板',
        vision: '愿景',
        mission: '使命',
        principles: '原则',
        techStack: '技术栈',
        budgetStatus: '预算状态',
        financialHealth: '财务健康',
        askCEO: '询问CEO',
        askCTO: '询问CTO',
        askCFO: '询问CFO',
        speak: '说话',
        talkModeOn: '🎤 对话模式: 开启',
        talkModeOff: '🎤 对话模式: 关闭',
        voiceReady: '语音识别已准备',
        listening: '正在聆听...',
        thinking: '正在思考...',
        analyzing: '正在分析...',
        calculating: '正在计算...',
        speaking: '正在说话...',
        decision: '决策',
        rationale: '理由',
        priority: '优先级',
        category: '类别',
        impact: '影响',
        financialImpact: '财务影响',
        riskLevel: '风险级别',
        decisionId: '决策ID',
        recentDecisions: '最近决策',
        contextPlaceholder: '描述业务情况或需要的决策...',
        techContextPlaceholder: '描述技术挑战或需要的决策...',
        finContextPlaceholder: '描述需要的财务决策...',
        optionsLabel: '选项（可选，每行一个）：',
        techOptionsLabel: '技术选项（可选，每行一个）：',
        finOptionsLabel: '财务选项（可选，每行一个）：',
        financialImpactPlaceholder: '财务影响（¥）'
    },
    en: {
        title: 'AI Executive Suite',
        subtitle: 'Communicate with your AI CEO, CTO, and CFO',
        ceo: 'CEO - Strategic Leadership',
        cto: 'CTO - Technical Leadership',
        cfo: 'CFO - Financial Leadership',
        dashboard: 'Executive Dashboard',
        vision: 'Vision',
        mission: 'Mission',
        principles: 'Principles',
        techStack: 'Tech Stack',
        budgetStatus: 'Budget Status',
        financialHealth: 'Financial Health',
        askCEO: 'Ask CEO',
        askCTO: 'Ask CTO',
        askCFO: 'Ask CFO',
        speak: 'Speak',
        talkModeOn: '🎤 Talk Mode: ON',
        talkModeOff: '🎤 Talk Mode: OFF',
        voiceReady: 'Voice recognition ready',
        listening: 'Listening...',
        thinking: 'CEO is thinking...',
        analyzing: 'CTO is analyzing...',
        calculating: 'CFO is calculating...',
        speaking: 'is speaking...',
        decision: 'Decision',
        rationale: 'Rationale',
        priority: 'Priority',
        category: 'Category',
        impact: 'Impact',
        financialImpact: 'Financial Impact',
        riskLevel: 'Risk Level',
        decisionId: 'Decision ID',
        recentDecisions: 'Recent Decisions',
        contextPlaceholder: 'Describe the business situation or decision needed...',
        techContextPlaceholder: 'Describe the technical challenge or decision needed...',
        finContextPlaceholder: 'Describe the financial decision needed...',
        optionsLabel: 'Options (optional, one per line):',
        techOptionsLabel: 'Technical Options (optional, one per line):',
        finOptionsLabel: 'Financial Options (optional, one per line):',
        financialImpactPlaceholder: 'Financial Impact ($)'
    }
};

// Initialize the app
document.addEventListener('DOMContentLoaded', function() {
    detectMobile();
    setupTabs();
    loadAgentInfo();
    loadDashboard();
    initializeVoice();
    initializeMobileFeatures();
    initializeNotifications();
});

// Tab functionality
function setupTabs() {
    const tabBtns = document.querySelectorAll('.tab-btn');
    const panels = document.querySelectorAll('.agent-panel');
    
    tabBtns.forEach(btn => {
        btn.addEventListener('click', () => {
            const agent = btn.dataset.agent;
            switchAgent(agent);
        });
    });
}

function switchAgent(agent) {
    // Update tab buttons
    document.querySelectorAll('.tab-btn').forEach(btn => {
        btn.classList.remove('active');
    });
    document.querySelector(`[data-agent="${agent}"]`).classList.add('active');
    
    // Update panels
    document.querySelectorAll('.agent-panel').forEach(panel => {
        panel.classList.remove('active');
    });
    document.getElementById(`${agent}-panel`).classList.add('active');
    
    currentAgent = agent;
}

// Load agent information
async function loadAgentInfo() {
    try {
        // Load CEO info
        const response = await fetch(`/api/ceo/vision?lang=${currentLanguage}`);
        const ceoData = await response.json();
        document.getElementById('ceo-vision').textContent = ceoData.vision;
        document.getElementById('ceo-mission').textContent = ceoData.mission;
        
        // Load CTO info
        const ctoResponse = await fetch(`/api/cto/info?lang=${currentLanguage}`);
        const ctoData = await ctoResponse.json();
        document.getElementById('cto-vision').textContent = ctoData.vision;
        
        const principlesHtml = '<p><strong>Principles:</strong></p><ul>' + 
            ctoData.principles.map(p => `<li>${p}</li>`).join('') + '</ul>';
        document.getElementById('cto-principles').innerHTML = principlesHtml;
        
        const stackHtml = '<p><strong>Tech Stack:</strong></p>' +
            Object.entries(ctoData.tech_stack).map(([category, techs]) => {
                if (techs.length === 0) return '';
                return `<div class="tech-category"><strong>${category}:</strong> ${
                    techs.map(t => `${t.name} v${t.version}`).join(', ')
                }</div>`;
            }).join('');
        document.getElementById('cto-stack').innerHTML = stackHtml;
        
        // Load CFO info
        const cfoResponse = await fetch(`/api/cfo/info?lang=${currentLanguage}`);
        const cfoData = await cfoResponse.json();
        document.getElementById('cfo-vision').textContent = cfoData.vision;
        
        const budgetHtml = '<p><strong>Budget Status:</strong></p>' +
            Object.entries(cfoData.budget).map(([category, data]) => 
                `<div class="budget-item">${category}: $${data.spent}/$${data.allocated} (${data.utilization}%)</div>`
            ).join('');
        document.getElementById('cfo-budget').innerHTML = budgetHtml;
        
        document.getElementById('cfo-health').innerHTML = 
            `<p><strong>Financial Health:</strong> ${cfoData.health_score}/100 (${cfoData.health_status})</p>`;
            
    } catch (error) {
        console.error('Error loading agent info:', error);
    }
}

// CEO Functions
async function askCEO() {
    const context = document.getElementById('ceo-context').value.trim();
    if (!context) {
        alert('Please enter a business context or question.');
        return;
    }
    
    const optionsText = document.getElementById('ceo-options').value.trim();
    const options = optionsText ? optionsText.split('\n').filter(o => o.trim()) : [];
    
    try {
        addMessage('ceo', 'user', context);
        addMessage('ceo', 'system', translations[currentLanguage].thinking);
        
        const response = await fetch('/api/ceo/decision', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({
                context: context,
                options: options,
                lang: currentLanguage
            })
        });
        
        const data = await response.json();
        
        // Remove thinking message
        removeLastMessage('ceo');
        
        if (response.ok) {
            const message = `
                <div class="decision-response">
                    <strong>Decision:</strong> ${data.decision}<br>
                    <strong>Rationale:</strong> ${data.rationale}<br>
                    <strong>Priority:</strong> ${data.priority}<br>
                    <small>Decision ID: ${data.id}</small>
                </div>
            `;
            addMessage('ceo', 'agent', message);
            
            // Speak the response if voice mode is enabled
            if (voiceModeEnabled) {
                const spokenText = `CEO Decision: ${data.decision}. ${data.rationale}`;
                speakResponse(spokenText, 'ceo');
            }
        } else {
            addMessage('ceo', 'error', data.error || 'Error occurred');
        }
        
        // Clear inputs
        document.getElementById('ceo-context').value = '';
        document.getElementById('ceo-options').value = '';
        
    } catch (error) {
        removeLastMessage('ceo');
        addMessage('ceo', 'error', 'Network error occurred');
        console.error('Error:', error);
    }
}

// CTO Functions
async function askCTO() {
    const context = document.getElementById('cto-context').value.trim();
    if (!context) {
        alert('Please enter a technical context or question.');
        return;
    }
    
    const category = document.getElementById('cto-category').value;
    const impact = document.getElementById('cto-impact').value;
    const optionsText = document.getElementById('cto-options').value.trim();
    const options = optionsText ? optionsText.split('\n').filter(o => o.trim()) : [];
    
    try {
        addMessage('cto', 'user', context);
        addMessage('cto', 'system', translations[currentLanguage].analyzing);
        
        const response = await fetch('/api/cto/decision', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({
                context: context,
                category: category,
                impact: impact,
                options: options,
                lang: currentLanguage
            })
        });
        
        const data = await response.json();
        
        removeLastMessage('cto');
        
        if (response.ok) {
            const message = `
                <div class="decision-response">
                    <strong>Decision:</strong> ${data.decision}<br>
                    <strong>Rationale:</strong> ${data.rationale}<br>
                    <strong>Category:</strong> ${data.category}<br>
                    <strong>Impact:</strong> ${data.impact}<br>
                    <strong>Priority:</strong> ${data.priority}<br>
                    <small>Decision ID: ${data.id}</small>
                </div>
            `;
            addMessage('cto', 'agent', message);
            
            // Speak the response if voice mode is enabled
            if (voiceModeEnabled) {
                const spokenText = `CTO Technical Decision: ${data.decision}. ${data.rationale}`;
                speakResponse(spokenText, 'cto');
            }
        } else {
            addMessage('cto', 'error', data.error || 'Error occurred');
        }
        
        // Clear inputs
        document.getElementById('cto-context').value = '';
        document.getElementById('cto-options').value = '';
        
    } catch (error) {
        removeLastMessage('cto');
        addMessage('cto', 'error', 'Network error occurred');
        console.error('Error:', error);
    }
}

// CFO Functions
async function askCFO() {
    const context = document.getElementById('cfo-context').value.trim();
    if (!context) {
        alert('Please enter a financial context or question.');
        return;
    }
    
    const category = document.getElementById('cfo-category').value;
    const risk = document.getElementById('cfo-risk').value;
    const impact = document.getElementById('cfo-impact').value || 0;
    const optionsText = document.getElementById('cfo-options').value.trim();
    const options = optionsText ? optionsText.split('\n').filter(o => o.trim()) : [];
    
    try {
        addMessage('cfo', 'user', context);
        addMessage('cfo', 'system', translations[currentLanguage].calculating);
        
        const response = await fetch('/api/cfo/decision', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({
                context: context,
                category: category,
                risk_level: risk,
                financial_impact: parseFloat(impact),
                options: options,
                lang: currentLanguage
            })
        });
        
        const data = await response.json();
        
        removeLastMessage('cfo');
        
        if (response.ok) {
            const message = `
                <div class="decision-response">
                    <strong>Decision:</strong> ${data.decision}<br>
                    <strong>Rationale:</strong> ${data.rationale}<br>
                    <strong>Category:</strong> ${data.category}<br>
                    <strong>Financial Impact:</strong> $${parseFloat(data.financial_impact).toLocaleString()}<br>
                    <strong>Risk Level:</strong> ${data.risk_level}<br>
                    <strong>Priority:</strong> ${data.priority}<br>
                    <small>Decision ID: ${data.id}</small>
                </div>
            `;
            addMessage('cfo', 'agent', message);
            
            // Speak the response if voice mode is enabled
            if (voiceModeEnabled) {
                const spokenText = `CFO Financial Decision: ${data.decision}. Expected impact: ${parseFloat(data.financial_impact).toLocaleString()} dollars. ${data.rationale}`;
                speakResponse(spokenText, 'cfo');
            }
        } else {
            addMessage('cfo', 'error', data.error || 'Error occurred');
        }
        
        // Clear inputs
        document.getElementById('cfo-context').value = '';
        document.getElementById('cfo-options').value = '';
        document.getElementById('cfo-impact').value = '';
        
    } catch (error) {
        removeLastMessage('cfo');
        addMessage('cfo', 'error', 'Network error occurred');
        console.error('Error:', error);
    }
}

// Message handling
function addMessage(agent, type, content) {
    const messagesDiv = document.getElementById(`${agent}-messages`);
    const messageDiv = document.createElement('div');
    messageDiv.className = `message ${type}`;
    messageDiv.innerHTML = content;
    messagesDiv.appendChild(messageDiv);
    messagesDiv.scrollTop = messagesDiv.scrollHeight;
}

function removeLastMessage(agent) {
    const messagesDiv = document.getElementById(`${agent}-messages`);
    const lastMessage = messagesDiv.lastElementChild;
    if (lastMessage) {
        messagesDiv.removeChild(lastMessage);
    }
}

// Voice functionality
function initializeVoice() {
    // Use enhanced voice initialization for mobile
    if (isMobile) {
        initializeEnhancedVoice();
    } else {
        // Initialize Speech Recognition for desktop
        if ('webkitSpeechRecognition' in window || 'SpeechRecognition' in window) {
            const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;
            recognition = new SpeechRecognition();
            recognition.continuous = false;
            recognition.interimResults = false;
            if (currentLanguage === 'ja') {
                recognition.lang = 'ja-JP';
            } else if (currentLanguage === 'zh') {
                recognition.lang = 'zh-CN';
            } else {
                recognition.lang = 'en-US';
            }
            
            recognition.onstart = function() {
                updateVoiceStatus(translations[currentLanguage].listening);
            };
            
            recognition.onresult = function(event) {
                const transcript = event.results[0][0].transcript;
                handleVoiceInput(transcript);
            };
            
            recognition.onerror = function(event) {
                updateVoiceStatus('Voice recognition error: ' + event.error);
            };
            
            recognition.onend = function() {
                updateVoiceStatus(translations[currentLanguage].voiceReady);
            };
        } else {
            updateVoiceStatus('Voice recognition not supported in this browser');
        }
        
        // Load available voices for text-to-speech
        loadVoices();
        if (speechSynthesis.onvoiceschanged !== undefined) {
            speechSynthesis.onvoiceschanged = loadVoices;
        }
    }
}

function loadVoices() {
    currentVoices = speechSynthesis.getVoices();
}

function toggleVoiceMode() {
    voiceModeEnabled = !voiceModeEnabled;
    const toggleBtn = document.getElementById('voice-toggle');
    
    if (voiceModeEnabled) {
        toggleBtn.textContent = translations[currentLanguage].talkModeOn;
        toggleBtn.classList.add('active');
        updateVoiceStatus('Voice mode enabled - click Speak buttons to talk');
    } else {
        toggleBtn.textContent = translations[currentLanguage].talkModeOff;
        toggleBtn.classList.remove('active');
        updateVoiceStatus('Voice mode disabled');
    }
}

function setLanguage(lang) {
    currentLanguage = lang;
    
    // Update button states
    document.querySelectorAll('.language-selector .lang-btn').forEach(btn => {
        btn.classList.remove('active');
    });
    document.getElementById(`lang-${lang}`).classList.add('active');
    
    // Update UI text
    updateUILanguage();
    
    // Reload agent info
    loadAgentInfo();
    loadDashboard();
    
    // Update voice recognition language
    if (recognition) {
        if (currentLanguage === 'ja') {
            recognition.lang = 'ja-JP';
        } else if (currentLanguage === 'zh') {
            recognition.lang = 'zh-CN';
        } else {
            recognition.lang = 'en-US';
        }
    }
}

// Keep the old function for backward compatibility
function toggleLanguage() {
    if (currentLanguage === 'en') {
        setLanguage('ja');
    } else if (currentLanguage === 'ja') {
        setLanguage('zh');
    } else {
        setLanguage('en');
    }
}

function updateUILanguage() {
    const t = translations[currentLanguage];
    
    // Update header
    document.querySelector('header h1').textContent = '🏢 ' + t.title;
    document.querySelector('header p').textContent = t.subtitle;
    
    // Update agent panel headers
    document.querySelector('#ceo-panel h2').textContent = t.ceo;
    document.querySelector('#cto-panel h2').textContent = t.cto;
    document.querySelector('#cfo-panel h2').textContent = t.cfo;
    document.querySelector('#dashboard-panel h2').textContent = t.dashboard;
    
    // Update labels
    document.querySelectorAll('label').forEach(label => {
        const text = label.textContent;
        if (text.includes('Options')) {
            if (label.closest('#ceo-panel')) {
                label.textContent = t.optionsLabel;
            } else if (label.closest('#cto-panel')) {
                label.textContent = t.techOptionsLabel;
            } else if (label.closest('#cfo-panel')) {
                label.textContent = t.finOptionsLabel;
            }
        }
    });
    
    // Update placeholders
    document.getElementById('ceo-context').placeholder = t.contextPlaceholder;
    document.getElementById('cto-context').placeholder = t.techContextPlaceholder;
    document.getElementById('cfo-context').placeholder = t.finContextPlaceholder;
    document.getElementById('cfo-impact').placeholder = t.financialImpactPlaceholder;
    
    // Update buttons
    document.querySelector('#ceo-panel .ask-btn').textContent = t.askCEO;
    document.querySelector('#cto-panel .ask-btn').textContent = t.askCTO;
    document.querySelector('#cfo-panel .ask-btn').textContent = t.askCFO;
    
    document.querySelectorAll('.voice-input-btn').forEach(btn => {
        btn.textContent = '🎤 ' + t.speak;
    });
    
    // Update voice mode button
    const voiceBtn = document.getElementById('voice-toggle');
    voiceBtn.textContent = voiceModeEnabled ? t.talkModeOn : t.talkModeOff;
}

function startVoiceInput(agent) {
    if (!voiceModeEnabled) {
        alert('Please enable Talk Mode first!');
        return;
    }
    
    if (!recognition) {
        alert('Voice recognition not available in this browser');
        return;
    }
    
    currentAgent = agent;
    recognition.start();
}

function handleVoiceInput(transcript) {
    updateVoiceStatus(`Heard: "${transcript}"`);
    
    // Fill the appropriate textarea with the transcript
    const contextField = document.getElementById(`${currentAgent}-context`);
    contextField.value = transcript;
    
    // Automatically ask the agent
    setTimeout(() => {
        if (currentAgent === 'ceo') {
            askCEO();
        } else if (currentAgent === 'cto') {
            askCTO();
        } else if (currentAgent === 'cfo') {
            askCFO();
        }
    }, 500);
}

function speakResponse(text, agentName) {
    // Use enhanced speech for mobile
    if (isMobile) {
        enhancedSpeakResponse(text, agentName);
        return;
    }
    
    // Desktop speech implementation
    if (!voiceModeEnabled || !speechSynthesis) return;
    
    // Cancel any ongoing speech
    speechSynthesis.cancel();
    
    const utterance = new SpeechSynthesisUtterance(text);
    
    // Select appropriate voice based on agent
    const voices = currentVoices;
    let selectedVoice = null;
    
    if (currentLanguage === 'ja') {
        // Japanese voices
        if (agentName === 'ceo') {
            selectedVoice = voices.find(voice => voice.lang.startsWith('ja') && voice.name.includes('Male')) ||
                          voices.find(voice => voice.lang.startsWith('ja'));
        } else if (agentName === 'cto') {
            selectedVoice = voices.find(voice => voice.lang.startsWith('ja') && voice.name.includes('Female')) ||
                          voices.find(voice => voice.lang.startsWith('ja'));
        } else if (agentName === 'cfo') {
            selectedVoice = voices.find(voice => voice.lang.startsWith('ja'));
        }
    } else {
        // English voices
        if (agentName === 'ceo') {
            selectedVoice = voices.find(voice => 
                voice.name.includes('Male') || voice.name.includes('Daniel') || voice.name.includes('Alex')
            ) || voices.find(voice => voice.lang.startsWith('en') && voice.name.includes('Male'));
        } else if (agentName === 'cto') {
            selectedVoice = voices.find(voice => 
                voice.name.includes('Female') || voice.name.includes('Samantha') || voice.name.includes('Karen')
            ) || voices.find(voice => voice.lang.startsWith('en') && voice.name.includes('Female'));
        } else if (agentName === 'cfo') {
            selectedVoice = voices.find(voice => 
                voice.name.includes('Tom') || voice.name.includes('Michael')
            ) || voices.find(voice => voice.lang.startsWith('en'));
        }
    }
    
    if (selectedVoice) {
        utterance.voice = selectedVoice;
    }
    
    utterance.rate = 0.9;
    utterance.pitch = 1.0;
    utterance.volume = 0.8;
    
    utterance.onstart = function() {
        updateVoiceStatus(`${agentName.toUpperCase()} is speaking...`);
    };
    
    utterance.onend = function() {
        updateVoiceStatus('Voice mode ready');
    };
    
    speechSynthesis.speak(utterance);
}

function updateVoiceStatus(message) {
    const statusDiv = document.getElementById('voice-status');
    if (statusDiv) {
        statusDiv.textContent = message;
    }
}

// Dashboard functions
async function loadDashboard() {
    try {
        const response = await fetch(`/api/decisions?lang=${currentLanguage}`);
        const data = await response.json();
        
        // CEO decisions
        const ceoHtml = data.ceo.slice(-5).map(d => 
            `<div class="decision-item">
                <div class="decision-text">${d.decision.substring(0, 60)}...</div>
                <div class="decision-meta">${d.priority} priority • ${d.status}</div>
            </div>`
        ).join('');
        document.getElementById('ceo-decisions').innerHTML = ceoHtml || '<p>No decisions yet</p>';
        
        // CTO decisions
        const ctoHtml = data.cto.slice(-5).map(d => 
            `<div class="decision-item">
                <div class="decision-text">${d.decision.substring(0, 60)}...</div>
                <div class="decision-meta">${d.category} • ${d.priority} priority</div>
            </div>`
        ).join('');
        document.getElementById('cto-decisions').innerHTML = ctoHtml || '<p>No decisions yet</p>';
        
        // CFO decisions
        const cfoHtml = data.cfo.slice(-5).map(d => 
            `<div class="decision-item">
                <div class="decision-text">${d.decision.substring(0, 60)}...</div>
                <div class="decision-meta">$${parseFloat(d.financial_impact).toLocaleString()} • ${d.priority}</div>
            </div>`
        ).join('');
        document.getElementById('cfo-decisions').innerHTML = cfoHtml || '<p>No decisions yet</p>';
        
    } catch (error) {
        console.error('Error loading dashboard:', error);
    }
}

// Mobile-specific functions

function detectMobile() {
    isMobile = /Android|webOS|iPhone|iPad|iPod|BlackBerry|IEMobile|Opera Mini/i.test(navigator.userAgent) ||
               window.innerWidth <= 768;
    
    if (isMobile) {
        document.body.classList.add('mobile-device');
        
        // Add viewport meta tag if not present
        if (!document.querySelector('meta[name="viewport"]')) {
            const viewport = document.createElement('meta');
            viewport.name = 'viewport';
            viewport.content = 'width=device-width, initial-scale=1.0, maximum-scale=1.0, user-scalable=no';
            document.head.appendChild(viewport);
        }
    }
}

function initializeMobileFeatures() {
    if (!isMobile) return;
    
    // Initialize mobile navigation
    initializeMobileNavigation();
    
    // Initialize touch gestures
    initializeTouchGestures();
    
    // Initialize pull-to-refresh
    initializePullToRefresh();
    
    // Optimize forms for mobile
    optimizeFormsForMobile();
    
    // Add mobile-specific event listeners
    addMobileEventListeners();
    
    // Optimize chat for mobile
    optimizeChatForMobile();
}

function initializeMobileNavigation() {
    // Create mobile navigation if it doesn't exist
    if (!document.querySelector('.mobile-nav')) {
        const mobileNav = document.createElement('div');
        mobileNav.className = 'mobile-nav';
        mobileNav.innerHTML = `
            <button class="mobile-nav-toggle" onclick="toggleMobileNav()">
                ☰
            </button>
            <div class="mobile-nav-menu">
                <a href="#" class="mobile-nav-item" onclick="switchAgent('ceo'); closeMobileNav();">CEO</a>
                <a href="#" class="mobile-nav-item" onclick="switchAgent('cto'); closeMobileNav();">CTO</a>
                <a href="#" class="mobile-nav-item" onclick="switchAgent('cfo'); closeMobileNav();">CFO</a>
                <a href="#" class="mobile-nav-item" onclick="switchAgent('dashboard'); closeMobileNav();">Dashboard</a>
                <a href="/upload" class="mobile-nav-item">Upload Document</a>
                <a href="/analytics/dashboard" class="mobile-nav-item">Analytics</a>
            </div>
        `;
        document.body.insertBefore(mobileNav, document.body.firstChild);
        
        // Add padding to body to account for fixed nav
        document.body.style.paddingTop = '60px';
    }
}

function toggleMobileNav() {
    const menu = document.querySelector('.mobile-nav-menu');
    menu.classList.toggle('active');
}

function closeMobileNav() {
    const menu = document.querySelector('.mobile-nav-menu');
    menu.classList.remove('active');
}

function initializeTouchGestures() {
    // Add swipe gesture support for tab switching
    const agentPanels = document.querySelectorAll('.agent-panel');
    
    agentPanels.forEach(panel => {
        let startX = 0;
        let startY = 0;
        let endX = 0;
        let endY = 0;
        
        panel.addEventListener('touchstart', (e) => {
            startX = e.touches[0].clientX;
            startY = e.touches[0].clientY;
        }, { passive: true });
        
        panel.addEventListener('touchend', (e) => {
            endX = e.changedTouches[0].clientX;
            endY = e.changedTouches[0].clientY;
            
            const deltaX = endX - startX;
            const deltaY = endY - startY;
            
            // Only process horizontal swipes
            if (Math.abs(deltaX) > Math.abs(deltaY) && Math.abs(deltaX) > swipeThreshold) {
                if (deltaX > 0) {
                    // Swipe right - previous agent
                    switchToPreviousAgent();
                } else {
                    // Swipe left - next agent
                    switchToNextAgent();
                }
            }
        }, { passive: true });
    });
}

function switchToPreviousAgent() {
    const agents = ['ceo', 'cto', 'cfo', 'dashboard'];
    const currentIndex = agents.indexOf(currentAgent);
    const previousIndex = currentIndex > 0 ? currentIndex - 1 : agents.length - 1;
    switchAgent(agents[previousIndex]);
}

function switchToNextAgent() {
    const agents = ['ceo', 'cto', 'cfo', 'dashboard'];
    const currentIndex = agents.indexOf(currentAgent);
    const nextIndex = currentIndex < agents.length - 1 ? currentIndex + 1 : 0;
    switchAgent(agents[nextIndex]);
}

function initializePullToRefresh() {
    let startY = 0;
    let currentY = 0;
    let isPulling = false;
    
    const container = document.querySelector('.container');
    if (!container) return;
    
    // Create pull-to-refresh indicator
    const refreshIndicator = document.createElement('div');
    refreshIndicator.className = 'pull-to-refresh';
    refreshIndicator.textContent = 'Pull to refresh...';
    container.appendChild(refreshIndicator);
    
    container.addEventListener('touchstart', (e) => {
        if (container.scrollTop === 0) {
            startY = e.touches[0].clientY;
            isPulling = true;
        }
    }, { passive: true });
    
    container.addEventListener('touchmove', (e) => {
        if (!isPulling) return;
        
        currentY = e.touches[0].clientY;
        const pullDistance = currentY - startY;
        
        if (pullDistance > 0 && pullDistance < 100) {
            refreshIndicator.style.top = `${pullDistance - 50}px`;
            refreshIndicator.textContent = 'Pull to refresh...';
        } else if (pullDistance >= 100) {
            refreshIndicator.style.top = '20px';
            refreshIndicator.textContent = 'Release to refresh';
            refreshIndicator.classList.add('active');
        }
    }, { passive: true });
    
    container.addEventListener('touchend', (e) => {
        if (!isPulling) return;
        
        const pullDistance = currentY - startY;
        
        if (pullDistance >= 100 && !isRefreshing) {
            performRefresh();
        } else {
            refreshIndicator.style.top = '-50px';
            refreshIndicator.classList.remove('active');
        }
        
        isPulling = false;
    }, { passive: true });
}

async function performRefresh() {
    if (isRefreshing) return;
    
    isRefreshing = true;
    const refreshIndicator = document.querySelector('.pull-to-refresh');
    refreshIndicator.textContent = 'Refreshing...';
    
    try {
        // Refresh current data
        await loadAgentInfo();
        await loadDashboard();
        
        // Show success feedback
        refreshIndicator.textContent = 'Refreshed!';
        setTimeout(() => {
            refreshIndicator.style.top = '-50px';
            refreshIndicator.classList.remove('active');
        }, 1000);
        
    } catch (error) {
        console.error('Refresh failed:', error);
        refreshIndicator.textContent = 'Refresh failed';
        setTimeout(() => {
            refreshIndicator.style.top = '-50px';
            refreshIndicator.classList.remove('active');
        }, 2000);
    } finally {
        isRefreshing = false;
    }
}

function optimizeFormsForMobile() {
    // Add mobile-friendly classes to form elements
    const textareas = document.querySelectorAll('textarea');
    const inputs = document.querySelectorAll('input');
    const selects = document.querySelectorAll('select');
    const buttons = document.querySelectorAll('button');
    
    textareas.forEach(textarea => {
        textarea.classList.add('touch-friendly');
        // Prevent zoom on iOS
        if (textarea.style.fontSize === '' || parseFloat(textarea.style.fontSize) < 16) {
            textarea.style.fontSize = '16px';
        }
    });
    
    inputs.forEach(input => {
        input.classList.add('touch-friendly');
        if (input.style.fontSize === '' || parseFloat(input.style.fontSize) < 16) {
            input.style.fontSize = '16px';
        }
    });
    
    selects.forEach(select => {
        select.classList.add('touch-friendly');
    });
    
    buttons.forEach(button => {
        button.classList.add('touch-friendly');
    });
}

function addMobileEventListeners() {
    // Prevent double-tap zoom on buttons
    const buttons = document.querySelectorAll('button, .btn, .tab-btn');
    buttons.forEach(button => {
        button.addEventListener('touchend', (e) => {
            e.preventDefault();
            button.click();
        });
    });
    
    // Handle orientation change
    window.addEventListener('orientationchange', () => {
        setTimeout(() => {
            // Recalculate dimensions after orientation change
            detectMobile();
            optimizeChatForMobile();
        }, 100);
    });
    
    // Handle window resize
    window.addEventListener('resize', () => {
        detectMobile();
        optimizeChatForMobile();
    });
}

function optimizeChatForMobile() {
    if (!isMobile) return;
    
    const chatSections = document.querySelectorAll('.chat-section');
    chatSections.forEach(section => {
        section.classList.add('mobile-chat');
        
        const chatMessages = section.querySelector('.chat-messages');
        if (chatMessages) {
            chatMessages.classList.add('swipeable');
        }
        
        const inputSection = section.querySelector('.input-section');
        if (inputSection) {
            inputSection.classList.add('mobile-chat-input');
        }
    });
}

// Enhanced voice functions for mobile
function enhancedStartVoiceInput(agent) {
    if (!voiceModeEnabled) {
        // Show mobile-friendly alert
        showMobileAlert('Please enable Talk Mode first!');
        return;
    }
    
    if (!recognition) {
        showMobileAlert('Voice recognition not available in this browser');
        return;
    }
    
    // Provide haptic feedback if available
    if (navigator.vibrate) {
        navigator.vibrate(50);
    }
    
    // Update UI to show recording state
    const voiceBtn = document.querySelector(`#${agent}-panel .voice-input-btn`);
    if (voiceBtn) {
        voiceBtn.classList.add('recording');
        voiceBtn.textContent = '🔴 Recording...';
    }
    
    currentAgent = agent;
    recognition.start();
}

// Enhanced speech-to-text with mobile optimizations
function initializeEnhancedVoice() {
    if ('webkitSpeechRecognition' in window || 'SpeechRecognition' in window) {
        const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;
        recognition = new SpeechRecognition();
        
        // Mobile-optimized settings
        recognition.continuous = false;
        recognition.interimResults = true; // Show interim results for better UX
        recognition.maxAlternatives = 3; // Get multiple alternatives
        
        // Set language based on current language
        updateVoiceRecognitionLanguage();
        
        recognition.onstart = function() {
            updateVoiceStatus(translations[currentLanguage].listening);
            // Provide haptic feedback
            if (navigator.vibrate) {
                navigator.vibrate([100, 50, 100]);
            }
        };
        
        recognition.onresult = function(event) {
            let transcript = '';
            let confidence = 0;
            
            // Get the best result
            for (let i = event.resultIndex; i < event.results.length; i++) {
                const result = event.results[i];
                if (result.isFinal) {
                    transcript = result[0].transcript;
                    confidence = result[0].confidence;
                } else {
                    // Show interim results
                    const interimTranscript = result[0].transcript;
                    updateVoiceStatus(`Hearing: "${interimTranscript}"`);
                }
            }
            
            if (transcript) {
                handleEnhancedVoiceInput(transcript, confidence);
            }
        };
        
        recognition.onerror = function(event) {
            console.error('Speech recognition error:', event.error);
            let errorMessage = 'Voice recognition error';
            
            switch(event.error) {
                case 'no-speech':
                    errorMessage = 'No speech detected. Please try again.';
                    break;
                case 'audio-capture':
                    errorMessage = 'Microphone not available. Please check permissions.';
                    break;
                case 'not-allowed':
                    errorMessage = 'Microphone access denied. Please enable microphone permissions.';
                    break;
                case 'network':
                    errorMessage = 'Network error. Please check your connection.';
                    break;
                default:
                    errorMessage = `Voice recognition error: ${event.error}`;
            }
            
            showMobileAlert(errorMessage);
            resetVoiceButton();
        };
        
        recognition.onend = function() {
            updateVoiceStatus(translations[currentLanguage].voiceReady);
            resetVoiceButton();
        };
    } else {
        updateVoiceStatus('Voice recognition not supported in this browser');
    }
    
    // Initialize enhanced text-to-speech
    initializeEnhancedTTS();
}

function updateVoiceRecognitionLanguage() {
    if (!recognition) return;
    
    const languageMap = {
        'en': 'en-US',
        'ja': 'ja-JP',
        'zh': 'zh-CN'
    };
    
    recognition.lang = languageMap[currentLanguage] || 'en-US';
}

function handleEnhancedVoiceInput(transcript, confidence) {
    updateVoiceStatus(`Heard: "${transcript}" (${Math.round(confidence * 100)}% confidence)`);
    
    // Provide haptic feedback for successful recognition
    if (navigator.vibrate && confidence > 0.7) {
        navigator.vibrate(200);
    }
    
    // Fill the appropriate textarea with the transcript
    const contextField = document.getElementById(`${currentAgent}-context`);
    if (contextField) {
        contextField.value = transcript;
        
        // Trigger input event for any listeners
        contextField.dispatchEvent(new Event('input', { bubbles: true }));
    }
    
    // Show confidence indicator
    if (confidence < 0.5) {
        showMobileAlert(`Low confidence (${Math.round(confidence * 100)}%). Please speak more clearly.`);
        return;
    }
    
    // Auto-submit if confidence is high enough
    if (confidence > 0.8) {
        setTimeout(() => {
            if (currentAgent === 'ceo') {
                askCEO();
            } else if (currentAgent === 'cto') {
                askCTO();
            } else if (currentAgent === 'cfo') {
                askCFO();
            }
        }, 500);
    } else {
        // Ask user to confirm if confidence is moderate
        showConfirmationDialog(transcript, confidence);
    }
}

function showConfirmationDialog(transcript, confidence) {
    const dialog = document.createElement('div');
    dialog.className = 'mobile-confirmation-dialog';
    dialog.style.cssText = `
        position: fixed;
        top: 50%;
        left: 50%;
        transform: translate(-50%, -50%);
        background: white;
        padding: 20px;
        border-radius: 12px;
        box-shadow: 0 10px 30px rgba(0,0,0,0.3);
        z-index: 10001;
        max-width: 90%;
        text-align: center;
    `;
    
    dialog.innerHTML = `
        <h3>Confirm Voice Input</h3>
        <p>I heard: "<strong>${transcript}</strong>"</p>
        <p>Confidence: ${Math.round(confidence * 100)}%</p>
        <div style="margin-top: 20px; display: flex; gap: 10px; justify-content: center;">
            <button onclick="confirmVoiceInput('${transcript}')" class="mobile-btn mobile-btn-primary">
                ✓ Correct
            </button>
            <button onclick="retryVoiceInput()" class="mobile-btn mobile-btn-secondary">
                🎤 Try Again
            </button>
            <button onclick="cancelVoiceInput()" class="mobile-btn mobile-btn-secondary">
                ✕ Cancel
            </button>
        </div>
    `;
    
    document.body.appendChild(dialog);
    
    // Auto-close after 10 seconds
    setTimeout(() => {
        if (document.body.contains(dialog)) {
            document.body.removeChild(dialog);
        }
    }, 10000);
}

function confirmVoiceInput(transcript) {
    const dialog = document.querySelector('.mobile-confirmation-dialog');
    if (dialog) {
        document.body.removeChild(dialog);
    }
    
    // Submit the request
    setTimeout(() => {
        if (currentAgent === 'ceo') {
            askCEO();
        } else if (currentAgent === 'cto') {
            askCTO();
        } else if (currentAgent === 'cfo') {
            askCFO();
        }
    }, 100);
}

function retryVoiceInput() {
    const dialog = document.querySelector('.mobile-confirmation-dialog');
    if (dialog) {
        document.body.removeChild(dialog);
    }
    
    // Clear the input and start voice recognition again
    const contextField = document.getElementById(`${currentAgent}-context`);
    if (contextField) {
        contextField.value = '';
    }
    
    setTimeout(() => {
        enhancedStartVoiceInput(currentAgent);
    }, 500);
}

function cancelVoiceInput() {
    const dialog = document.querySelector('.mobile-confirmation-dialog');
    if (dialog) {
        document.body.removeChild(dialog);
    }
}

function resetVoiceButton() {
    const voiceBtns = document.querySelectorAll('.voice-input-btn');
    voiceBtns.forEach(btn => {
        btn.classList.remove('recording');
        btn.textContent = '🎤 ' + translations[currentLanguage].speak;
    });
}

// Enhanced text-to-speech with mobile optimizations
function initializeEnhancedTTS() {
    if (!speechSynthesis) return;
    
    // Load voices with retry mechanism
    loadVoicesWithRetry();
    
    if (speechSynthesis.onvoiceschanged !== undefined) {
        speechSynthesis.onvoiceschanged = loadVoicesWithRetry;
    }
}

function loadVoicesWithRetry(retryCount = 0) {
    currentVoices = speechSynthesis.getVoices();
    
    // Retry if no voices loaded (common on mobile)
    if (currentVoices.length === 0 && retryCount < 3) {
        setTimeout(() => loadVoicesWithRetry(retryCount + 1), 100);
        return;
    }
    
    // Log available voices for debugging
    console.log('Available voices:', currentVoices.map(v => `${v.name} (${v.lang})`));
}

function enhancedSpeakResponse(text, agentName) {
    if (!voiceModeEnabled || !speechSynthesis) return;
    
    // Cancel any ongoing speech
    speechSynthesis.cancel();
    
    // Clean text for better speech
    const cleanText = cleanTextForSpeech(text);
    
    const utterance = new SpeechSynthesisUtterance(cleanText);
    
    // Select appropriate voice with fallbacks
    const selectedVoice = selectBestVoice(agentName);
    if (selectedVoice) {
        utterance.voice = selectedVoice;
    }
    
    // Mobile-optimized speech settings
    utterance.rate = isMobile ? 0.8 : 0.9; // Slightly slower on mobile
    utterance.pitch = getAgentPitch(agentName);
    utterance.volume = 0.8;
    
    utterance.onstart = function() {
        updateVoiceStatus(`${agentName.toUpperCase()} is speaking...`);
        
        // Provide haptic feedback
        if (navigator.vibrate) {
            navigator.vibrate(100);
        }
        
        // Update UI to show speaking state
        const speakingIndicator = document.createElement('div');
        speakingIndicator.className = 'speaking-indicator';
        speakingIndicator.style.cssText = `
            position: fixed;
            bottom: 20px;
            right: 20px;
            background: rgba(102, 126, 234, 0.9);
            color: white;
            padding: 10px 15px;
            border-radius: 20px;
            font-size: 0.9rem;
            z-index: 1000;
            animation: pulse 1.5s infinite;
        `;
        speakingIndicator.textContent = `🔊 ${agentName.toUpperCase()} speaking...`;
        document.body.appendChild(speakingIndicator);
    };
    
    utterance.onend = function() {
        updateVoiceStatus('Voice mode ready');
        
        // Remove speaking indicator
        const indicator = document.querySelector('.speaking-indicator');
        if (indicator) {
            document.body.removeChild(indicator);
        }
        
        // Provide completion haptic feedback
        if (navigator.vibrate) {
            navigator.vibrate([50, 50, 50]);
        }
    };
    
    utterance.onerror = function(event) {
        console.error('Speech synthesis error:', event.error);
        updateVoiceStatus('Speech error occurred');
        
        // Remove speaking indicator
        const indicator = document.querySelector('.speaking-indicator');
        if (indicator) {
            document.body.removeChild(indicator);
        }
    };
    
    // Add to speech queue with chunking for long text
    if (cleanText.length > 200) {
        speakInChunks(cleanText, utterance);
    } else {
        speechSynthesis.speak(utterance);
    }
}

function cleanTextForSpeech(text) {
    return text
        .replace(/\*\*(.*?)\*\*/g, '$1') // Remove bold markdown
        .replace(/\*(.*?)\*/g, '$1') // Remove italic markdown
        .replace(/\n+/g, '. ') // Replace newlines with pauses
        .replace(/\s+/g, ' ') // Normalize whitespace
        .replace(/([.!?])\s*([A-Z])/g, '$1 $2') // Ensure pauses between sentences
        .trim();
}

function selectBestVoice(agentName) {
    if (currentVoices.length === 0) return null;
    
    const languagePrefix = currentLanguage === 'ja' ? 'ja' : 
                          currentLanguage === 'zh' ? 'zh' : 'en';
    
    // Filter voices by language
    const languageVoices = currentVoices.filter(voice => 
        voice.lang.startsWith(languagePrefix)
    );
    
    if (languageVoices.length === 0) {
        // Fallback to any English voice
        return currentVoices.find(voice => voice.lang.startsWith('en')) || currentVoices[0];
    }
    
    // Agent-specific voice selection
    let preferredVoices = [];
    
    switch (agentName) {
        case 'ceo':
            preferredVoices = languageVoices.filter(voice => 
                voice.name.toLowerCase().includes('male') ||
                voice.name.toLowerCase().includes('daniel') ||
                voice.name.toLowerCase().includes('alex')
            );
            break;
        case 'cto':
            preferredVoices = languageVoices.filter(voice => 
                voice.name.toLowerCase().includes('female') ||
                voice.name.toLowerCase().includes('samantha') ||
                voice.name.toLowerCase().includes('karen')
            );
            break;
        case 'cfo':
            preferredVoices = languageVoices.filter(voice => 
                voice.name.toLowerCase().includes('tom') ||
                voice.name.toLowerCase().includes('michael') ||
                voice.name.toLowerCase().includes('male')
            );
            break;
    }
    
    return preferredVoices[0] || languageVoices[0];
}

function getAgentPitch(agentName) {
    switch (agentName) {
        case 'ceo': return 0.9; // Slightly lower, authoritative
        case 'cto': return 1.1; // Slightly higher, analytical
        case 'cfo': return 1.0; // Neutral, professional
        default: return 1.0;
    }
}

function speakInChunks(text, baseUtterance) {
    const chunks = text.match(/.{1,200}(?:\s|$)/g) || [text];
    let chunkIndex = 0;
    
    function speakNextChunk() {
        if (chunkIndex >= chunks.length) return;
        
        const chunk = chunks[chunkIndex].trim();
        if (!chunk) {
            chunkIndex++;
            speakNextChunk();
            return;
        }
        
        const utterance = new SpeechSynthesisUtterance(chunk);
        utterance.voice = baseUtterance.voice;
        utterance.rate = baseUtterance.rate;
        utterance.pitch = baseUtterance.pitch;
        utterance.volume = baseUtterance.volume;
        
        utterance.onend = function() {
            chunkIndex++;
            setTimeout(speakNextChunk, 100); // Small pause between chunks
        };
        
        utterance.onerror = function(event) {
            console.error('Chunk speech error:', event.error);
            chunkIndex++;
            speakNextChunk();
        };
        
        speechSynthesis.speak(utterance);
    }
    
    speakNextChunk();
}

// Voice command shortcuts for common actions
const voiceCommands = {
    'clear': () => {
        const contextField = document.getElementById(`${currentAgent}-context`);
        if (contextField) contextField.value = '';
        showMobileAlert('Input cleared');
    },
    'switch to ceo': () => switchAgent('ceo'),
    'switch to cto': () => switchAgent('cto'),
    'switch to cfo': () => switchAgent('cfo'),
    'dashboard': () => switchAgent('dashboard'),
    'help': () => showVoiceHelp(),
    'stop': () => {
        speechSynthesis.cancel();
        showMobileAlert('Speech stopped');
    }
};

function processVoiceCommand(transcript) {
    const command = transcript.toLowerCase().trim();
    
    for (const [cmd, action] of Object.entries(voiceCommands)) {
        if (command.includes(cmd)) {
            action();
            return true;
        }
    }
    
    return false;
}

function showVoiceHelp() {
    const helpText = `
        Voice Commands:
        • "Clear" - Clear input
        • "Switch to CEO/CTO/CFO" - Change agent
        • "Dashboard" - Go to dashboard
        • "Stop" - Stop speech
        • "Help" - Show this help
    `;
    
    showMobileAlert(helpText);
}

// Offline voice command caching
let offlineVoiceCache = [];

function cacheVoiceCommand(transcript, agent) {
    if (!navigator.onLine) {
        offlineVoiceCache.push({
            transcript,
            agent,
            timestamp: Date.now()
        });
        showMobileAlert('Voice command cached for when online');
    }
}

function processOfflineVoiceCache() {
    if (navigator.onLine && offlineVoiceCache.length > 0) {
        const commands = [...offlineVoiceCache];
        offlineVoiceCache = [];
        
        commands.forEach(cmd => {
            // Process cached commands
            const contextField = document.getElementById(`${cmd.agent}-context`);
            if (contextField) {
                contextField.value = cmd.transcript;
            }
        });
        
        if (commands.length > 0) {
            showMobileAlert(`Processed ${commands.length} cached voice commands`);
        }
    }
}

// Listen for online/offline events
window.addEventListener('online', processOfflineVoiceCache);
window.addEventListener('offline', () => {
    showMobileAlert('Offline mode: Voice commands will be cached');
});

function showMobileAlert(message) {
    // Create a mobile-friendly alert
    const alert = document.createElement('div');
    alert.className = 'mobile-alert';
    alert.style.cssText = `
        position: fixed;
        top: 50%;
        left: 50%;
        transform: translate(-50%, -50%);
        background: rgba(0, 0, 0, 0.9);
        color: white;
        padding: 20px;
        border-radius: 12px;
        z-index: 10000;
        max-width: 80%;
        text-align: center;
        font-size: 16px;
    `;
    alert.textContent = message;
    
    document.body.appendChild(alert);
    
    setTimeout(() => {
        document.body.removeChild(alert);
    }, 3000);
}

// Override existing voice function for mobile compatibility
document.addEventListener('DOMContentLoaded', function() {
    if (isMobile) {
        window.startVoiceInput = enhancedStartVoiceInput;
    }
});// No
tification integration functions

function initializeNotifications() {
    // Load notification service script if on mobile
    if (isMobile && !window.notificationService) {
        const script = document.createElement('script');
        script.src = '/static/js/mobile-notifications.js';
        script.onload = () => {
            console.log('Mobile notifications loaded');
        };
        document.head.appendChild(script);
    }
}

// Enhanced CEO function with notifications
async function askCEOWithNotifications() {
    const originalAskCEO = window.askCEO;
    
    window.askCEO = async function() {
        const result = await originalAskCEO.apply(this, arguments);
        
        // Send notification about new decision
        if (window.notificationService && result) {
            setTimeout(() => {
                window.notificationService.notifyDecisionUpdate({
                    id: Date.now(),
                    executive_type: 'ceo',
                    decision: document.querySelector('#ceo-messages .message.agent:last-child')?.textContent || 'New CEO decision available'
                }, 'created');
            }, 1000);
        }
        
        return result;
    };
}

// Enhanced CTO function with notifications
async function askCTOWithNotifications() {
    const originalAskCTO = window.askCTO;
    
    window.askCTO = async function() {
        const result = await originalAskCTO.apply(this, arguments);
        
        // Send notification about new decision
        if (window.notificationService && result) {
            setTimeout(() => {
                window.notificationService.notifyDecisionUpdate({
                    id: Date.now(),
                    executive_type: 'cto',
                    decision: document.querySelector('#cto-messages .message.agent:last-child')?.textContent || 'New CTO decision available'
                }, 'created');
            }, 1000);
        }
        
        return result;
    };
}

// Enhanced CFO function with notifications
async function askCFOWithNotifications() {
    const originalAskCFO = window.askCFO;
    
    window.askCFO = async function() {
        const result = await originalAskCFO.apply(this, arguments);
        
        // Send notification about new decision
        if (window.notificationService && result) {
            setTimeout(() => {
                window.notificationService.notifyDecisionUpdate({
                    id: Date.now(),
                    executive_type: 'cfo',
                    decision: document.querySelector('#cfo-messages .message.agent:last-child')?.textContent || 'New CFO decision available'
                }, 'created');
            }, 1000);
        }
        
        return result;
    };
}

// Apply notification enhancements when service is ready
document.addEventListener('DOMContentLoaded', () => {
    if (isMobile) {
        // Wait for notification service to be available
        const checkService = setInterval(() => {
            if (window.notificationService) {
                clearInterval(checkService);
                askCEOWithNotifications();
                askCTOWithNotifications();
                askCFOWithNotifications();
            }
        }, 100);
        
        // Stop checking after 10 seconds
        setTimeout(() => clearInterval(checkService), 10000);
    }
});

// Add notification settings link to mobile navigation
function addNotificationSettingsToNav() {
    const mobileNav = document.querySelector('.mobile-nav-menu');
    if (mobileNav && !document.querySelector('.mobile-nav-item[href*="notifications"]')) {
        const settingsLink = document.createElement('a');
        settingsLink.href = '/mobile-notifications';
        settingsLink.className = 'mobile-nav-item';
        settingsLink.textContent = '🔔 Notifications';
        mobileNav.appendChild(settingsLink);
    }
}

// Call this when mobile nav is created
document.addEventListener('DOMContentLoaded', () => {
    if (isMobile) {
        setTimeout(addNotificationSettingsToNav, 1000);
    }
});