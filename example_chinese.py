#!/usr/bin/env python3
"""
Example demonstrating the AI_CEO class with multilingual support.
多言語対応のAI_CEOクラスのデモンストレーション。
演示支持多语言的AI_CEO类的示例。
"""

from ai_ceo.ceo import AI_CEO

def main():
    print("=== English AI CEO ===")
    # Create English CEO
    ceo_en = AI_CEO(name="Alex Chen", company_name="TechCorp", language="en")
    print(f"CEO: {ceo_en.name}")
    print(f"Company: {ceo_en.company_name}")
    print(f"Vision: {ceo_en.get_vision_statement()}")
    print(f"Mission: {ceo_en.get_mission_statement()}")
    
    # Make a decision in English
    decision_en = ceo_en.make_decision("Should we expand to new markets?", 
                                      ["Expand to Asia", "Focus on domestic market", "Partner with local companies"])
    print(f"Decision: {decision_en.decision}")
    print(f"Rationale: {decision_en.rationale}")
    print()
    
    print("=== 日本語AI CEO ===")
    # Create Japanese CEO
    ceo_ja = AI_CEO(name="田中社長", company_name="テクノロジー株式会社", language="ja")
    print(f"CEO: {ceo_ja.name}")
    print(f"会社: {ceo_ja.company_name}")
    print(f"ビジョン: {ceo_ja.get_vision_statement()}")
    print(f"ミッション: {ceo_ja.get_mission_statement()}")
    
    # Make a decision in Japanese
    decision_ja = ceo_ja.make_decision("新しい市場に拡大すべきでしょうか？", 
                                      ["アジアに拡大", "国内市場に集中", "現地企業と提携"])
    print(f"決定: {decision_ja.decision}")
    print(f"根拠: {decision_ja.rationale}")
    print()
    
    print("=== 中文AI CEO ===")
    # Create Chinese CEO
    ceo_zh = AI_CEO(name="陈总", company_name="科技公司", language="zh")
    print(f"CEO: {ceo_zh.name}")
    print(f"公司: {ceo_zh.company_name}")
    print(f"愿景: {ceo_zh.get_vision_statement()}")
    print(f"使命: {ceo_zh.get_mission_statement()}")
    
    # Make a decision in Chinese
    decision_zh = ceo_zh.make_decision("我们是否应该扩展到新市场？", 
                                      ["扩展到亚洲", "专注于国内市场", "与当地公司合作"])
    print(f"决策: {decision_zh.decision}")
    print(f"理由: {decision_zh.rationale}")
    print()
    
    print("=== Language Switching Demo ===")
    # Demonstrate language switching
    ceo = AI_CEO(name="Global CEO", company_name="International Corp", language="en")
    print("Initial (English):")
    print(f"Vision: {ceo.get_vision_statement()}")
    
    # Switch to Japanese
    ceo.set_language("ja")
    print("After switching to Japanese:")
    print(f"ビジョン: {ceo.get_vision_statement()}")
    
    # Switch to Chinese
    ceo.set_language("zh")
    print("After switching to Chinese:")
    print(f"愿景: {ceo.get_vision_statement()}")
    
    # Switch back to English
    ceo.set_language("en")
    print("After switching back to English:")
    print(f"Vision: {ceo.get_vision_statement()}")

if __name__ == "__main__":
    main()
