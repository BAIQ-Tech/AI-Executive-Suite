// Login page JavaScript functionality
class LoginManager {
    constructor() {
        this.currentLanguage = 'en'; // Default to English
        this.isLoading = false;
        this.translations = {
            en: {
                headerSubtitle: "Login to communicate with AI executives",
                signInTab: "Sign In",
                signUpTab: "Sign Up",
                emailLabel: "Email Address",
                passwordLabel: "Password",
                signInBtn: "Sign In",
                nameLabel: "Full Name",
                usernameLabel: "Username",
                confirmPasswordLabel: "Confirm Password",
                signUpBtn: "Sign Up",
                orText: "or",
                googleBtn: "Sign in with Google",
                appleBtn: "Sign in with Apple",
                web3Title: " Web3 Wallet Login",
                web3Desc: "Login with MetaMask, Coinbase Wallet, or Phantom wallet",
                termsText: "By logging into AI Executive Suite, you agree to our Terms of Service and Privacy Policy."
            },
            ja: {
                headerSubtitle: "ログインしてAI役員とコミュニケーション",
                signInTab: "ログイン",
                signUpTab: "新規登録",
                emailLabel: "メールアドレス",
                passwordLabel: "パスワード",
                signInBtn: "ログイン",
                nameLabel: "名前",
                usernameLabel: "ユーザー名",
                confirmPasswordLabel: "パスワード確認",
                signUpBtn: "新規登録",
                orText: "または",
                googleBtn: "Googleでログイン",
                appleBtn: "Appleでサインイン",
                web3Title: " Web3ウォレットでログイン",
                web3Desc: "MetaMask、Coinbase Wallet、Phantomウォレットでログインできます",
                termsText: "AI Executive Suiteにログインすることで、利用規約とプライバシーポリシーに同意したものとみなされます。"
            },
            zh: {
                headerSubtitle: "登录与AI高管沟通",
                signInTab: "登录",
                signUpTab: "注册",
                emailLabel: "邮箱地址",
                passwordLabel: "密码",
                signInBtn: "登录",
                nameLabel: "姓名",
                usernameLabel: "用户名",
                confirmPasswordLabel: "确认密码",
                signUpBtn: "注册",
                orText: "或",
                googleBtn: "使用Google登录",
                appleBtn: "使用Apple登录",
                web3Title: " Web3钱包登录",
                web3Desc: "使用MetaMask、Coinbase Wallet或Phantom钱包登录",
                termsText: "登录AI Executive Suite即表示您同意我们的服务条款和隐私政策。"
            }
        };
        
        this.setupTabs();
        this.setupForms();
        this.setupOAuth();
        this.setupWeb3();
        this.setupLanguageSelector();
        
        // Initialize language after DOM setup
        setTimeout(() => {
            this.changeLanguage(this.currentLanguage);
        }, 100);
    }

    // Tab Management
    setupTabs() {
        const tabBtns = document.querySelectorAll('.tab-btn');
        const tabContents = document.querySelectorAll('.tab-content');

        tabBtns.forEach(btn => {
            btn.addEventListener('click', () => {
                const tabId = btn.dataset.tab;
                this.switchTab(tabId);
            });
        });
    }

    switchTab(tabId) {
        // Update tab buttons
        document.querySelectorAll('.tab-btn').forEach(btn => {
            btn.classList.toggle('active', btn.dataset.tab === tabId);
        });

        // Update tab content
        document.querySelectorAll('.tab-content').forEach(content => {
            content.classList.toggle('active', content.id === `${tabId}-tab`);
        });

        this.currentTab = tabId;
    }

    // Form Management
    setupForms() {
        // Sign In Form
        const signinForm = document.getElementById('signin-form');
        if (signinForm) {
            signinForm.addEventListener('submit', (e) => this.handleSignIn(e));
        }

        // Sign Up Form
        const signupForm = document.getElementById('signup-form');
        if (signupForm) {
            signupForm.addEventListener('submit', (e) => this.handleSignUp(e));
        }
    }

    async handleSignIn(e) {
        e.preventDefault();
        
        const formData = new FormData(e.target);
        const email = formData.get('email');
        const password = formData.get('password');

        if (!this.validateEmail(email)) {
            this.showMessage('有効なメールアドレスを入力してください', 'error');
            return;
        }

        if (!password) {
            this.showMessage('パスワードを入力してください', 'error');
            return;
        }

        this.setLoading(true);

        try {
            const response = await fetch('/api/auth/login', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({ email, password })
            });

            const data = await response.json();

            if (response.ok) {
                this.showMessage('ログインしました！', 'success');
                setTimeout(() => {
                    window.location.href = '/';
                }, 1500);
            } else {
                this.showMessage(data.error || 'ログインに失敗しました', 'error');
            }
        } catch (error) {
            console.error('Login error:', error);
            this.showMessage('ネットワークエラーが発生しました', 'error');
        } finally {
            this.setLoading(false);
        }
    }

    async handleSignUp(e) {
        e.preventDefault();
        
        const formData = new FormData(e.target);
        const name = formData.get('name');
        const username = formData.get('username');
        const email = formData.get('email');
        const password = formData.get('password');
        const confirmPassword = formData.get('confirm_password');

        // Validation
        if (!name || !username || !email || !password) {
            this.showMessage('すべてのフィールドを入力してください', 'error');
            return;
        }

        if (!this.validateEmail(email)) {
            this.showMessage('有効なメールアドレスを入力してください', 'error');
            return;
        }

        if (password !== confirmPassword) {
            this.showMessage('パスワードが一致しません', 'error');
            return;
        }

        if (password.length < 6) {
            this.showMessage('パスワードは6文字以上で入力してください', 'error');
            return;
        }

        this.setLoading(true);

        try {
            const response = await fetch('/api/auth/register', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({ name, username, email, password })
            });

            const data = await response.json();

            if (response.ok) {
                this.showMessage('アカウントが作成されました！', 'success');
                setTimeout(() => {
                    this.switchTab('signin');
                }, 1500);
            } else {
                this.showMessage(data.error || '登録に失敗しました', 'error');
            }
        } catch (error) {
            console.error('Registration error:', error);
            this.showMessage('ネットワークエラーが発生しました', 'error');
        } finally {
            this.setLoading(false);
        }
    }

    // OAuth Setup
    setupOAuth() {
        // Google Sign-In
        const googleBtn = document.getElementById('google-signin');
        if (googleBtn) {
            googleBtn.addEventListener('click', () => this.handleGoogleSignIn());
        }

        // Apple Sign-In
        const appleBtn = document.getElementById('apple-signin');
        if (appleBtn) {
            appleBtn.addEventListener('click', () => this.handleAppleSignIn());
        }
    }

    handleGoogleSignIn() {
        this.setLoading(true);
        window.location.href = '/auth/google';
    }

    handleAppleSignIn() {
        this.setLoading(true);
        window.location.href = '/auth/apple';
    }

    // Web3 Setup
    setupWeb3() {
        const metamaskBtn = document.getElementById('metamask-connect');
        const coinbaseBtn = document.getElementById('coinbase-connect');
        const phantomBtn = document.getElementById('phantom-connect');

        if (metamaskBtn) {
            metamaskBtn.addEventListener('click', () => this.connectMetaMask());
        }

        if (coinbaseBtn) {
            coinbaseBtn.addEventListener('click', () => this.connectCoinbase());
        }

        if (phantomBtn) {
            phantomBtn.addEventListener('click', () => this.connectPhantom());
        }
    }

    async connectMetaMask() {
        if (typeof window.ethereum === 'undefined') {
            this.updateWalletStatus('MetaMaskがインストールされていません。<a href="https://metamask.io/download/" target="_blank">こちらからインストール</a>してください。', 'error');
            return;
        }

        // Check if MetaMask is specifically available
        let metamaskProvider = null;
        if (window.ethereum.isMetaMask) {
            metamaskProvider = window.ethereum;
        } else if (window.ethereum.providers) {
            metamaskProvider = window.ethereum.providers.find(p => p.isMetaMask);
        }

        if (!metamaskProvider) {
            this.updateWalletStatus('MetaMaskが検出されません。MetaMaskがインストールされ、有効になっていることを確認してください。', 'error');
            return;
        }

        try {
            this.updateWalletStatus('MetaMaskに接続中...', 'info');
            
            // Request account access using the specific MetaMask provider
            const accounts = await metamaskProvider.request({
                method: 'eth_requestAccounts'
            });

            if (accounts.length === 0) {
                this.updateWalletStatus('アカウントが選択されていません', 'error');
                return;
            }

            const address = accounts[0];
            this.updateWalletStatus(`接続済み: ${this.formatAddress(address)}`, 'success');

            // Sign message for authentication
            await this.authenticateWallet(address, 'metamask');

        } catch (error) {
            console.error('MetaMask connection error:', error);
            if (error.code === 4001) {
                this.updateWalletStatus('接続がキャンセルされました', 'error');
            } else if (error.code === -32002) {
                this.updateWalletStatus('MetaMaskで既にリクエストが処理中です。MetaMaskを確認してください。', 'error');
            } else {
                this.updateWalletStatus(`MetaMask接続エラー: ${error.message || 'Unknown error'}`, 'error');
            }
        }
    }


    async connectCoinbase() {
        // Check for Coinbase Wallet - comprehensive detection for browser extension
        let hasCoinbaseWallet = false;
        let coinbaseProvider = null;

        // Method 1: Direct check for Coinbase Wallet extension
        if (window.ethereum) {
            if (window.ethereum.isCoinbaseWallet) {
                hasCoinbaseWallet = true;
                coinbaseProvider = window.ethereum;
            } else if (window.ethereum.providers) {
                // Method 2: Check in providers array
                coinbaseProvider = window.ethereum.providers.find(p => p.isCoinbaseWallet);
                if (coinbaseProvider) {
                    hasCoinbaseWallet = true;
                }
            } else if (window.ethereum.selectedProvider?.isCoinbaseWallet) {
                // Method 3: Check selected provider
                hasCoinbaseWallet = true;
                coinbaseProvider = window.ethereum.selectedProvider;
            }
        }

        // Method 4: Check for Coinbase Wallet specific global object
        if (!hasCoinbaseWallet && window.coinbaseWalletExtension) {
            hasCoinbaseWallet = true;
            coinbaseProvider = window.coinbaseWalletExtension;
        }

        // Method 5: Check for CoinbaseWalletSDK
        if (!hasCoinbaseWallet && window.CoinbaseWalletSDK) {
            hasCoinbaseWallet = true;
            coinbaseProvider = window.ethereum;
        }

        // Method 6: Fallback - if ethereum exists but no specific Coinbase detection, try anyway
        if (!hasCoinbaseWallet && window.ethereum && !window.ethereum.isMetaMask) {
            // This might be Coinbase Wallet without proper identification
            hasCoinbaseWallet = true;
            coinbaseProvider = window.ethereum;
            console.log('Attempting connection with unidentified ethereum provider (might be Coinbase)');
        }

        if (!hasCoinbaseWallet) {
            this.updateWalletStatus('Coinbase Walletがインストールされていません。<a href="https://chrome.google.com/webstore/detail/coinbase-wallet-extension/hnfanknocfeofbddgcijnmhnfnkdnaad" target="_blank">Chrome拡張機能をインストール</a>してください。', 'error');
            return;
        }

        try {
            this.updateWalletStatus('Coinbase Walletに接続中...', 'info');
            
            // Use the detected Coinbase provider
            const provider = coinbaseProvider || window.ethereum;
            
            // Request account access
            const accounts = await provider.request({
                method: 'eth_requestAccounts'
            });

            if (accounts.length === 0) {
                this.updateWalletStatus('アカウントが選択されていません', 'error');
                return;
            }

            const address = accounts[0];
            this.updateWalletStatus(`接続済み: ${this.formatAddress(address)}`, 'success');

            // Sign message for authentication using the correct provider
            await this.authenticateWallet(address, 'coinbase', provider);

        } catch (error) {
            console.error('Coinbase Wallet connection error:', error);
            if (error.code === 4001) {
                this.updateWalletStatus('接続がキャンセルされました', 'error');
            } else if (error.code === -32002) {
                this.updateWalletStatus('Coinbase Walletで既にリクエストが処理中です。ウォレットを確認してください。', 'error');
            } else {
                this.updateWalletStatus(`Coinbase Wallet接続エラー: ${error.message || 'Unknown error'}`, 'error');
            }
        }
    }

    async connectPhantom() {
        // Check for Phantom Wallet (Solana)
        if (typeof window.solana === 'undefined') {
            this.updateWalletStatus('Phantom Walletがインストールされていません。<a href="https://phantom.app/" target="_blank">こちらからインストール</a>してください。', 'error');
            return;
        }

        try {
            this.updateWalletStatus('Phantom Walletに接続中...', 'info');
            
            // Connect to Phantom - use the correct method
            const response = await window.solana.connect({ onlyIfTrusted: false });
            const address = response.publicKey.toString();
            
            this.updateWalletStatus(`接続済み: ${this.formatAddress(address)}`, 'success');

            // Sign message for authentication
            await this.authenticatePhantomWallet(address);

        } catch (error) {
            console.error('Phantom Wallet connection error:', error);
            if (error.code === 4001 || error.message?.includes('User rejected')) {
                this.updateWalletStatus('接続がキャンセルされました', 'error');
            } else {
                this.updateWalletStatus(`Phantom Wallet接続エラー: ${error.message || 'Unknown error'}`, 'error');
            }
        }
    }

    async authenticateWallet(address, walletType, provider = null) {
        try {
            this.setLoading(true);
            this.updateWalletStatus('署名を要求中...', 'info');

            // Create message to sign
            const message = `AI Executive Suite へのログイン\n\nアドレス: ${address}\n時刻: ${new Date().toISOString()}`;
            
            // Use the specific provider if provided, otherwise use window.ethereum
            const walletProvider = provider || window.ethereum;
            
            let signature;
            if (walletType === 'metamask') {
                // Use personal_sign method for MetaMask
                signature = await walletProvider.request({
                    method: 'personal_sign',
                    params: [message, address]
                });
            } else if (walletType === 'coinbase') {
                // Use personal_sign method for Coinbase Wallet with specific provider
                signature = await walletProvider.request({
                    method: 'personal_sign',
                    params: [message, address]
                });
            }

            // Send to backend for verification
            const response = await fetch('/web3', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({
                    address,
                    message,
                    signature,
                    wallet_type: walletType
                })
            });

            const data = await response.json();

            if (response.ok) {
                this.showMessage('Web3ログインが完了しました！', 'success');
                setTimeout(() => {
                    window.location.href = '/';
                }, 1500);
            } else {
                this.updateWalletStatus(data.error || 'Web3認証に失敗しました', 'error');
            }

        } catch (error) {
            console.error('Web3 authentication error:', error);
            if (error.code === 4001) {
                this.updateWalletStatus('署名がキャンセルされました', 'error');
            } else {
                this.updateWalletStatus('Web3認証エラー', 'error');
            }
        } finally {
            this.setLoading(false);
        }
    }

    async authenticatePhantomWallet(address) {
        try {
            this.setLoading(true);
            this.updateWalletStatus('署名を要求中...', 'info');

            // Create message to sign for Phantom (Solana)
            const message = `AI Executive Suite へのログイン\n\nアドレス: ${address}\n時刻: ${new Date().toISOString()}`;
            
            // Convert message to Uint8Array for Phantom
            const encodedMessage = new TextEncoder().encode(message);
            
            // Sign message with Phantom - use the correct API for Phantom wallet
            let signedMessage;
            try {
                // Try the standard Phantom API first
                signedMessage = await window.solana.signMessage(encodedMessage, 'utf8');
            } catch (signError) {
                console.log('Standard signMessage failed, trying request method:', signError);
                // Fallback to request method
                signedMessage = await window.solana.request({
                    method: 'signMessage',
                    params: {
                        message: encodedMessage,
                        display: 'utf8'
                    }
                });
            }
            
            // Handle different signature formats
            let signature;
            if (signedMessage.signature) {
                // Convert Uint8Array signature to hex string
                signature = Array.from(signedMessage.signature, byte => byte.toString(16).padStart(2, '0')).join('');
            } else if (typeof signedMessage === 'string') {
                signature = signedMessage.replace('0x', '');
            } else {
                throw new Error('Invalid signature format');
            }

            // Send to backend for verification
            const response = await fetch('/auth/phantom', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({
                    address,
                    message,
                    signature: '0x' + signature,
                    wallet_type: 'phantom'
                })
            });

            const data = await response.json();

            if (response.ok) {
                this.showMessage('Phantom Walletログインが完了しました！', 'success');
                setTimeout(() => {
                    window.location.href = '/';
                }, 1500);
            } else {
                this.updateWalletStatus(data.error || 'Phantom認証に失敗しました', 'error');
            }

        } catch (error) {
            console.error('Phantom authentication error:', error);
            if (error.code === 4001 || error.message?.includes('User rejected')) {
                this.updateWalletStatus('署名がキャンセルされました', 'error');
            } else {
                this.updateWalletStatus(`Phantom認証エラー: ${error.message || 'Unknown error'}`, 'error');
            }
        } finally {
            this.setLoading(false);
        }
    }

    updateWalletStatus(message, type) {
        const statusEl = document.getElementById('wallet-status');
        if (statusEl) {
            statusEl.innerHTML = message; // Use innerHTML to support HTML links
            statusEl.className = `wallet-status ${type}`;
            statusEl.style.display = 'block';
        }
    }

    formatAddress(address) {
        return `${address.slice(0, 6)}...${address.slice(-4)}`;
    }

    // Message System
    setupMessageSystem() {
        const messageClose = document.querySelector('.message-close');
        if (messageClose) {
            messageClose.addEventListener('click', () => this.hideMessage());
        }
    }

    showMessage(text, type = 'info') {
        const messageEl = document.getElementById('message');
        const messageText = messageEl.querySelector('.message-text');
        const messageContent = messageEl.querySelector('.message-content');

        messageText.textContent = text;
        messageContent.className = `message-content ${type}`;
        messageEl.style.display = 'block';

        // Auto-hide after 5 seconds
        setTimeout(() => {
            this.hideMessage();
        }, 5000);
    }

    hideMessage() {
        const messageEl = document.getElementById('message');
        messageEl.style.display = 'none';
    }

    // Loading State
    setLoading(loading) {
        this.isLoading = loading;
        const loadingEl = document.getElementById('loading');
        const buttons = document.querySelectorAll('button');

        if (loading) {
            loadingEl.style.display = 'flex';
            buttons.forEach(btn => btn.disabled = true);
        } else {
            loadingEl.style.display = 'none';
            buttons.forEach(btn => btn.disabled = false);
        }
    }

    // Validation Helpers
    validateEmail(email) {
        const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
        return emailRegex.test(email);
    }

    // Language Management
    setupLanguageSelector() {
        const languageSelect = document.getElementById('language-select');
        if (languageSelect) {
            languageSelect.addEventListener('change', (e) => {
                this.changeLanguage(e.target.value);
            });
        }
    }

    changeLanguage(lang) {
        this.currentLanguage = lang;
        const t = this.translations[lang];
        
        // Update header subtitle
        const headerSubtitle = document.getElementById('header-subtitle');
        if (headerSubtitle) headerSubtitle.textContent = t.headerSubtitle;
        
        // Update tab buttons
        const tabBtns = document.querySelectorAll('.tab-btn');
        if (tabBtns[0]) tabBtns[0].textContent = t.signInTab;
        if (tabBtns[1]) tabBtns[1].textContent = t.signUpTab;
        
        // Update Sign In form
        const signinEmailLabel = document.querySelector('#signin-tab label[for="signin-email"]');
        if (signinEmailLabel) signinEmailLabel.textContent = t.emailLabel;
        
        const signinPasswordLabel = document.querySelector('#signin-tab label[for="signin-password"]');
        if (signinPasswordLabel) signinPasswordLabel.textContent = t.passwordLabel;
        
        const signinBtn = document.querySelector('#signin-tab .auth-btn');
        if (signinBtn) signinBtn.textContent = t.signInBtn;
        
        // Update Sign Up form
        const signupNameLabel = document.querySelector('#signup-tab label[for="signup-name"]');
        if (signupNameLabel) signupNameLabel.textContent = t.nameLabel;
        
        const signupUsernameLabel = document.querySelector('#signup-tab label[for="signup-username"]');
        if (signupUsernameLabel) signupUsernameLabel.textContent = t.usernameLabel;
        
        const signupEmailLabel = document.querySelector('#signup-tab label[for="signup-email"]');
        if (signupEmailLabel) signupEmailLabel.textContent = t.emailLabel;
        
        const signupPasswordLabel = document.querySelector('#signup-tab label[for="signup-password"]');
        if (signupPasswordLabel) signupPasswordLabel.textContent = t.passwordLabel;
        
        const signupConfirmLabel = document.querySelector('#signup-tab label[for="signup-confirm"]');
        if (signupConfirmLabel) signupConfirmLabel.textContent = t.confirmPasswordLabel;
        
        const signupBtn = document.querySelector('#signup-tab .auth-btn');
        if (signupBtn) signupBtn.textContent = t.signUpBtn;
        
        // Update divider
        const dividerSpan = document.querySelector('.divider span');
        if (dividerSpan) dividerSpan.textContent = t.orText;
        
        // Update OAuth buttons
        const googleBtn = document.getElementById('google-signin');
        if (googleBtn) {
            const googleText = googleBtn.querySelector('span') || googleBtn.childNodes[googleBtn.childNodes.length - 1];
            if (googleText) googleText.textContent = t.googleBtn;
        }
        
        const appleBtn = document.getElementById('apple-signin');
        if (appleBtn) {
            const appleText = appleBtn.querySelector('span') || appleBtn.childNodes[appleBtn.childNodes.length - 1];
            if (appleText) appleText.textContent = t.appleBtn;
        }
        
        // Update Web3 section
        const web3Title = document.querySelector('#web3-tab h3');
        if (web3Title) web3Title.textContent = t.web3Title;
        
        const web3Desc = document.querySelector('#web3-tab p');
        if (web3Desc) web3Desc.textContent = t.web3Desc;
        
        // Update Terms notice
        const termsText = document.getElementById('terms-text');
        if (termsText) termsText.textContent = t.termsText;
        
        // Update HTML lang attribute
        document.documentElement.lang = lang;
    }
}

// Initialize the login manager when the page loads
document.addEventListener('DOMContentLoaded', () => {
    new LoginManager();
});

// Handle OAuth callbacks
window.addEventListener('load', () => {
    const urlParams = new URLSearchParams(window.location.search);
    const error = urlParams.get('error');
    const success = urlParams.get('success');

    if (error) {
        const loginManager = new LoginManager();
        loginManager.showMessage(decodeURIComponent(error), 'error');
    }

    if (success) {
        const loginManager = new LoginManager();
        loginManager.showMessage(decodeURIComponent(success), 'success');
        setTimeout(() => {
            window.location.href = '/';
        }, 2000);
    }
});
