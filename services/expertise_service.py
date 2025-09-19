"""
Expertise Service for managing knowledge domains and expertise validation.
"""

import json
import logging
from datetime import datetime
from typing import Dict, List, Optional, Any, Tuple
from flask import current_app
from models import (
    db, PersonalityProfile, User, ExecutiveType, 
    IndustrySpecialization, ExpertiseLevel
)

logger = logging.getLogger(__name__)


class ExpertiseService:
    """Service for managing expertise domains and knowledge validation."""
    
    def __init__(self):
        self.domain_categories = self._get_domain_categories()
        self.industry_domains = self._get_industry_specific_domains()
        self.skill_levels = self._get_skill_level_definitions()
    
    def get_available_domains(self, executive_type: Optional[str] = None, 
                            industry: Optional[str] = None) -> Dict[str, List[str]]:
        """Get available expertise domains filtered by executive type and industry."""
        try:
            domains = {}
            
            # Get base domains for executive type
            if executive_type and executive_type in self.domain_categories:
                domains['core'] = self.domain_categories[executive_type].copy()
            else:
                # Return all domains if no specific type
                domains['core'] = []
                for exec_type, type_domains in self.domain_categories.items():
                    domains['core'].extend(type_domains)
                domains['core'] = list(set(domains['core']))  # Remove duplicates
            
            # Add industry-specific domains
            if industry and industry in self.industry_domains:
                domains['industry'] = self.industry_domains[industry]
            else:
                domains['industry'] = []
            
            # Add cross-functional domains
            domains['cross_functional'] = [
                'Project Management',
                'Change Management',
                'Communication',
                'Team Leadership',
                'Problem Solving',
                'Decision Making',
                'Negotiation',
                'Presentation Skills',
                'Data Analysis',
                'Process Improvement'
            ]
            
            # Add emerging/trending domains
            domains['emerging'] = [
                'Artificial Intelligence',
                'Machine Learning',
                'Digital Transformation',
                'Sustainability',
                'ESG (Environmental, Social, Governance)',
                'Remote Work Management',
                'Agile Methodologies',
                'Design Thinking',
                'Customer Experience',
                'Data Privacy'
            ]
            
            return domains
            
        except Exception as e:
            logger.error(f"Error getting available domains: {str(e)}")
            return {'core': [], 'industry': [], 'cross_functional': [], 'emerging': []}
    
    def validate_expertise_domains(self, domains: List[str], executive_type: str, 
                                 industry: Optional[str] = None) -> Dict[str, Any]:
        """Validate expertise domains for relevance and completeness."""
        try:
            available_domains = self.get_available_domains(executive_type, industry)
            all_available = []
            for category_domains in available_domains.values():
                all_available.extend(category_domains)
            
            validation_result = {
                'valid_domains': [],
                'invalid_domains': [],
                'suggested_domains': [],
                'completeness_score': 0.0,
                'relevance_score': 0.0,
                'recommendations': []
            }
            
            # Validate each domain
            for domain in domains:
                if domain in all_available:
                    validation_result['valid_domains'].append(domain)
                else:
                    validation_result['invalid_domains'].append(domain)
                    # Find similar domains
                    suggestions = self._find_similar_domains(domain, all_available)
                    validation_result['suggested_domains'].extend(suggestions)
            
            # Calculate completeness score (based on core domains coverage)
            core_domains = available_domains.get('core', [])
            if core_domains:
                covered_core = len([d for d in domains if d in core_domains])
                validation_result['completeness_score'] = min(covered_core / len(core_domains), 1.0)
            
            # Calculate relevance score
            if domains:
                relevant_count = len(validation_result['valid_domains'])
                validation_result['relevance_score'] = relevant_count / len(domains)
            
            # Generate recommendations
            validation_result['recommendations'] = self._generate_domain_recommendations(
                domains, executive_type, industry, validation_result
            )
            
            return validation_result
            
        except Exception as e:
            logger.error(f"Error validating expertise domains: {str(e)}")
            return {
                'valid_domains': domains,
                'invalid_domains': [],
                'suggested_domains': [],
                'completeness_score': 0.5,
                'relevance_score': 0.5,
                'recommendations': []
            }
    
    def suggest_domains_for_profile(self, executive_type: str, industry: str, 
                                  experience_level: str, current_domains: List[str] = None) -> List[str]:
        """Suggest expertise domains based on profile characteristics."""
        try:
            current_domains = current_domains or []
            available_domains = self.get_available_domains(executive_type, industry)
            
            suggestions = []
            
            # Get core domains for the executive type
            core_domains = available_domains.get('core', [])
            
            # Prioritize based on experience level
            if experience_level in ['expert', 'thought_leader']:
                # Senior levels should have broader expertise
                suggestions.extend(core_domains[:8])  # Top 8 core domains
                suggestions.extend(available_domains.get('cross_functional', [])[:4])
                suggestions.extend(available_domains.get('emerging', [])[:3])
            elif experience_level == 'senior':
                suggestions.extend(core_domains[:6])
                suggestions.extend(available_domains.get('cross_functional', [])[:3])
                suggestions.extend(available_domains.get('emerging', [])[:2])
            elif experience_level == 'intermediate':
                suggestions.extend(core_domains[:4])
                suggestions.extend(available_domains.get('cross_functional', [])[:2])
            else:  # junior
                suggestions.extend(core_domains[:3])
                suggestions.extend(available_domains.get('cross_functional', [])[:1])
            
            # Add industry-specific domains
            industry_domains = available_domains.get('industry', [])
            if industry_domains:
                max_industry = min(3, len(industry_domains))
                suggestions.extend(industry_domains[:max_industry])
            
            # Remove duplicates and already selected domains
            suggestions = list(set(suggestions))
            suggestions = [d for d in suggestions if d not in current_domains]
            
            # Limit to reasonable number
            return suggestions[:12]
            
        except Exception as e:
            logger.error(f"Error suggesting domains: {str(e)}")
            return []
    
    def create_custom_knowledge_base(self, user_id: int, knowledge_data: Dict[str, Any]) -> Dict[str, Any]:
        """Create a custom knowledge base entry."""
        try:
            knowledge_entry = {
                'id': f"kb_{user_id}_{datetime.utcnow().timestamp()}",
                'user_id': user_id,
                'title': knowledge_data.get('title', ''),
                'description': knowledge_data.get('description', ''),
                'category': knowledge_data.get('category', 'general'),
                'content': knowledge_data.get('content', ''),
                'tags': knowledge_data.get('tags', []),
                'source_type': knowledge_data.get('source_type', 'manual'),  # manual, document, url
                'source_reference': knowledge_data.get('source_reference', ''),
                'confidence_level': knowledge_data.get('confidence_level', 0.8),
                'created_at': datetime.utcnow().isoformat(),
                'updated_at': datetime.utcnow().isoformat()
            }
            
            # Validate knowledge entry
            validation_errors = self._validate_knowledge_entry(knowledge_entry)
            if validation_errors:
                return {
                    'success': False,
                    'errors': validation_errors
                }
            
            return {
                'success': True,
                'knowledge_entry': knowledge_entry
            }
            
        except Exception as e:
            logger.error(f"Error creating custom knowledge base: {str(e)}")
            return {
                'success': False,
                'errors': ['Failed to create knowledge base entry']
            }
    
    def validate_knowledge_sources(self, sources: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Validate knowledge sources for credibility and relevance."""
        try:
            validation_result = {
                'valid_sources': [],
                'invalid_sources': [],
                'credibility_scores': {},
                'recommendations': []
            }
            
            for source in sources:
                source_validation = self._validate_single_source(source)
                
                if source_validation['is_valid']:
                    validation_result['valid_sources'].append(source)
                    validation_result['credibility_scores'][source.get('id', '')] = source_validation['credibility_score']
                else:
                    validation_result['invalid_sources'].append(source)
                
                if source_validation.get('recommendations'):
                    validation_result['recommendations'].extend(source_validation['recommendations'])
            
            return validation_result
            
        except Exception as e:
            logger.error(f"Error validating knowledge sources: {str(e)}")
            return {
                'valid_sources': sources,
                'invalid_sources': [],
                'credibility_scores': {},
                'recommendations': []
            }
    
    def assess_expertise_level(self, domains: List[str], experience_years: int, 
                             industry: str, achievements: List[str] = None) -> Dict[str, Any]:
        """Assess and recommend expertise level based on domains and experience."""
        try:
            achievements = achievements or []
            
            assessment = {
                'recommended_level': 'intermediate',
                'confidence': 0.7,
                'reasoning': [],
                'domain_analysis': {},
                'suggestions': []
            }
            
            # Analyze domain breadth and depth
            domain_score = self._calculate_domain_score(domains, industry)
            assessment['domain_analysis'] = domain_score
            
            # Experience-based scoring
            experience_score = min(experience_years / 15.0, 1.0)  # Cap at 15 years for expert
            
            # Achievement-based scoring
            achievement_score = min(len(achievements) / 10.0, 1.0)  # Cap at 10 achievements
            
            # Combined score
            combined_score = (domain_score['score'] * 0.4 + 
                            experience_score * 0.4 + 
                            achievement_score * 0.2)
            
            # Determine level
            if combined_score >= 0.9:
                assessment['recommended_level'] = 'thought_leader'
                assessment['reasoning'].append('Exceptional domain expertise and extensive experience')
            elif combined_score >= 0.75:
                assessment['recommended_level'] = 'expert'
                assessment['reasoning'].append('Strong domain expertise with significant experience')
            elif combined_score >= 0.6:
                assessment['recommended_level'] = 'senior'
                assessment['reasoning'].append('Good domain coverage with solid experience')
            elif combined_score >= 0.4:
                assessment['recommended_level'] = 'intermediate'
                assessment['reasoning'].append('Moderate domain expertise with some experience')
            else:
                assessment['recommended_level'] = 'junior'
                assessment['reasoning'].append('Limited domain expertise or experience')
            
            assessment['confidence'] = combined_score
            
            # Generate suggestions for improvement
            assessment['suggestions'] = self._generate_expertise_suggestions(
                domains, experience_years, achievements, assessment['recommended_level']
            )
            
            return assessment
            
        except Exception as e:
            logger.error(f"Error assessing expertise level: {str(e)}")
            return {
                'recommended_level': 'intermediate',
                'confidence': 0.5,
                'reasoning': ['Unable to assess expertise level'],
                'domain_analysis': {},
                'suggestions': []
            }
    
    def get_expertise_testing_scenarios(self, domains: List[str], 
                                      executive_type: str) -> List[Dict[str, Any]]:
        """Generate testing scenarios to validate expertise in specific domains."""
        try:
            scenarios = []
            
            for domain in domains[:5]:  # Limit to 5 domains for testing
                scenario = self._create_domain_scenario(domain, executive_type)
                if scenario:
                    scenarios.append(scenario)
            
            return scenarios
            
        except Exception as e:
            logger.error(f"Error generating testing scenarios: {str(e)}")
            return []
    
    def _find_similar_domains(self, domain: str, available_domains: List[str]) -> List[str]:
        """Find similar domains using simple string matching."""
        domain_lower = domain.lower()
        similar = []
        
        for available in available_domains:
            available_lower = available.lower()
            
            # Check for partial matches
            if (domain_lower in available_lower or 
                available_lower in domain_lower or
                any(word in available_lower for word in domain_lower.split())):
                similar.append(available)
        
        return similar[:3]  # Return top 3 matches
    
    def _generate_domain_recommendations(self, domains: List[str], executive_type: str, 
                                       industry: Optional[str], validation_result: Dict) -> List[str]:
        """Generate recommendations for improving domain selection."""
        recommendations = []
        
        if validation_result['completeness_score'] < 0.6:
            recommendations.append("Consider adding more core domains for your executive type")
        
        if validation_result['relevance_score'] < 0.8:
            recommendations.append("Some domains may not be relevant - consider focusing on core competencies")
        
        if len(domains) < 3:
            recommendations.append("Add more expertise domains to create a comprehensive profile")
        elif len(domains) > 15:
            recommendations.append("Consider focusing on fewer, more specialized domains")
        
        if industry and not any(d in self.industry_domains.get(industry, []) for d in domains):
            recommendations.append(f"Consider adding {industry}-specific expertise domains")
        
        return recommendations
    
    def _validate_knowledge_entry(self, entry: Dict[str, Any]) -> List[str]:
        """Validate a knowledge base entry."""
        errors = []
        
        if not entry.get('title'):
            errors.append("Title is required")
        
        if not entry.get('content'):
            errors.append("Content is required")
        
        if entry.get('confidence_level', 0) < 0 or entry.get('confidence_level', 0) > 1:
            errors.append("Confidence level must be between 0 and 1")
        
        return errors
    
    def _validate_single_source(self, source: Dict[str, Any]) -> Dict[str, Any]:
        """Validate a single knowledge source."""
        validation = {
            'is_valid': True,
            'credibility_score': 0.7,
            'recommendations': []
        }
        
        source_type = source.get('type', '').lower()
        
        # Basic validation
        if not source.get('title') or not source.get('url'):
            validation['is_valid'] = False
            validation['recommendations'].append("Source must have title and URL")
            return validation
        
        # Credibility scoring based on source type
        credibility_scores = {
            'academic': 0.9,
            'industry_report': 0.8,
            'book': 0.8,
            'whitepaper': 0.7,
            'blog': 0.5,
            'news': 0.6,
            'social_media': 0.3
        }
        
        validation['credibility_score'] = credibility_scores.get(source_type, 0.5)
        
        # Additional recommendations
        if validation['credibility_score'] < 0.6:
            validation['recommendations'].append("Consider using more authoritative sources")
        
        return validation
    
    def _calculate_domain_score(self, domains: List[str], industry: str) -> Dict[str, Any]:
        """Calculate a score based on domain breadth and relevance."""
        score_data = {
            'score': 0.0,
            'breadth_score': 0.0,
            'depth_score': 0.0,
            'relevance_score': 0.0
        }
        
        if not domains:
            return score_data
        
        # Breadth score (number of domains)
        score_data['breadth_score'] = min(len(domains) / 10.0, 1.0)
        
        # Depth score (assume based on domain complexity)
        complex_domains = ['Strategic Planning', 'Financial Modeling', 'System Architecture', 'AI/ML']
        complex_count = len([d for d in domains if d in complex_domains])
        score_data['depth_score'] = min(complex_count / 5.0, 1.0)
        
        # Relevance score (industry alignment)
        industry_domains = self.industry_domains.get(industry, [])
        if industry_domains:
            relevant_count = len([d for d in domains if d in industry_domains])
            score_data['relevance_score'] = min(relevant_count / len(industry_domains), 1.0)
        else:
            score_data['relevance_score'] = 0.7  # Default for general domains
        
        # Combined score
        score_data['score'] = (score_data['breadth_score'] * 0.3 + 
                              score_data['depth_score'] * 0.4 + 
                              score_data['relevance_score'] * 0.3)
        
        return score_data
    
    def _generate_expertise_suggestions(self, domains: List[str], experience_years: int, 
                                      achievements: List[str], current_level: str) -> List[str]:
        """Generate suggestions for improving expertise level."""
        suggestions = []
        
        if len(domains) < 5:
            suggestions.append("Expand your expertise domains to demonstrate broader knowledge")
        
        if experience_years < 5 and current_level in ['senior', 'expert']:
            suggestions.append("Consider if your experience level aligns with your claimed expertise")
        
        if len(achievements) < 3:
            suggestions.append("Document more achievements to support your expertise level")
        
        if current_level == 'junior':
            suggestions.append("Focus on developing core competencies in 3-4 key domains")
        elif current_level == 'intermediate':
            suggestions.append("Consider specializing in 1-2 domains while maintaining broad knowledge")
        elif current_level in ['senior', 'expert']:
            suggestions.append("Consider thought leadership activities like speaking or writing")
        
        return suggestions
    
    def _create_domain_scenario(self, domain: str, executive_type: str) -> Optional[Dict[str, Any]]:
        """Create a testing scenario for a specific domain."""
        scenarios = {
            'Strategic Planning': {
                'scenario': 'Your company is facing increased competition and declining market share. Develop a 3-year strategic plan.',
                'key_points': ['Market analysis', 'Competitive positioning', 'Resource allocation', 'Timeline'],
                'difficulty': 'advanced'
            },
            'Financial Analysis': {
                'scenario': 'Evaluate the ROI of a $2M technology investment with projected benefits over 5 years.',
                'key_points': ['NPV calculation', 'Risk assessment', 'Payback period', 'Sensitivity analysis'],
                'difficulty': 'intermediate'
            },
            'Technology Strategy': {
                'scenario': 'Design a technology roadmap for digital transformation in a traditional manufacturing company.',
                'key_points': ['Current state assessment', 'Technology selection', 'Implementation phases', 'Change management'],
                'difficulty': 'advanced'
            },
            'Team Leadership': {
                'scenario': 'Your team is underperforming and morale is low. How would you address this situation?',
                'key_points': ['Root cause analysis', 'Communication strategy', 'Performance improvement', 'Team building'],
                'difficulty': 'intermediate'
            }
        }
        
        if domain in scenarios:
            scenario = scenarios[domain].copy()
            scenario['domain'] = domain
            scenario['executive_type'] = executive_type
            return scenario
        
        return None
    
    def _get_domain_categories(self) -> Dict[str, List[str]]:
        """Get domain categories by executive type."""
        return {
            'ceo': [
                'Strategic Planning',
                'Business Development',
                'Leadership',
                'Market Analysis',
                'Stakeholder Management',
                'Corporate Governance',
                'Mergers & Acquisitions',
                'Organizational Development',
                'Vision & Mission Development',
                'Board Relations',
                'Investor Relations',
                'Crisis Management'
            ],
            'cto': [
                'Software Architecture',
                'Technology Strategy',
                'Engineering Management',
                'System Design',
                'Innovation',
                'DevOps',
                'Cloud Computing',
                'Cybersecurity',
                'Data Architecture',
                'AI/ML',
                'Technical Due Diligence',
                'Platform Development'
            ],
            'cfo': [
                'Financial Analysis',
                'Budget Management',
                'Risk Assessment',
                'Investment Strategy',
                'Compliance',
                'Tax Planning',
                'Financial Reporting',
                'Treasury Management',
                'Audit',
                'Capital Structure',
                'Financial Planning & Analysis',
                'Cost Management'
            ]
        }
    
    def _get_industry_specific_domains(self) -> Dict[str, List[str]]:
        """Get industry-specific expertise domains."""
        return {
            'technology': [
                'Software Development',
                'Product Management',
                'Agile Methodologies',
                'API Design',
                'Mobile Development',
                'Web Development',
                'Database Management',
                'Quality Assurance'
            ],
            'finance': [
                'Investment Banking',
                'Portfolio Management',
                'Derivatives',
                'Credit Analysis',
                'Regulatory Compliance',
                'Quantitative Analysis',
                'Trading',
                'Wealth Management'
            ],
            'healthcare': [
                'Healthcare Administration',
                'Medical Device Regulation',
                'Clinical Trials',
                'Healthcare IT',
                'Patient Safety',
                'Healthcare Quality',
                'Medical Research',
                'Healthcare Policy'
            ],
            'manufacturing': [
                'Supply Chain Management',
                'Quality Control',
                'Lean Manufacturing',
                'Operations Management',
                'Industrial Engineering',
                'Safety Management',
                'Procurement',
                'Logistics'
            ],
            'retail': [
                'Merchandising',
                'Customer Experience',
                'Inventory Management',
                'E-commerce',
                'Brand Management',
                'Store Operations',
                'Supply Chain',
                'Market Research'
            ]
        }
    
    def _get_skill_level_definitions(self) -> Dict[str, Dict[str, Any]]:
        """Get skill level definitions and requirements."""
        return {
            'junior': {
                'experience_years': '0-3',
                'domain_count': '2-4',
                'description': 'Early career professional with foundational knowledge',
                'characteristics': ['Learning fundamentals', 'Guided work', 'Basic problem solving']
            },
            'intermediate': {
                'experience_years': '3-7',
                'domain_count': '4-7',
                'description': 'Experienced professional with solid competencies',
                'characteristics': ['Independent work', 'Moderate complexity', 'Some mentoring']
            },
            'senior': {
                'experience_years': '7-12',
                'domain_count': '6-10',
                'description': 'Senior professional with deep expertise',
                'characteristics': ['Complex problem solving', 'Team leadership', 'Strategic thinking']
            },
            'expert': {
                'experience_years': '12-20',
                'domain_count': '8-15',
                'description': 'Expert with recognized authority in field',
                'characteristics': ['Industry recognition', 'Innovation', 'Organizational impact']
            },
            'thought_leader': {
                'experience_years': '15+',
                'domain_count': '10+',
                'description': 'Thought leader shaping industry direction',
                'characteristics': ['Industry influence', 'Published work', 'Speaking engagements']
            }
        }