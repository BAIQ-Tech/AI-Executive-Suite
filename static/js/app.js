// Global state
let currentAgent = 'ceo';
let voiceModeEnabled = false;
let recognition = null;
let speechSynthesis = window.speechSynthesis;
let currentVoices = [];
let currentLanguage = 'en';

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
    setupTabs();
    loadAgentInfo();
    loadDashboard();
    initializeVoice();
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
    // Initialize Speech Recognition
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
