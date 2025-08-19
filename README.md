# AI Executive Suite 🏢

A comprehensive AI-powered executive management system featuring multilingual support, secure authentication, and advanced decision-making capabilities.

## ✨ Features

### 🤖 AI Executives
- **AI CEO**: Strategic decision making and leadership guidance
- **AI CFO**: Financial analysis and budget management  
- **AI CTO**: Technology strategy and development oversight

### 🔐 Secure Authentication
- **Email/Password**: Traditional registration and login
- **Web3 Wallets**: MetaMask, Coinbase Wallet, Phantom support
- **OAuth**: Google and Apple Sign-In integration
- **Cryptographic Verification**: Ethereum and Solana signature validation

### 🌍 Multilingual Support
- **Languages**: English, Japanese (日本語), Chinese (中文)
- **Dynamic UI**: Real-time language switching
- **Localized Content**: All interface elements translated

### 📊 Management Features
- **Decision Tracking**: Comprehensive logging of executive decisions
- **User Sessions**: Secure session management
- **Interactive Interface**: Real-time communication with AI executives

## 🚀 Installation

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

4. **Set up environment variables**
   ```bash
   cp .env.example .env
   # Edit .env with your configuration
   ```

5. **Run the application**
   ```bash
   python app.py
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
