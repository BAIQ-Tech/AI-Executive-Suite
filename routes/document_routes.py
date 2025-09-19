"""
Document management routes for the AI Executive Suite

Handles file upload, document processing, and document management endpoints.
"""

import logging
from flask import Blueprint, request, jsonify, current_app
from flask_login import login_required, current_user
from werkzeug.utils import secure_filename
from werkzeug.exceptions import RequestEntityTooLarge
import os
from typing import Dict, Any

from services.document_processing import (
    DocumentProcessingService,
    FileUpload,
    DocumentMetadata,
    DocumentType,
    SensitivityLevel,
    FileProcessingError,
    SecurityScanError
)
from models import db, Document as DocumentModel
from utils.logging import get_logger

# Create blueprint
document_bp = Blueprint('documents', __name__, url_prefix='/api/documents')
logger = get_logger(__name__)


def get_document_service() -> DocumentProcessingService:
    """Get configured document processing service"""
    config = {
        'upload_directory': current_app.config.get('UPLOAD_FOLDER', 'uploads'),
        'max_file_size': current_app.config.get('MAX_CONTENT_LENGTH', 50 * 1024 * 1024),
        'allowed_extensions': current_app.config.get('ALLOWED_EXTENSIONS', [
            'pdf', 'docx', 'doc', 'xlsx', 'xls', 'txt', 'csv'
        ])
    }
    return DocumentProcessingService(config)


@document_bp.route('/upload', methods=['POST'])
@login_required
def upload_document():
    """
    Upload and process a document
    
    Expected form data:
    - file: The uploaded file
    - title: Optional document title
    - description: Optional document description
    - tags: Optional comma-separated tags
    - document_type: Optional document type (financial, technical, strategic, legal, operational)
    - sensitivity_level: Optional sensitivity level (public, internal, confidential, restricted)
    - author: Optional author name
    - department: Optional department name
    
    Returns:
        JSON response with document information or error
    """
    try:
        # Check if file is present
        if 'file' not in request.files:
            return jsonify({'error': 'No file provided'}), 400
        
        file = request.files['file']
        if file.filename == '':
            return jsonify({'error': 'No file selected'}), 400
        
        # Read file content
        file_content = file.read()
        file.seek(0)  # Reset file pointer
        
        # Create FileUpload object
        file_upload = FileUpload(
            filename=secure_filename(file.filename),
            content=file_content,
            content_type=file.content_type or 'application/octet-stream',
            size=len(file_content)
        )
        
        # Parse metadata from form
        metadata = _parse_document_metadata(request.form)
        
        # Process document
        service = get_document_service()
        document = service.upload_document(file_upload, metadata, str(current_user.id))
        
        # Save to database
        db_document = _save_document_to_db(document, current_user.id)
        
        logger.info(f"Document uploaded successfully: {db_document.id}")
        
        return jsonify({
            'success': True,
            'message': 'Document uploaded and processed successfully',
            'document': db_document.to_dict()
        }), 201
        
    except FileProcessingError as e:
        logger.error(f"File processing error: {str(e)}")
        return jsonify({'error': f'File processing failed: {str(e)}'}), 400
    
    except SecurityScanError as e:
        logger.error(f"Security scan error: {str(e)}")
        return jsonify({'error': f'Security scan failed: {str(e)}'}), 400
    
    except ValueError as e:
        logger.error(f"Validation error: {str(e)}")
        return jsonify({'error': f'Validation failed: {str(e)}'}), 400
    
    except RequestEntityTooLarge:
        return jsonify({'error': 'File too large'}), 413
    
    except Exception as e:
        logger.error(f"Unexpected error during document upload: {str(e)}")
        return jsonify({'error': 'Internal server error'}), 500


@document_bp.route('/', methods=['GET'])
@login_required
def list_documents():
    """
    List user's documents with optional filtering
    
    Query parameters:
    - document_type: Filter by document type
    - sensitivity_level: Filter by sensitivity level
    - tags: Filter by tags (comma-separated)
    - limit: Maximum number of results (default: 50)
    - offset: Number of results to skip (default: 0)
    
    Returns:
        JSON response with list of documents
    """
    try:
        # Parse query parameters
        document_type = request.args.get('document_type')
        sensitivity_level = request.args.get('sensitivity_level')
        tags = request.args.get('tags')
        limit = min(int(request.args.get('limit', 50)), 100)  # Max 100 results
        offset = int(request.args.get('offset', 0))
        
        # Build query
        query = DocumentModel.query.filter_by(user_id=current_user.id)
        
        if document_type:
            try:
                doc_type_enum = DocumentType(document_type.lower())
                query = query.filter_by(document_type=doc_type_enum)
            except ValueError:
                return jsonify({'error': f'Invalid document type: {document_type}'}), 400
        
        if sensitivity_level:
            try:
                sensitivity_enum = SensitivityLevel(sensitivity_level.lower())
                query = query.filter_by(sensitivity_level=sensitivity_enum)
            except ValueError:
                return jsonify({'error': f'Invalid sensitivity level: {sensitivity_level}'}), 400
        
        if tags:
            tag_list = [tag.strip() for tag in tags.split(',')]
            for tag in tag_list:
                query = query.filter(DocumentModel.tags.contains(tag))
        
        # Execute query with pagination
        documents = query.order_by(DocumentModel.created_at.desc()).offset(offset).limit(limit).all()
        total_count = query.count()
        
        return jsonify({
            'success': True,
            'documents': [doc.to_dict() for doc in documents],
            'total_count': total_count,
            'limit': limit,
            'offset': offset
        })
        
    except Exception as e:
        logger.error(f"Error listing documents: {str(e)}")
        return jsonify({'error': 'Internal server error'}), 500


@document_bp.route('/<int:document_id>', methods=['GET'])
@login_required
def get_document(document_id: int):
    """
    Get a specific document by ID
    
    Args:
        document_id: ID of the document
        
    Returns:
        JSON response with document information
    """
    try:
        document = DocumentModel.query.filter_by(
            id=document_id,
            user_id=current_user.id
        ).first()
        
        if not document:
            return jsonify({'error': 'Document not found'}), 404
        
        # Update last accessed time
        document.increment_reference_count()
        db.session.commit()
        
        return jsonify({
            'success': True,
            'document': document.to_dict()
        })
        
    except Exception as e:
        logger.error(f"Error getting document {document_id}: {str(e)}")
        return jsonify({'error': 'Internal server error'}), 500


@document_bp.route('/<int:document_id>', methods=['DELETE'])
@login_required
def delete_document(document_id: int):
    """
    Delete a document
    
    Args:
        document_id: ID of the document
        
    Returns:
        JSON response confirming deletion
    """
    try:
        document = DocumentModel.query.filter_by(
            id=document_id,
            user_id=current_user.id
        ).first()
        
        if not document:
            return jsonify({'error': 'Document not found'}), 404
        
        # Delete file from storage if it exists
        file_path = document.file_path
        if file_path and os.path.exists(file_path):
            try:
                os.remove(file_path)
                logger.info(f"Deleted file: {file_path}")
            except OSError as e:
                logger.warning(f"Could not delete file {file_path}: {str(e)}")
        
        # Delete from database
        db.session.delete(document)
        db.session.commit()
        
        logger.info(f"Document deleted: {document_id}")
        
        return jsonify({
            'success': True,
            'message': 'Document deleted successfully'
        })
        
    except Exception as e:
        logger.error(f"Error deleting document {document_id}: {str(e)}")
        return jsonify({'error': 'Internal server error'}), 500


@document_bp.route('/<int:document_id>/context', methods=['POST'])
@login_required
def extract_context(document_id: int):
    """
    Extract context from a document based on a query
    
    Args:
        document_id: ID of the document
        
    Expected JSON body:
    - query: The query or context request
    - max_results: Optional maximum number of context pieces (default: 5)
    
    Returns:
        JSON response with extracted context
    """
    try:
        document = DocumentModel.query.filter_by(
            id=document_id,
            user_id=current_user.id
        ).first()
        
        if not document:
            return jsonify({'error': 'Document not found'}), 404
        
        data = request.get_json()
        if not data or 'query' not in data:
            return jsonify({'error': 'Query is required'}), 400
        
        query = data['query']
        max_results = data.get('max_results', 5)
        
        # Extract context using document processing service
        service = get_document_service()
        contexts = service.extract_context(str(document.id), query, max_results)
        
        # Update document access tracking
        document.increment_reference_count()
        db.session.commit()
        
        return jsonify({
            'success': True,
            'contexts': [
                {
                    'document_id': ctx.document_id,
                    'content': ctx.content,
                    'relevance_score': ctx.relevance_score,
                    'page_number': ctx.page_number,
                    'section': ctx.section
                }
                for ctx in contexts
            ]
        })
        
    except Exception as e:
        logger.error(f"Error extracting context from document {document_id}: {str(e)}")
        return jsonify({'error': 'Internal server error'}), 500


@document_bp.route('/search', methods=['POST'])
@login_required
def search_documents():
    """
    Search documents using semantic search
    
    Expected JSON body:
    - query: The search query
    - document_types: Optional list of document types to filter by
    - sensitivity_levels: Optional list of sensitivity levels to filter by
    - max_results: Optional maximum number of results (default: 10)
    
    Returns:
        JSON response with search results
    """
    try:
        data = request.get_json()
        if not data or 'query' not in data:
            return jsonify({'error': 'Query is required'}), 400
        
        query = data['query']
        max_results = data.get('max_results', 10)
        
        # TODO: Implement actual semantic search with vector database
        # For now, return placeholder response
        
        return jsonify({
            'success': True,
            'results': [],
            'message': 'Semantic search not yet implemented'
        })
        
    except Exception as e:
        logger.error(f"Error searching documents: {str(e)}")
        return jsonify({'error': 'Internal server error'}), 500


def _parse_document_metadata(form_data: Dict[str, Any]) -> DocumentMetadata:
    """
    Parse document metadata from form data
    
    Args:
        form_data: Form data from request
        
    Returns:
        DocumentMetadata object
    """
    # Parse document type
    document_type = None
    if 'document_type' in form_data:
        try:
            document_type = DocumentType(form_data['document_type'].lower())
        except ValueError:
            pass  # Will be auto-classified
    
    # Parse sensitivity level
    sensitivity_level = SensitivityLevel.INTERNAL  # Default
    if 'sensitivity_level' in form_data:
        try:
            sensitivity_level = SensitivityLevel(form_data['sensitivity_level'].lower())
        except ValueError:
            pass  # Use default
    
    # Parse tags
    tags = []
    if 'tags' in form_data and form_data['tags']:
        tags = [tag.strip() for tag in form_data['tags'].split(',') if tag.strip()]
    
    return DocumentMetadata(
        title=form_data.get('title'),
        description=form_data.get('description'),
        tags=tags,
        document_type=document_type,
        sensitivity_level=sensitivity_level,
        author=form_data.get('author'),
        department=form_data.get('department')
    )


def _save_document_to_db(document, user_id: int) -> DocumentModel:
    """
    Save processed document to database
    
    Args:
        document: Processed document from service
        user_id: ID of the user
        
    Returns:
        Saved DocumentModel instance
    """
    db_document = DocumentModel(
        user_id=user_id,
        filename=document.filename,
        original_filename=document.metadata.get('original_filename', document.filename),
        file_type=document.file_type,
        file_size=document.file_size,
        file_path=document.metadata.get('file_path', ''),
        content_hash=document.content_hash,
        extracted_text=document.extracted_text,
        summary=document.summary,
        document_type=document.document_type,
        sensitivity_level=document.sensitivity_level,
        processing_status='completed'
    )
    
    # Set key insights
    db_document.set_key_insights(document.key_insights)
    
    # Set tags
    if document.metadata.get('tags'):
        db_document.tags = ','.join(document.metadata['tags'])
    
    db.session.add(db_document)
    db.session.commit()
    
    return db_document