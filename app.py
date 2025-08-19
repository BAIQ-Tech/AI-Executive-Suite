from flask import Flask, render_template, request, jsonify, redirect, url_for, session
import json
from ai_ceo.ceo import AI_CEO
from ai_ceo.cfo import AI_CFO
from ai_ceo.cto import AI_CTO
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, login_required, current_user
import os
from dotenv import load_dotenv
from decimal import Decimal
import json
import random

# Load environment variables
load_dotenv()

app = Flask(__name__)
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'dev-secret-key-change-in-production')
app.config['SQLALCHEMY_DATABASE_URI'] = os.environ.get('DATABASE_URL', 'sqlite:///ai_executive_suite.db')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# Initialize extensions
from models import db
db.init_app(app)
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'
login_manager.login_message = 'ログインが必要です'

# Import models after db initialization
from models import User, LoginAttempt, UserSession

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

# Register blueprints
from auth import auth_bp
app.register_blueprint(auth_bp)

# Initialize the AI agents (English)
ceo_en = AI_CEO(name="Alex", company_name="Your Company")
cto_en = AI_CTO(name="Sarah", company_name="Your Company")
cfo_en = AI_CFO(name="Michael", company_name="Your Company")

# Initialize the AI agents (Japanese)
ceo_ja = AI_CEO(name="田中", company_name="あなたの会社", language="ja")
cto_ja = AI_CTO(name="佐藤", company_name="あなたの会社")
cfo_ja = AI_CFO(name="山田", company_name="あなたの会社")

# Initialize the AI agents (Chinese)
ceo_zh = AI_CEO(name="陈总", company_name="您的公司", language="zh")
cto_zh = AI_CTO(name="李总", company_name="您的公司")
cfo_zh = AI_CFO(name="王总", company_name="您的公司")

# Set Japanese visions and missions
ceo_ja.set_vision("業界で最も革新的で顧客中心の企業になること。")
ceo_ja.set_mission("最先端技術と優れたサービスを通じて、お客様、従業員、ステークホルダーに卓越した価値を提供すること。")

cto_ja.set_technical_vision("ビジネス成長を促進する、スケーラブルで安全かつ革新的な技術ソリューションを構築すること。")
cfo_ja.set_financial_vision("戦略的財務管理を通じて財務パフォーマンスを最適化し、持続可能な成長を確保し、株主価値を最大化すること。")

# Set Chinese visions and missions
cto_zh.set_technical_vision("构建可扩展、安全且创新的技术解决方案，推动业务增长。")
cfo_zh.set_financial_vision("通过战略财务管理优化财务绩效，确保可持续增长并最大化股东价值。")

# Japanese response templates
japanese_responses = {
    'ceo': [
        "戦略的観点から検討した結果、{decision}が最適だと判断いたします。{rationale}",
        "経営陣として総合的に分析し、{decision}を推奨いたします。{rationale}",
        "市場動向と企業戦略を考慮し、{decision}という結論に至りました。{rationale}"
    ],
    'cto': [
        "技術的な観点から分析した結果、{decision}が最適解だと考えます。{rationale}",
        "システム要件とアーキテクチャを検討し、{decision}を提案いたします。{rationale}",
        "技術的実現可能性を評価した結果、{decision}が適切だと判断します。{rationale}"
    ],
    'cfo': [
        "財務分析の結果、{decision}が最も合理的な選択だと考えます。{rationale}",
        "コスト効果とROIを検討し、{decision}を推奨いたします。{rationale}",
        "財務戦略の観点から、{decision}が適切だと判断いたします。{rationale}"
    ]
}

# Chinese response templates
chinese_responses = {
    'ceo': [
        "从战略角度考虑，我认为{decision}是最佳选择。{rationale}",
        "经过管理层综合分析，我们推荐{decision}。{rationale}",
        "考虑到市场趋势和企业战略，我们得出{decision}的结论。{rationale}"
    ],
    'cto': [
        "从技术角度分析，我认为{decision}是最优解。{rationale}",
        "考虑到系统需求和架构，我建议{decision}。{rationale}",
        "评估技术可行性后，我判断{decision}是合适的。{rationale}"
    ],
    'cfo': [
        "根据财务分析，我认为{decision}是最合理的选择。{rationale}",
        "考虑到成本效益和投资回报率，我推荐{decision}。{rationale}",
        "从财务战略角度，我判断{decision}是合适的。{rationale}"
    ]
}

def get_agents(lang='en'):
    if lang == 'ja':
        return ceo_ja, cto_ja, cfo_ja
    elif lang == 'zh':
        return ceo_zh, cto_zh, cfo_zh
    return ceo_en, cto_en, cfo_en

def generate_japanese_response(agent_type, context):
    templates = japanese_responses[agent_type]
    template = random.choice(templates)
    
    # Simple decision generation for Japanese
    decisions = {
        'ceo': [
            "積極的に推進する",
            "段階的に実施する", 
            "慎重に検討を続ける"
        ],
        'cto': [
            "新技術を導入する",
            "既存システムを最適化する",
            "段階的にアップグレードする"
        ],
        'cfo': [
            "投資を承認する",
            "予算を再配分する",
            "コスト削減を優先する"
        ]
    }
    
    rationales = {
        'ceo': [
            "市場機会と競合状況を総合的に判断した結果です。",
            "リスクとリターンのバランスを考慮しました。",
            "長期的な企業価値向上を重視しました。"
        ],
        'cto': [
            "技術的実現可能性とスケーラビリティを重視しました。",
            "セキュリティとパフォーマンスの両立を図りました。",
            "開発効率と保守性を考慮しました。"
        ],
        'cfo': [
            "ROIと財務リスクを慎重に評価しました。",
            "キャッシュフローへの影響を考慮しました。",
            "株主価値の最大化を目指しました。"
        ]
    }
    
    decision = random.choice(decisions[agent_type])
    rationale = random.choice(rationales[agent_type])
    
    return template.format(decision=decision, rationale=rationale), decision, rationale

def generate_chinese_response(agent_type, context):
    templates = chinese_responses[agent_type]
    template = random.choice(templates)
    
    # Simple decision generation for Chinese
    decisions = {
        'ceo': [
            "积极推进",
            "分阶段实施", 
            "谨慎继续考虑"
        ],
        'cto': [
            "引入新技术",
            "优化现有系统",
            "分阶段升级"
        ],
        'cfo': [
            "批准投资",
            "重新分配预算",
            "优先削减成本"
        ]
    }
    
    rationales = {
        'ceo': [
            "这是综合判断市场机会和竞争状况的结果。",
            "我们考虑了风险和回报的平衡。",
            "我们重视长期企业价值提升。"
        ],
        'cto': [
            "我们重视技术可行性和可扩展性。",
            "我们兼顾了安全性和性能。",
            "我们考虑了开发效率和可维护性。"
        ],
        'cfo': [
            "我们谨慎评估了投资回报率和财务风险。",
            "我们考虑了对现金流的影响。",
            "我们致力于最大化股东价值。"
        ]
    }
    
    decision = random.choice(decisions[agent_type])
    rationale = random.choice(rationales[agent_type])
    
    return template.format(decision=decision, rationale=rationale), decision, rationale

@app.route('/login')
def login():
    """Login page."""
    return render_template('login.html')

@app.route('/')
@login_required
def index():
    """Main page with agent interface."""
    return render_template('index.html')

@app.route('/logout')
@login_required
def logout():
    """Logout and redirect to login."""
    from flask_login import logout_user
    logout_user()
    return redirect(url_for('login'))

@app.route('/api/ceo/decision', methods=['POST'])
def ceo_decision():
    """Make a CEO decision."""
    data = request.json
    context = data.get('context', '')
    options = data.get('options', [])
    lang = data.get('lang', 'en')
    
    if not context:
        if lang == 'ja':
            error_msg = 'コンテキストが必要です'
        elif lang == 'zh':
            error_msg = '需要提供上下文'
        else:
            error_msg = 'Context is required'
        return jsonify({'error': error_msg}), 400
    
    ceo, _, _ = get_agents(lang)
    
    if lang == 'ja':
        response_text, decision_text, rationale_text = generate_japanese_response('ceo', context)
        decision = ceo.make_decision(context, options if options else None)
        decision.decision = decision_text
        decision.rationale = rationale_text
    elif lang == 'zh':
        response_text, decision_text, rationale_text = generate_chinese_response('ceo', context)
        decision = ceo.make_decision(context, options if options else None)
        decision.decision = decision_text
        decision.rationale = rationale_text
    else:
        decision = ceo.make_decision(context, options if options else None)
    
    return jsonify({
        'id': decision.id,
        'decision': decision.decision,
        'rationale': decision.rationale,
        'priority': decision.priority,
        'status': decision.status,
        'timestamp': decision.timestamp
    })

@app.route('/api/cto/decision', methods=['POST'])
def cto_decision():
    """Make a CTO technical decision."""
    data = request.json
    context = data.get('context', '')
    category = data.get('category', 'development')
    options = data.get('options', [])
    impact = data.get('impact', 'medium')
    lang = data.get('lang', 'en')
    
    if not context:
        if lang == 'ja':
            error_msg = 'コンテキストが必要です'
        elif lang == 'zh':
            error_msg = '需要提供上下文'
        else:
            error_msg = 'Context is required'
        return jsonify({'error': error_msg}), 400
    
    _, cto, _ = get_agents(lang)
    
    if lang == 'ja':
        response_text, decision_text, rationale_text = generate_japanese_response('cto', context)
        decision = cto.make_technical_decision(context, category, options if options else None, impact)
        decision.decision = decision_text
        decision.rationale = rationale_text
    elif lang == 'zh':
        response_text, decision_text, rationale_text = generate_chinese_response('cto', context)
        decision = cto.make_technical_decision(context, category, options if options else None, impact)
        decision.decision = decision_text
        decision.rationale = rationale_text
    else:
        decision = cto.make_technical_decision(context, category, options if options else None, impact)
    
    return jsonify({
        'id': decision.id,
        'decision': decision.decision,
        'rationale': decision.rationale,
        'priority': decision.priority,
        'category': decision.category,
        'impact': decision.impact,
        'status': decision.status,
        'timestamp': decision.timestamp
    })

@app.route('/api/cfo/decision', methods=['POST'])
def cfo_decision():
    """Make a CFO financial decision."""
    data = request.json
    context = data.get('context', '')
    category = data.get('category', 'budget')
    options = data.get('options', [])
    financial_impact = data.get('financial_impact', 0)
    risk_level = data.get('risk_level', 'medium')
    lang = data.get('lang', 'en')
    
    if not context:
        if lang == 'ja':
            error_msg = 'コンテキストが必要です'
        elif lang == 'zh':
            error_msg = '需要提供上下文'
        else:
            error_msg = 'Context is required'
        return jsonify({'error': error_msg}), 400
    
    _, _, cfo = get_agents(lang)
    
    if lang == 'ja':
        response_text, decision_text, rationale_text = generate_japanese_response('cfo', context)
        decision = cfo.make_financial_decision(context, category, options if options else None, Decimal(str(financial_impact)), risk_level)
        decision.decision = decision_text
        decision.rationale = rationale_text
    elif lang == 'zh':
        response_text, decision_text, rationale_text = generate_chinese_response('cfo', context)
        decision = cfo.make_financial_decision(context, category, options if options else None, Decimal(str(financial_impact)), risk_level)
        decision.decision = decision_text
        decision.rationale = rationale_text
    else:
        decision = cfo.make_financial_decision(context, category, options if options else None, Decimal(str(financial_impact)), risk_level)
    
    return jsonify({
        'id': decision.id,
        'decision': decision.decision,
        'rationale': decision.rationale,
        'priority': decision.priority,
        'category': decision.category,
        'financial_impact': str(decision.financial_impact),
        'risk_level': decision.risk_level,
        'status': decision.status,
        'timestamp': decision.timestamp
    })

@app.route('/api/ceo/vision')
def ceo_vision():
    """Get CEO vision and mission."""
    lang = request.args.get('lang', 'en')
    ceo, _, _ = get_agents(lang)
    
    return jsonify({
        'vision': ceo.get_vision_statement(),
        'mission': ceo.get_mission_statement(),
        'name': ceo.name,
        'company': ceo.company_name
    })

@app.route('/api/cto/info')
def cto_info():
    """Get CTO technical vision and stack."""
    lang = request.args.get('lang', 'en')
    _, cto, _ = get_agents(lang)
    
    tech_stack = {}
    for category in ['frontend', 'backend', 'database', 'infrastructure']:
        techs = cto.get_technology_stack_by_category(category)
        tech_stack[category] = [
            {
                'name': tech.name,
                'version': tech.version,
                'status': tech.status
            } for tech in techs
        ]
    
    return jsonify({
        'vision': cto.get_technical_vision(),
        'principles': cto.get_architecture_principles(),
        'tech_stack': tech_stack,
        'name': cto.name,
        'company': cto.company_name
    })

@app.route('/api/cfo/info')
def cfo_info():
    """Get CFO financial info."""
    lang = request.args.get('lang', 'en')
    _, _, cfo = get_agents(lang)
    
    budget_info = {}
    for category, item in cfo.budget.items():
        budget_info[category] = {
            'allocated': str(item.allocated_amount),
            'spent': str(item.spent_amount),
            'remaining': str(item.remaining_amount),
            'utilization': round(float(item.spent_amount / item.allocated_amount * 100), 1)
        }
    
    health_score, health_status = cfo.get_financial_health_score()
    
    return jsonify({
        'vision': cfo.get_financial_vision(),
        'principles': cfo.get_financial_principles(),
        'budget': budget_info,
        'health_score': health_score,
        'health_status': health_status,
        'name': cfo.name,
        'company': cfo.company_name
    })

@app.route('/api/decisions')
def all_decisions():
    """Get all decisions from all agents."""
    lang = request.args.get('lang', 'en')
    ceo, cto, cfo = get_agents(lang)
    
    decisions = {
        'ceo': [
            {
                'id': d.id,
                'decision': d.decision,
                'priority': d.priority,
                'status': d.status,
                'timestamp': d.timestamp
            } for d in ceo.decisions.values()
        ],
        'cto': [
            {
                'id': d.id,
                'decision': d.decision,
                'category': d.category,
                'priority': d.priority,
                'status': d.status,
                'timestamp': d.timestamp
            } for d in cto.technical_decisions.values()
        ],
        'cfo': [
            {
                'id': d.id,
                'decision': d.decision,
                'category': d.category,
                'priority': d.priority,
                'financial_impact': str(d.financial_impact),
                'status': d.status,
                'timestamp': d.timestamp
            } for d in cfo.financial_decisions.values()
        ]
    }
    
    return jsonify(decisions)

if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    app.run(debug=True, port=5000)
