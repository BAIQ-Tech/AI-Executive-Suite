# AI Executive Suite 🏢

A comprehensive AI-powered executive management system featuring multilingual support, secure authentication, advanced decision-making capabilities, and enterprise-grade features.

## ✨ Features

### 🤖 AI Executives
- **AI CEO**: Strategic decision making and leadership guidance with real AI integration
- **AI CFO**: Financial analysis, budget management, and advanced financial modeling
- **AI CTO**: Technology strategy, development oversight, and technical decision support

### 🔐 Secure Authentication
- **Email/Password**: Traditional registration and login
- **Web3 Wallets**: MetaMask, Coinbase Wallet, Phantom support
- **OAuth**: Google and Apple Sign-In integration
- **Multi-Factor Authentication**: TOTP-based 2FA support
- **Cryptographic Verification**: Ethereum and Solana signature validation

### 🌍 Multilingual Support
- **Languages**: English, Japanese (日本語), Chinese (中文)
- **Dynamic UI**: Real-time language switching
- **Localized Content**: All interface elements translated

### 📊 Enhanced Management Features
- **Real AI Integration**: OpenAI GPT-4 powered intelligent responses
- **Decision Analytics**: Comprehensive tracking and analysis of executive decisions
- **Document Processing**: Upload and analyze business documents with AI context
- **Team Collaboration**: Multi-user decision review and commenting system
- **Advanced Financial Analytics**: ROI calculations, NPV analysis, and industry benchmarking
- **External Integrations**: CRM, ERP, and financial system connections
- **Mobile Responsive**: Optimized interface for mobile devices
- **Performance Monitoring**: Real-time system monitoring and health checks

### 🏗️ Enterprise Architecture
- **Microservices Design**: Modular service architecture for scalability
- **Vector Database**: Semantic document search with ChromaDB
- **Caching Layer**: Redis for improved performance
- **Background Tasks**: Celery for asynchronous processing
- **Comprehensive Logging**: Structured logging with performance tracking
- **Configuration Management**: Centralized configuration with environment support

## 🚀 Installation

### Quick Setup

1. **Clone the repository**
   ```bash
   git clone https://github.com/yourusername/AI-Executive-Suite.git
   cd AI-Executive-Suite
   ```

2. **Create virtual environment**
   ```bash
   python -m venv .venv
   source .venv/bin/activate  # On Windows: .venv\Scripts\activate
   ```

3. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

4. **Run setup script**
   ```bash
   python scripts/setup.py
   ```

5. **Configure environment**
   ```bash
   cp .env.example .env
   # Edit .env with your configuration (especially OPENAI_API_KEY)
   ```

6. **Run the application**
   ```bash
   python app.py
   ```

### Enhanced Setup (Production)

For production deployment with full features:

1. **Database Setup** (PostgreSQL recommended)
   ```bash
   # Install PostgreSQL and create database
   createdb ai_executive_suite
   
   # Update DATABASE_URL in .env
   DATABASE_URL=postgresql://username:password@localhost/ai_executive_suite
   ```

2. **Redis Setup** (for caching and sessions)
   ```bash
   # Install and start Redis
   redis-server
   
   # Update REDIS_URL in .env
   REDIS_URL=redis://localhost:6379/0
   ```

3. **Vector Database** (for document search)
   ```bash
   # ChromaDB will be automatically configured
   # Or set up external vector database
   ```

4. **API Keys Configuration**
   ```bash
   # Required for AI features
   OPENAI_API_KEY=sk-your-openai-api-key
   
   # Optional for integrations
   CRM_API_KEY=your-crm-api-key
   ERP_API_KEY=your-erp-api-key
   ```

## 📁 Project Structure

```
AI-Executive-Suite/
├── ai_ceo/                 # Core AI executive modules
├── services/               # Enhanced service modules
│   ├── ai_integration.py   # AI model integration
│   ├── analytics.py        # Business analytics
│   ├── collaboration.py    # Team collaboration
│   ├── document_processing.py # Document handling
│   └── registry.py         # Service management
├── config/                 # Configuration management
│   └── settings.py         # Centralized configuration
├── utils/                  # Utility modules
│   ├── logging.py          # Logging infrastructure
│   └── monitoring.py       # System monitoring
├── scripts/                # Setup and maintenance scripts
├── static/                 # Frontend assets
├── templates/              # HTML templates
└── requirements.txt        # Enhanced dependencies
```

## Usage

### AI_CEO Usage
```python
from ai_ceo import AI_CEO

# Create a new AI CEO
ceo = AI_CEO(name="Alex", company_name="Your Company")

# Get vision and mission
print(f"Vision: {ceo.get_vision_statement()}")
print(f"Mission: {ceo.get_mission_statement()}")

# Make a decision
context = "Should we expand to the European market next quarter?"
decision = ceo.make_decision(context)
print(f"Decision: {decision.decision}")
```

### AI_CTO Usage
```python
from ai_ceo import AI_CTO

# Create a new AI CTO
cto = AI_CTO(name="Sarah", company_name="Your Company")

# Get technical vision
print(f"Technical Vision: {cto.get_technical_vision()}")

# Make a technical decision
context = "We need to scale our backend architecture for 10x growth"
options = ["Microservices", "Serverless", "Vertical scaling"]
decision = cto.make_technical_decision(context, "architecture", options, "high")
print(f"Decision: {decision.decision}")

# Add new technology
cto.add_technology("Redis", "database", "7.x", "planned")
```

### AI_CFO Usage
```python
from ai_ceo import AI_CFO
from decimal import Decimal

# Create a new AI CFO
cfo = AI_CFO(name="Michael", company_name="Your Company")

# Get financial vision
print(f"Financial Vision: {cfo.get_financial_vision()}")

# Make a financial decision
context = "Should we increase marketing budget for Q4?"
options = ["Increase by $100K", "Reallocate from operations", "Maintain current"]
decision = cfo.make_financial_decision(context, "budget", options, Decimal('250000'))
print(f"Decision: {decision.decision}")

# Check budget utilization
utilization = cfo.get_budget_utilization()
print(f"Marketing utilization: {utilization['marketing']:.1f}%")

# Calculate ROI
roi = cfo.calculate_roi(Decimal('50000'), Decimal('150000'))
print(f"ROI: {roi}%")
```

## Examples

Run the example scripts:

```bash
# CEO example
python3 example.py

# CTO example  
python3 example_cto.py

# CFO example
python3 example_cfo.py
```

## License

MIT
