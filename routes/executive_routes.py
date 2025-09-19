"""
Executive Routes

API endpoints for AI executive decision making with real AI integration.
"""

import logging
from flask import Blueprint, request, jsonify, session
from flask_login import login_required, current_user
from datetime import datetime
from typing import Dict, Any, List, Optional

from models import db, Decision, DecisionStatus, DecisionPriority, ExecutiveType, RiskLevel, Document
from services.ai_integration import AIIntegrationService
from services.document_processing import DocumentProcessingService
from services.vector_database import VectorDatabaseService
from config.settings import config_manager

logger = logging.getLogger(__name__)

# Create blueprint
executive_bp = Blueprint('executive', __name__, url_prefix='/api/executive')

# Initialize services
ai_service = None
doc_service = None
vector_service = None

def init_services():
    """Initialize services with configuration"""
    global ai_service, doc_service, vector_service
    
    try:
        ai_config = config_manager.get_service_config('ai_integration')
        ai_service = AIIntegrationService(ai_config)
        
        doc_config = config_manager.get_service_config('document_processing')
        doc_service = DocumentProcessingService(doc_config)
        
        vector_config = config_manager.get_service_config('ai_integration')['vector_db']
        vector_service = VectorDatabaseService(vector_config)
        
        logger.info("Executive services initialized successfully")
    except Exception as e:
        logger.error(f"Failed to initialize executive services: {e}")
        # Continue without services for development
        pass

# Initialize services on module load
init_services()


@executive_bp.route('/ceo/decision', methods=['POST'])
@login_required
def create_ceo_decision():
    """
    Create a new CEO decision using AI integration
    
    Expected JSON payload:
    {
        "context": "Business context or problem statement",
        "title": "Decision title",
        "category": "strategic|operational|financial",
        "priority": "low|medium|high|critical",
        "options": ["Option 1", "Option 2"],  // optional
        "document_ids": [1, 2, 3]  // optional document references
    }
    """
    try:
        data = request.get_json()
        if not data:
            return jsonify({'error': 'No JSON data provided'}), 400
        
        # Validate required fields
        context = data.get('context', '').strip()
        title = data.get('title', '').strip()
        
        if not context:
            return jsonify({'error': 'Context is required'}), 400
        
        if not title:
            return jsonify({'error': 'Title is required'}), 400
        
        # Extract optional fields
        category = data.get('category', 'strategic')
        priority_str = data.get('priority', 'medium')
        options = data.get('options', [])
        document_ids = data.get('document_ids', [])
        
        # Convert priority string to enum
        priority_map = {
            'low': DecisionPriority.LOW,
            'medium': DecisionPriority.MEDIUM,
            'high': DecisionPriority.HIGH,
            'critical': DecisionPriority.CRITICAL
        }
        priority = priority_map.get(priority_str, DecisionPriority.MEDIUM)
        
        # Get document context if document IDs provided
        document_context = ""
        referenced_documents = []
        
        if document_ids and vector_service:
            try:
                for doc_id in document_ids:
                    document = Document.query.get(doc_id)
                    if document and document.user_id == current_user.id:
                        referenced_documents.append(document)
                        
                        # Get relevant context from document
                        if document.summary:
                            document_context += f"\n\nDocument: {document.filename}\nSummary: {document.summary}"
                        
                        # Get semantic search results for the context
                        search_results = vector_service.search_similar_content(
                            query=context,
                            collection_name=f"user_{current_user.id}_documents",
                            limit=3
                        )
                        
                        for result in search_results:
                            if result.get('document_id') == str(doc_id):
                                document_context += f"\nRelevant content: {result.get('content', '')[:500]}..."
                                break
                                
            except Exception as e:
                logger.warning(f"Failed to get document context: {e}")
                # Continue without document context
        
        # Get conversation history from session
        conversation_history = session.get('ceo_conversation_history', [])
        
        # Generate AI response using the AI integration service
        if ai_service:
            try:
                executive_response = ai_service.generate_executive_response(
                    executive_type='ceo',
                    context=context,
                    conversation_history=conversation_history,
                    document_context=document_context,
                    options=options
                )
                
                # Extract decision components from AI response
                decision_text = executive_response.decision
                rationale = executive_response.rationale
                confidence_score = executive_response.confidence_score
                financial_impact = executive_response.financial_impact
                risk_level_str = executive_response.risk_level
                
                # Convert risk level string to enum
                risk_map = {
                    'low': RiskLevel.LOW,
                    'medium': RiskLevel.MEDIUM,
                    'high': RiskLevel.HIGH,
                    'critical': RiskLevel.CRITICAL
                }
                risk_level = risk_map.get(risk_level_str, RiskLevel.MEDIUM)
                
            except Exception as e:
                logger.error(f"AI service failed, using fallback: {e}")
                # Fallback to basic response
                decision_text = f"Proceed with the recommended approach based on the provided context."
                rationale = f"Based on strategic analysis of the situation: {context[:200]}..."
                confidence_score = 0.7
                financial_impact = None
                risk_level = RiskLevel.MEDIUM
        else:
            # Fallback when AI service is not available
            decision_text = f"Proceed with the recommended approach based on the provided context."
            rationale = f"Based on strategic analysis of the situation: {context[:200]}..."
            confidence_score = 0.7
            financial_impact = None
            risk_level = RiskLevel.MEDIUM
        
        # Create decision record
        decision = Decision(
            user_id=current_user.id,
            title=title,
            context=context,
            decision=decision_text,
            rationale=rationale,
            executive_type=ExecutiveType.CEO,
            category=category,
            priority=priority,
            confidence_score=confidence_score,
            financial_impact=financial_impact,
            risk_level=risk_level,
            ai_model_version=ai_service.client.model if ai_service else 'fallback',
            prompt_version='1.0'
        )
        
        # Add document references
        for doc in referenced_documents:
            decision.add_document(doc)
        
        # Update conversation history
        conversation_history.append({
            'role': 'user',
            'content': context,
            'timestamp': datetime.utcnow().isoformat()
        })
        conversation_history.append({
            'role': 'assistant',
            'content': decision_text,
            'timestamp': datetime.utcnow().isoformat()
        })
        
        # Keep only last 10 exchanges to manage memory
        if len(conversation_history) > 20:
            conversation_history = conversation_history[-20:]
        
        session['ceo_conversation_history'] = conversation_history
        decision.set_conversation_history(conversation_history)
        
        # Save to database
        db.session.add(decision)
        db.session.commit()
        
        logger.info(f"CEO decision created: {decision.id} for user {current_user.id}")
        
        return jsonify({
            'success': True,
            'decision': decision.to_dict(),
            'message': 'CEO decision created successfully'
        }), 201
        
    except Exception as e:
        logger.error(f"Error creating CEO decision: {e}")
        db.session.rollback()
        return jsonify({'error': 'Failed to create decision'}), 500


@executive_bp.route('/ceo/decisions', methods=['GET'])
@login_required
def get_ceo_decisions():
    """Get all CEO decisions for the current user"""
    try:
        # Get query parameters
        status = request.args.get('status')
        category = request.args.get('category')
        limit = int(request.args.get('limit', 50))
        offset = int(request.args.get('offset', 0))
        
        # Build query
        query = Decision.query.filter_by(
            user_id=current_user.id,
            executive_type=ExecutiveType.CEO
        )
        
        if status:
            try:
                status_enum = DecisionStatus(status)
                query = query.filter_by(status=status_enum)
            except ValueError:
                return jsonify({'error': f'Invalid status: {status}'}), 400
        
        if category:
            query = query.filter_by(category=category)
        
        # Order by creation date (newest first)
        query = query.order_by(Decision.created_at.desc())
        
        # Apply pagination
        decisions = query.offset(offset).limit(limit).all()
        total_count = query.count()
        
        return jsonify({
            'success': True,
            'decisions': [decision.to_dict() for decision in decisions],
            'total_count': total_count,
            'limit': limit,
            'offset': offset
        })
        
    except Exception as e:
        logger.error(f"Error getting CEO decisions: {e}")
        return jsonify({'error': 'Failed to retrieve decisions'}), 500


@executive_bp.route('/ceo/decision/<int:decision_id>', methods=['GET'])
@login_required
def get_ceo_decision(decision_id):
    """Get a specific CEO decision"""
    try:
        decision = Decision.query.filter_by(
            id=decision_id,
            user_id=current_user.id,
            executive_type=ExecutiveType.CEO
        ).first()
        
        if not decision:
            return jsonify({'error': 'Decision not found'}), 404
        
        return jsonify({
            'success': True,
            'decision': decision.to_dict()
        })
        
    except Exception as e:
        logger.error(f"Error getting CEO decision {decision_id}: {e}")
        return jsonify({'error': 'Failed to retrieve decision'}), 500


@executive_bp.route('/ceo/decision/<int:decision_id>/status', methods=['PUT'])
@login_required
def update_ceo_decision_status(decision_id):
    """
    Update the status of a CEO decision
    
    Expected JSON payload:
    {
        "status": "pending|in_progress|completed|rejected|under_review",
        "notes": "Optional implementation notes"
    }
    """
    try:
        decision = Decision.query.filter_by(
            id=decision_id,
            user_id=current_user.id,
            executive_type=ExecutiveType.CEO
        ).first()
        
        if not decision:
            return jsonify({'error': 'Decision not found'}), 404
        
        data = request.get_json()
        if not data:
            return jsonify({'error': 'No JSON data provided'}), 400
        
        status_str = data.get('status')
        notes = data.get('notes', '')
        
        if not status_str:
            return jsonify({'error': 'Status is required'}), 400
        
        # Convert status string to enum
        try:
            new_status = DecisionStatus(status_str)
        except ValueError:
            return jsonify({'error': f'Invalid status: {status_str}'}), 400
        
        # Update decision
        decision.update_status(new_status, notes)
        db.session.commit()
        
        logger.info(f"CEO decision {decision_id} status updated to {status_str}")
        
        return jsonify({
            'success': True,
            'decision': decision.to_dict(),
            'message': 'Decision status updated successfully'
        })
        
    except Exception as e:
        logger.error(f"Error updating CEO decision status: {e}")
        db.session.rollback()
        return jsonify({'error': 'Failed to update decision status'}), 500


@executive_bp.route('/ceo/decision/<int:decision_id>/outcome', methods=['PUT'])
@login_required
def update_ceo_decision_outcome(decision_id):
    """
    Update the outcome rating of a CEO decision
    
    Expected JSON payload:
    {
        "outcome_rating": 1-5,  // 1=Poor, 2=Below Average, 3=Average, 4=Good, 5=Excellent
        "notes": "Optional outcome notes"
    }
    """
    try:
        decision = Decision.query.filter_by(
            id=decision_id,
            user_id=current_user.id,
            executive_type=ExecutiveType.CEO
        ).first()
        
        if not decision:
            return jsonify({'error': 'Decision not found'}), 404
        
        data = request.get_json()
        if not data:
            return jsonify({'error': 'No JSON data provided'}), 400
        
        outcome_rating = data.get('outcome_rating')
        notes = data.get('notes', '')
        
        if outcome_rating is None:
            return jsonify({'error': 'Outcome rating is required'}), 400
        
        if not isinstance(outcome_rating, int) or outcome_rating < 1 or outcome_rating > 5:
            return jsonify({'error': 'Outcome rating must be an integer between 1 and 5'}), 400
        
        # Update decision
        decision.outcome_rating = outcome_rating
        if notes:
            decision.implementation_notes = notes
        
        # Calculate effectiveness score
        decision.calculate_effectiveness()
        
        db.session.commit()
        
        logger.info(f"CEO decision {decision_id} outcome updated: rating={outcome_rating}")
        
        return jsonify({
            'success': True,
            'decision': decision.to_dict(),
            'message': 'Decision outcome updated successfully'
        })
        
    except Exception as e:
        logger.error(f"Error updating CEO decision outcome: {e}")
        db.session.rollback()
        return jsonify({'error': 'Failed to update decision outcome'}), 500


@executive_bp.route('/ceo/conversation/clear', methods=['POST'])
@login_required
def clear_ceo_conversation():
    """Clear the CEO conversation history"""
    try:
        session.pop('ceo_conversation_history', None)
        
        return jsonify({
            'success': True,
            'message': 'CEO conversation history cleared'
        })
        
    except Exception as e:
        logger.error(f"Error clearing CEO conversation: {e}")
        return jsonify({'error': 'Failed to clear conversation'}), 500


@executive_bp.route('/cto/decision', methods=['POST'])
@login_required
def create_cto_decision():
    """
    Create a new CTO decision using AI integration
    
    Expected JSON payload:
    {
        "context": "Technical context or problem statement",
        "title": "Decision title",
        "category": "architecture|development|infrastructure|security",
        "priority": "low|medium|high|critical",
        "options": ["Option 1", "Option 2"],  // optional
        "document_ids": [1, 2, 3],  // optional document references
        "technical_requirements": {  // optional technical specifications
            "scalability": "high|medium|low",
            "performance": "critical|important|normal",
            "security": "critical|important|normal",
            "maintainability": "high|medium|low"
        }
    }
    """
    try:
        data = request.get_json()
        if not data:
            return jsonify({'error': 'No JSON data provided'}), 400
        
        # Validate required fields
        context = data.get('context', '').strip()
        title = data.get('title', '').strip()
        
        if not context:
            return jsonify({'error': 'Context is required'}), 400
        
        if not title:
            return jsonify({'error': 'Title is required'}), 400
        
        # Extract optional fields
        category = data.get('category', 'development')
        priority_str = data.get('priority', 'medium')
        options = data.get('options', [])
        document_ids = data.get('document_ids', [])
        tech_requirements = data.get('technical_requirements', {})
        
        # Convert priority string to enum
        priority_map = {
            'low': DecisionPriority.LOW,
            'medium': DecisionPriority.MEDIUM,
            'high': DecisionPriority.HIGH,
            'critical': DecisionPriority.CRITICAL
        }
        priority = priority_map.get(priority_str, DecisionPriority.MEDIUM)
        
        # Get document context if document IDs provided
        document_context = ""
        referenced_documents = []
        
        if document_ids and vector_service:
            try:
                for doc_id in document_ids:
                    document = Document.query.get(doc_id)
                    if document and document.user_id == current_user.id:
                        referenced_documents.append(document)
                        
                        # Get relevant context from document
                        if document.summary:
                            document_context += f"\n\nDocument: {document.filename}\nSummary: {document.summary}"
                        
                        # Get semantic search results for the context
                        search_results = vector_service.search_similar_content(
                            query=context,
                            collection_name=f"user_{current_user.id}_documents",
                            limit=3
                        )
                        
                        for result in search_results:
                            if result.get('document_id') == str(doc_id):
                                document_context += f"\nRelevant content: {result.get('content', '')[:500]}..."
                                break
                                
            except Exception as e:
                logger.warning(f"Failed to get document context: {e}")
        
        # Add technical requirements to context
        if tech_requirements:
            tech_context = "\n\nTechnical Requirements:\n"
            for req, level in tech_requirements.items():
                tech_context += f"- {req.title()}: {level}\n"
            document_context += tech_context
        
        # Get conversation history from session
        conversation_history = session.get('cto_conversation_history', [])
        
        # Generate AI response using the AI integration service
        if ai_service:
            try:
                executive_response = ai_service.generate_executive_response(
                    executive_type='cto',
                    context=context,
                    conversation_history=conversation_history,
                    document_context=document_context,
                    options=options
                )
                
                # Extract decision components from AI response
                decision_text = executive_response.decision
                rationale = executive_response.rationale
                confidence_score = executive_response.confidence_score
                financial_impact = executive_response.financial_impact
                risk_level_str = executive_response.risk_level
                
                # Convert risk level string to enum
                risk_map = {
                    'low': RiskLevel.LOW,
                    'medium': RiskLevel.MEDIUM,
                    'high': RiskLevel.HIGH,
                    'critical': RiskLevel.CRITICAL
                }
                risk_level = risk_map.get(risk_level_str, RiskLevel.MEDIUM)
                
            except Exception as e:
                logger.error(f"AI service failed, using fallback: {e}")
                # Fallback to basic response
                decision_text = f"Proceed with technical analysis and architecture review before implementation."
                rationale = f"Based on technical evaluation of the requirements: {context[:200]}..."
                confidence_score = 0.7
                financial_impact = None
                risk_level = RiskLevel.MEDIUM
        else:
            # Fallback when AI service is not available
            decision_text = f"Proceed with technical analysis and architecture review before implementation."
            rationale = f"Based on technical evaluation of the requirements: {context[:200]}..."
            confidence_score = 0.7
            financial_impact = None
            risk_level = RiskLevel.MEDIUM
        
        # Create decision record
        decision = Decision(
            user_id=current_user.id,
            title=title,
            context=context,
            decision=decision_text,
            rationale=rationale,
            executive_type=ExecutiveType.CTO,
            category=category,
            priority=priority,
            confidence_score=confidence_score,
            financial_impact=financial_impact,
            risk_level=risk_level,
            ai_model_version=ai_service.client.model if ai_service else 'fallback',
            prompt_version='1.0'
        )
        
        # Add document references
        for doc in referenced_documents:
            decision.add_document(doc)
        
        # Update conversation history
        conversation_history.append({
            'role': 'user',
            'content': context,
            'timestamp': datetime.utcnow().isoformat()
        })
        conversation_history.append({
            'role': 'assistant',
            'content': decision_text,
            'timestamp': datetime.utcnow().isoformat()
        })
        
        # Keep only last 10 exchanges to manage memory
        if len(conversation_history) > 20:
            conversation_history = conversation_history[-20:]
        
        session['cto_conversation_history'] = conversation_history
        decision.set_conversation_history(conversation_history)
        
        # Save to database
        db.session.add(decision)
        db.session.commit()
        
        logger.info(f"CTO decision created: {decision.id} for user {current_user.id}")
        
        return jsonify({
            'success': True,
            'decision': decision.to_dict(),
            'message': 'CTO decision created successfully'
        }), 201
        
    except Exception as e:
        logger.error(f"Error creating CTO decision: {e}")
        db.session.rollback()
        return jsonify({'error': 'Failed to create decision'}), 500


@executive_bp.route('/cto/decisions', methods=['GET'])
@login_required
def get_cto_decisions():
    """Get all CTO decisions for the current user"""
    try:
        # Get query parameters
        status = request.args.get('status')
        category = request.args.get('category')
        limit = int(request.args.get('limit', 50))
        offset = int(request.args.get('offset', 0))
        
        # Build query
        query = Decision.query.filter_by(
            user_id=current_user.id,
            executive_type=ExecutiveType.CTO
        )
        
        if status:
            try:
                status_enum = DecisionStatus(status)
                query = query.filter_by(status=status_enum)
            except ValueError:
                return jsonify({'error': f'Invalid status: {status}'}), 400
        
        if category:
            query = query.filter_by(category=category)
        
        # Order by creation date (newest first)
        query = query.order_by(Decision.created_at.desc())
        
        # Apply pagination
        decisions = query.offset(offset).limit(limit).all()
        total_count = query.count()
        
        return jsonify({
            'success': True,
            'decisions': [decision.to_dict() for decision in decisions],
            'total_count': total_count,
            'limit': limit,
            'offset': offset
        })
        
    except Exception as e:
        logger.error(f"Error getting CTO decisions: {e}")
        return jsonify({'error': 'Failed to retrieve decisions'}), 500


@executive_bp.route('/cto/decision/<int:decision_id>', methods=['GET'])
@login_required
def get_cto_decision(decision_id):
    """Get a specific CTO decision"""
    try:
        decision = Decision.query.filter_by(
            id=decision_id,
            user_id=current_user.id,
            executive_type=ExecutiveType.CTO
        ).first()
        
        if not decision:
            return jsonify({'error': 'Decision not found'}), 404
        
        return jsonify({
            'success': True,
            'decision': decision.to_dict()
        })
        
    except Exception as e:
        logger.error(f"Error getting CTO decision {decision_id}: {e}")
        return jsonify({'error': 'Failed to retrieve decision'}), 500


@executive_bp.route('/cto/architecture-analysis', methods=['POST'])
@login_required
def get_architecture_analysis():
    """
    Get technical architecture analysis
    
    Expected JSON payload:
    {
        "context": "Technical architecture context",
        "current_architecture": "Description of current system",
        "requirements": ["Requirement 1", "Requirement 2"],
        "constraints": ["Constraint 1", "Constraint 2"]
    }
    """
    try:
        data = request.get_json()
        if not data:
            return jsonify({'error': 'No JSON data provided'}), 400
        
        context = data.get('context', '').strip()
        current_arch = data.get('current_architecture', '')
        requirements = data.get('requirements', [])
        constraints = data.get('constraints', [])
        
        if not context:
            return jsonify({'error': 'Context is required'}), 400
        
        # Build comprehensive analysis context
        analysis_context = f"Architecture Analysis Request: {context}"
        
        if current_arch:
            analysis_context += f"\n\nCurrent Architecture: {current_arch}"
        
        if requirements:
            analysis_context += f"\n\nRequirements:\n" + "\n".join(f"- {req}" for req in requirements)
        
        if constraints:
            analysis_context += f"\n\nConstraints:\n" + "\n".join(f"- {constraint}" for constraint in constraints)
        
        # Get conversation history
        conversation_history = session.get('cto_conversation_history', [])
        
        # Generate AI response
        if ai_service:
            try:
                executive_response = ai_service.generate_executive_response(
                    executive_type='cto',
                    context=analysis_context,
                    conversation_history=conversation_history
                )
                
                analysis = {
                    "analysis": executive_response.decision,
                    "rationale": executive_response.rationale,
                    "confidence_score": executive_response.confidence_score,
                    "risk_level": executive_response.risk_level,
                    "recommendations": executive_response.decision.split('\n')[:5],  # First 5 lines as recommendations
                    "ai_powered": True
                }
                
            except Exception as e:
                logger.error(f"AI architecture analysis failed: {e}")
                analysis = {
                    "analysis": "Technical architecture analysis requires evaluation of scalability, maintainability, security, and performance requirements.",
                    "rationale": "Based on standard architectural patterns and best practices.",
                    "confidence_score": 0.6,
                    "risk_level": "medium",
                    "recommendations": [
                        "Conduct thorough requirements analysis",
                        "Evaluate existing system constraints",
                        "Consider scalability requirements",
                        "Assess security implications",
                        "Plan for maintainability"
                    ],
                    "ai_powered": False
                }
        else:
            analysis = {
                "analysis": "Technical architecture analysis requires evaluation of scalability, maintainability, security, and performance requirements.",
                "rationale": "Based on standard architectural patterns and best practices.",
                "confidence_score": 0.6,
                "risk_level": "medium",
                "recommendations": [
                    "Conduct thorough requirements analysis",
                    "Evaluate existing system constraints",
                    "Consider scalability requirements",
                    "Assess security implications",
                    "Plan for maintainability"
                ],
                "ai_powered": False
            }
        
        return jsonify({
            'success': True,
            'analysis': analysis
        })
        
    except Exception as e:
        logger.error(f"Error in architecture analysis: {e}")
        return jsonify({'error': 'Failed to generate architecture analysis'}), 500


@executive_bp.route('/cto/conversation/clear', methods=['POST'])
@login_required
def clear_cto_conversation():
    """Clear the CTO conversation history"""
    try:
        session.pop('cto_conversation_history', None)
        
        return jsonify({
            'success': True,
            'message': 'CTO conversation history cleared'
        })
        
    except Exception as e:
        logger.error(f"Error clearing CTO conversation: {e}")
        return jsonify({'error': 'Failed to clear conversation'}), 500


@executive_bp.route('/cfo/decision', methods=['POST'])
@login_required
def create_cfo_decision():
    """
    Create a new CFO decision using AI integration
    
    Expected JSON payload:
    {
        "context": "Financial context or problem statement",
        "title": "Decision title",
        "category": "budget|investment|cost_management|financial_planning|risk_management",
        "priority": "low|medium|high|critical",
        "options": ["Option 1", "Option 2"],  // optional
        "document_ids": [1, 2, 3],  // optional document references
        "financial_data": {  // optional financial specifications
            "budget_amount": 100000,
            "expected_roi": 0.15,
            "time_horizon": "12 months",
            "risk_tolerance": "medium"
        }
    }
    """
    try:
        data = request.get_json()
        if not data:
            return jsonify({'error': 'No JSON data provided'}), 400
        
        # Validate required fields
        context = data.get('context', '').strip()
        title = data.get('title', '').strip()
        
        if not context:
            return jsonify({'error': 'Context is required'}), 400
        
        if not title:
            return jsonify({'error': 'Title is required'}), 400
        
        # Extract optional fields
        category = data.get('category', 'financial_planning')
        priority_str = data.get('priority', 'medium')
        options = data.get('options', [])
        document_ids = data.get('document_ids', [])
        financial_data = data.get('financial_data', {})
        
        # Convert priority string to enum
        priority_map = {
            'low': DecisionPriority.LOW,
            'medium': DecisionPriority.MEDIUM,
            'high': DecisionPriority.HIGH,
            'critical': DecisionPriority.CRITICAL
        }
        priority = priority_map.get(priority_str, DecisionPriority.MEDIUM)
        
        # Get document context if document IDs provided
        document_context = ""
        referenced_documents = []
        
        if document_ids and vector_service:
            try:
                for doc_id in document_ids:
                    document = Document.query.get(doc_id)
                    if document and document.user_id == current_user.id:
                        referenced_documents.append(document)
                        
                        # Get relevant context from document
                        if document.summary:
                            document_context += f"\n\nDocument: {document.filename}\nSummary: {document.summary}"
                        
                        # Get semantic search results for the context
                        search_results = vector_service.search_similar_content(
                            query=context,
                            collection_name=f"user_{current_user.id}_documents",
                            limit=3
                        )
                        
                        for result in search_results:
                            if result.get('document_id') == str(doc_id):
                                document_context += f"\nRelevant content: {result.get('content', '')[:500]}..."
                                break
                                
            except Exception as e:
                logger.warning(f"Failed to get document context: {e}")
        
        # Add financial data to context
        if financial_data:
            financial_context = "\n\nFinancial Data:\n"
            for key, value in financial_data.items():
                financial_context += f"- {key.replace('_', ' ').title()}: {value}\n"
            document_context += financial_context
        
        # Get conversation history from session
        conversation_history = session.get('cfo_conversation_history', [])
        
        # Generate AI response using the AI integration service
        if ai_service:
            try:
                executive_response = ai_service.generate_executive_response(
                    executive_type='cfo',
                    context=context,
                    conversation_history=conversation_history,
                    document_context=document_context,
                    options=options
                )
                
                # Extract decision components from AI response
                decision_text = executive_response.decision
                rationale = executive_response.rationale
                confidence_score = executive_response.confidence_score
                financial_impact = executive_response.financial_impact
                risk_level_str = executive_response.risk_level
                
                # Convert risk level string to enum
                risk_map = {
                    'low': RiskLevel.LOW,
                    'medium': RiskLevel.MEDIUM,
                    'high': RiskLevel.HIGH,
                    'critical': RiskLevel.CRITICAL
                }
                risk_level = risk_map.get(risk_level_str, RiskLevel.MEDIUM)
                
            except Exception as e:
                logger.error(f"AI service failed, using fallback: {e}")
                # Fallback to basic response
                decision_text = f"Proceed with detailed financial analysis and risk assessment before implementation."
                rationale = f"Based on financial evaluation of the requirements: {context[:200]}..."
                confidence_score = 0.7
                financial_impact = financial_data.get('budget_amount') if financial_data else None
                risk_level = RiskLevel.MEDIUM
        else:
            # Fallback when AI service is not available
            decision_text = f"Proceed with detailed financial analysis and risk assessment before implementation."
            rationale = f"Based on financial evaluation of the requirements: {context[:200]}..."
            confidence_score = 0.7
            financial_impact = financial_data.get('budget_amount') if financial_data else None
            risk_level = RiskLevel.MEDIUM
        
        # Create decision record
        decision = Decision(
            user_id=current_user.id,
            title=title,
            context=context,
            decision=decision_text,
            rationale=rationale,
            executive_type=ExecutiveType.CFO,
            category=category,
            priority=priority,
            confidence_score=confidence_score,
            financial_impact=financial_impact,
            risk_level=risk_level,
            ai_model_version=ai_service.client.model if ai_service else 'fallback',
            prompt_version='1.0'
        )
        
        # Add document references
        for doc in referenced_documents:
            decision.add_document(doc)
        
        # Update conversation history
        conversation_history.append({
            'role': 'user',
            'content': context,
            'timestamp': datetime.utcnow().isoformat()
        })
        conversation_history.append({
            'role': 'assistant',
            'content': decision_text,
            'timestamp': datetime.utcnow().isoformat()
        })
        
        # Keep only last 10 exchanges to manage memory
        if len(conversation_history) > 20:
            conversation_history = conversation_history[-20:]
        
        session['cfo_conversation_history'] = conversation_history
        decision.set_conversation_history(conversation_history)
        
        # Save to database
        db.session.add(decision)
        db.session.commit()
        
        logger.info(f"CFO decision created: {decision.id} for user {current_user.id}")
        
        return jsonify({
            'success': True,
            'decision': decision.to_dict(),
            'message': 'CFO decision created successfully'
        }), 201
        
    except Exception as e:
        logger.error(f"Error creating CFO decision: {e}")
        db.session.rollback()
        return jsonify({'error': 'Failed to create decision'}), 500


@executive_bp.route('/cfo/decisions', methods=['GET'])
@login_required
def get_cfo_decisions():
    """Get all CFO decisions for the current user"""
    try:
        # Get query parameters
        status = request.args.get('status')
        category = request.args.get('category')
        limit = int(request.args.get('limit', 50))
        offset = int(request.args.get('offset', 0))
        
        # Build query
        query = Decision.query.filter_by(
            user_id=current_user.id,
            executive_type=ExecutiveType.CFO
        )
        
        if status:
            try:
                status_enum = DecisionStatus(status)
                query = query.filter_by(status=status_enum)
            except ValueError:
                return jsonify({'error': f'Invalid status: {status}'}), 400
        
        if category:
            query = query.filter_by(category=category)
        
        # Order by creation date (newest first)
        query = query.order_by(Decision.created_at.desc())
        
        # Apply pagination
        decisions = query.offset(offset).limit(limit).all()
        total_count = query.count()
        
        return jsonify({
            'success': True,
            'decisions': [decision.to_dict() for decision in decisions],
            'total_count': total_count,
            'limit': limit,
            'offset': offset
        })
        
    except Exception as e:
        logger.error(f"Error getting CFO decisions: {e}")
        return jsonify({'error': 'Failed to retrieve decisions'}), 500


@executive_bp.route('/cfo/decision/<int:decision_id>', methods=['GET'])
@login_required
def get_cfo_decision(decision_id):
    """Get a specific CFO decision"""
    try:
        decision = Decision.query.filter_by(
            id=decision_id,
            user_id=current_user.id,
            executive_type=ExecutiveType.CFO
        ).first()
        
        if not decision:
            return jsonify({'error': 'Decision not found'}), 404
        
        return jsonify({
            'success': True,
            'decision': decision.to_dict()
        })
        
    except Exception as e:
        logger.error(f"Error getting CFO decision {decision_id}: {e}")
        return jsonify({'error': 'Failed to retrieve decision'}), 500


@executive_bp.route('/cfo/financial-analysis', methods=['POST'])
@login_required
def get_financial_analysis():
    """
    Get comprehensive financial analysis
    
    Expected JSON payload:
    {
        "context": "Financial analysis context",
        "financial_data": {
            "revenue": 1000000,
            "costs": 800000,
            "investment_amount": 200000,
            "time_horizon": "24 months"
        },
        "analysis_type": "roi|npv|payback|risk_assessment"
    }
    """
    try:
        data = request.get_json()
        if not data:
            return jsonify({'error': 'No JSON data provided'}), 400
        
        context = data.get('context', '').strip()
        financial_data = data.get('financial_data', {})
        analysis_type = data.get('analysis_type', 'roi')
        
        if not context:
            return jsonify({'error': 'Context is required'}), 400
        
        # Build comprehensive analysis context
        analysis_context = f"Financial Analysis ({analysis_type.upper()}): {context}"
        
        if financial_data:
            analysis_context += f"\n\nFinancial Data:\n"
            for key, value in financial_data.items():
                analysis_context += f"- {key.replace('_', ' ').title()}: {value}\n"
        
        # Get conversation history
        conversation_history = session.get('cfo_conversation_history', [])
        
        # Generate AI response
        if ai_service:
            try:
                executive_response = ai_service.generate_executive_response(
                    executive_type='cfo',
                    context=analysis_context,
                    conversation_history=conversation_history
                )
                
                analysis = {
                    "analysis": executive_response.decision,
                    "rationale": executive_response.rationale,
                    "confidence_score": executive_response.confidence_score,
                    "risk_level": executive_response.risk_level,
                    "financial_impact": executive_response.financial_impact,
                    "recommendations": executive_response.decision.split('\n')[:5],  # First 5 lines as recommendations
                    "ai_powered": True
                }
                
            except Exception as e:
                logger.error(f"AI financial analysis failed: {e}")
                analysis = {
                    "analysis": f"Financial {analysis_type.upper()} analysis requires evaluation of cash flows, risk factors, and market conditions.",
                    "rationale": "Based on standard financial analysis frameworks and industry benchmarks.",
                    "confidence_score": 0.6,
                    "risk_level": "medium",
                    "financial_impact": financial_data.get('investment_amount'),
                    "recommendations": [
                        "Conduct detailed cash flow analysis",
                        "Evaluate market conditions and risks",
                        "Consider alternative scenarios",
                        "Review industry benchmarks",
                        "Plan for contingencies"
                    ],
                    "ai_powered": False
                }
        else:
            analysis = {
                "analysis": f"Financial {analysis_type.upper()} analysis requires evaluation of cash flows, risk factors, and market conditions.",
                "rationale": "Based on standard financial analysis frameworks and industry benchmarks.",
                "confidence_score": 0.6,
                "risk_level": "medium",
                "financial_impact": financial_data.get('investment_amount'),
                "recommendations": [
                    "Conduct detailed cash flow analysis",
                    "Evaluate market conditions and risks",
                    "Consider alternative scenarios",
                    "Review industry benchmarks",
                    "Plan for contingencies"
                ],
                "ai_powered": False
            }
        
        return jsonify({
            'success': True,
            'analysis': analysis
        })
        
    except Exception as e:
        logger.error(f"Error in financial analysis: {e}")
        return jsonify({'error': 'Failed to generate financial analysis'}), 500


@executive_bp.route('/cfo/conversation/clear', methods=['POST'])
@login_required
def clear_cfo_conversation():
    """Clear the CFO conversation history"""
    try:
        session.pop('cfo_conversation_history', None)
        
        return jsonify({
            'success': True,
            'message': 'CFO conversation history cleared'
        })
        
    except Exception as e:
        logger.error(f"Error clearing CFO conversation: {e}")
        return jsonify({'error': 'Failed to clear conversation'}), 500


@executive_bp.route('/health', methods=['GET'])
def health_check():
    """Health check endpoint for executive services"""
    try:
        status = {
            'ai_service': 'available' if ai_service else 'unavailable',
            'document_service': 'available' if doc_service else 'unavailable',
            'vector_service': 'available' if vector_service else 'unavailable',
            'database': 'available'
        }
        
        # Test database connection
        try:
            db.session.execute('SELECT 1')
            status['database'] = 'available'
        except Exception:
            status['database'] = 'unavailable'
        
        overall_status = 'healthy' if all(s != 'unavailable' for s in status.values()) else 'degraded'
        
        return jsonify({
            'status': overall_status,
            'services': status,
            'timestamp': datetime.utcnow().isoformat()
        })
        
    except Exception as e:
        logger.error(f"Health check failed: {e}")
        return jsonify({
            'status': 'unhealthy',
            'error': str(e),
            'timestamp': datetime.utcnow().isoformat()
        }), 500