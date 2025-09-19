#!/usr/bin/env python3
"""
Simple test script for expertise service functionality.
"""

import sys
from services.expertise_service import ExpertiseService

def test_expertise_service():
    """Test basic expertise service functionality."""
    
    print("Testing Expertise Service...")
    
    # Initialize service
    expertise_service = ExpertiseService()
    
    # Test 1: Get available domains
    print("\nTest 1: Getting available domains...")
    try:
        domains = expertise_service.get_available_domains('ceo', 'technology')
        
        assert 'core' in domains
        assert 'industry' in domains
        assert 'cross_functional' in domains
        assert 'emerging' in domains
        
        assert len(domains['core']) > 0
        assert 'Strategic Planning' in domains['core']
        assert len(domains['industry']) > 0
        
        print(f"✓ Retrieved domains: {len(domains['core'])} core, {len(domains['industry'])} industry")
        
    except Exception as e:
        print(f"✗ Failed to get available domains: {e}")
        return False
    
    # Test 2: Validate expertise domains
    print("\nTest 2: Validating expertise domains...")
    try:
        test_domains = ['Strategic Planning', 'Leadership', 'Invalid Domain', 'Technology Strategy']
        validation = expertise_service.validate_expertise_domains(
            test_domains, 'ceo', 'technology'
        )
        
        assert 'valid_domains' in validation
        assert 'invalid_domains' in validation
        assert 'completeness_score' in validation
        assert 'relevance_score' in validation
        
        assert len(validation['valid_domains']) > 0
        assert len(validation['invalid_domains']) > 0
        assert 'Invalid Domain' in validation['invalid_domains']
        
        print(f"✓ Validation completed: {len(validation['valid_domains'])} valid, {len(validation['invalid_domains'])} invalid")
        print(f"  Completeness: {validation['completeness_score']:.2f}, Relevance: {validation['relevance_score']:.2f}")
        
    except Exception as e:
        print(f"✗ Failed to validate domains: {e}")
        return False
    
    # Test 3: Suggest domains for profile
    print("\nTest 3: Suggesting domains for profile...")
    try:
        suggestions = expertise_service.suggest_domains_for_profile(
            'cto', 'technology', 'expert', ['Software Architecture']
        )
        
        assert isinstance(suggestions, list)
        assert len(suggestions) > 0
        assert 'Software Architecture' not in suggestions  # Should not suggest existing domains
        
        print(f"✓ Generated {len(suggestions)} domain suggestions")
        print(f"  Sample suggestions: {suggestions[:3]}")
        
    except Exception as e:
        print(f"✗ Failed to suggest domains: {e}")
        return False
    
    # Test 4: Create custom knowledge base
    print("\nTest 4: Creating custom knowledge base...")
    try:
        knowledge_data = {
            'title': 'Test Knowledge Entry',
            'description': 'A test knowledge base entry',
            'category': 'strategy',
            'content': 'This is test content for the knowledge base',
            'tags': ['test', 'strategy'],
            'confidence_level': 0.8
        }
        
        result = expertise_service.create_custom_knowledge_base(1, knowledge_data)
        
        assert result['success'] == True
        assert 'knowledge_entry' in result
        assert result['knowledge_entry']['title'] == knowledge_data['title']
        
        print("✓ Created custom knowledge base entry")
        
    except Exception as e:
        print(f"✗ Failed to create knowledge base: {e}")
        return False
    
    # Test 5: Validate knowledge sources
    print("\nTest 5: Validating knowledge sources...")
    try:
        test_sources = [
            {
                'id': 'source1',
                'title': 'Academic Paper on Strategy',
                'url': 'https://example.com/paper',
                'type': 'academic'
            },
            {
                'id': 'source2',
                'title': 'Blog Post',
                'url': 'https://example.com/blog',
                'type': 'blog'
            },
            {
                'id': 'invalid',
                'title': '',  # Invalid - no title
                'url': ''
            }
        ]
        
        validation = expertise_service.validate_knowledge_sources(test_sources)
        
        assert 'valid_sources' in validation
        assert 'invalid_sources' in validation
        assert 'credibility_scores' in validation
        
        assert len(validation['valid_sources']) == 2
        assert len(validation['invalid_sources']) == 1
        assert validation['credibility_scores']['source1'] > validation['credibility_scores']['source2']
        
        print(f"✓ Validated knowledge sources: {len(validation['valid_sources'])} valid, {len(validation['invalid_sources'])} invalid")
        
    except Exception as e:
        print(f"✗ Failed to validate knowledge sources: {e}")
        return False
    
    # Test 6: Assess expertise level
    print("\nTest 6: Assessing expertise level...")
    try:
        assessment = expertise_service.assess_expertise_level(
            ['Strategic Planning', 'Leadership', 'Financial Analysis', 'Technology Strategy'],
            10,  # 10 years experience
            'technology',
            ['Led major transformation', 'Published articles', 'Speaking engagements']
        )
        
        assert 'recommended_level' in assessment
        assert 'confidence' in assessment
        assert 'reasoning' in assessment
        assert 'suggestions' in assessment
        
        assert assessment['recommended_level'] in ['junior', 'intermediate', 'senior', 'expert', 'thought_leader']
        assert 0 <= assessment['confidence'] <= 1
        
        print(f"✓ Assessed expertise level: {assessment['recommended_level']} (confidence: {assessment['confidence']:.2f})")
        print(f"  Reasoning: {assessment['reasoning'][0] if assessment['reasoning'] else 'No reasoning provided'}")
        
    except Exception as e:
        print(f"✗ Failed to assess expertise level: {e}")
        return False
    
    # Test 7: Generate testing scenarios
    print("\nTest 7: Generating testing scenarios...")
    try:
        scenarios = expertise_service.get_expertise_testing_scenarios(
            ['Strategic Planning', 'Financial Analysis', 'Team Leadership'],
            'ceo'
        )
        
        assert isinstance(scenarios, list)
        assert len(scenarios) > 0
        
        for scenario in scenarios:
            assert 'scenario' in scenario
            assert 'key_points' in scenario
            assert 'difficulty' in scenario
            assert 'domain' in scenario
        
        print(f"✓ Generated {len(scenarios)} testing scenarios")
        print(f"  Sample scenario: {scenarios[0]['domain']} - {scenarios[0]['difficulty']}")
        
    except Exception as e:
        print(f"✗ Failed to generate testing scenarios: {e}")
        return False
    
    # Test 8: Get configuration data
    print("\nTest 8: Getting configuration data...")
    try:
        # Test domain categories
        categories = expertise_service.domain_categories
        assert 'ceo' in categories
        assert 'cto' in categories
        assert 'cfo' in categories
        assert len(categories['ceo']) > 0
        
        # Test industry domains
        industry_domains = expertise_service.industry_domains
        assert 'technology' in industry_domains
        assert 'finance' in industry_domains
        assert len(industry_domains['technology']) > 0
        
        # Test skill levels
        skill_levels = expertise_service.skill_levels
        assert 'junior' in skill_levels
        assert 'expert' in skill_levels
        assert 'experience_years' in skill_levels['junior']
        
        print("✓ Retrieved all configuration data successfully")
        
    except Exception as e:
        print(f"✗ Failed to get configuration data: {e}")
        return False
    
    print("\n🎉 All expertise service tests passed!")
    return True

if __name__ == '__main__':
    success = test_expertise_service()
    sys.exit(0 if success else 1)