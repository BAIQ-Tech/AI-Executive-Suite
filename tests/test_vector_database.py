"""
Unit tests for Vector Database Service
"""

import pytest
from unittest.mock import Mock, patch, MagicMock
import numpy as np
from datetime import datetime

from services.vector_database import (
    VectorDatabaseService,
    VectorSearchResult,
    EmbeddingModel,
    VectorDatabaseError,
    DocumentEmbedding
)
from tests.factories import DocumentFactory


class TestVectorDatabaseService:
    """Test VectorDatabaseService functionality"""
    
    @pytest.fixture
    def mock_config(self):
        return {
            'vector_database': {
                'provider': 'chromadb',
                'collection_name': 'test_documents',
                'embedding_model': 'text-embedding-ada-002',
                'similarity_threshold': 0.7,
                'max_results': 10
            },
            'openai': {
                'api_key': 'test-key'
            }
        }
    
    @pytest.fixture
    def mock_chroma_client(self):
        client = Mock()
        collection = Mock()
        
        # Mock collection methods
        collection.add.return_value = None
        collection.query.return_value = {
            'ids': [['doc1', 'doc2']],
            'distances': [[0.2, 0.4]],
            'documents': [['Document 1 content', 'Document 2 content']],
            'metadatas': [[{'id': 'doc1', 'type': 'financial'}, {'id': 'doc2', 'type': 'technical'}]]
        }
        collection.delete.return_value = None
        collection.update.return_value = None
        collection.count.return_value = 100
        
        client.get_or_create_collection.return_value = collection
        client.delete_collection.return_value = None
        
        return client, collection
    
    @pytest.fixture
    def mock_openai_client(self):
        client = Mock()
        
        # Mock embedding response
        mock_response = Mock()
        mock_response.data = [Mock()]
        mock_response.data[0].embedding = [0.1, 0.2, 0.3] * 512  # 1536 dimensions
        mock_response.usage.total_tokens = 100
        
        client.embeddings.create.return_value = mock_response
        
        return client
    
    @pytest.fixture
    def service(self, mock_config, mock_chroma_client, mock_openai_client):
        chroma_client, chroma_collection = mock_chroma_client
        
        with patch('services.vector_database.chromadb.Client', return_value=chroma_client), \
             patch('services.vector_database.OpenAI', return_value=mock_openai_client):
            
            service = VectorDatabaseService(mock_config)
            service.collection = chroma_collection
            return service
    
    def test_service_initialization(self, service, mock_config):
        assert service.config == mock_config
        assert service.collection_name == 'test_documents'
        assert service.embedding_model == EmbeddingModel.ADA_002
        assert service.similarity_threshold == 0.7
        assert service.max_results == 10
    
    def test_service_initialization_invalid_provider(self, mock_config):
        mock_config['vector_database']['provider'] = 'invalid_provider'
        
        with pytest.raises(VectorDatabaseError, match="Unsupported vector database provider"):
            VectorDatabaseService(mock_config)
    
    def test_generate_embedding_success(self, service):
        text = "This is a test document for embedding generation."
        
        embedding = service.generate_embedding(text)
        
        assert isinstance(embedding, list)
        assert len(embedding) == 1536  # OpenAI ada-002 dimension
        assert all(isinstance(x, float) for x in embedding)
    
    def test_generate_embedding_empty_text(self, service):
        with pytest.raises(VectorDatabaseError, match="Text cannot be empty"):
            service.generate_embedding("")
    
    def test_generate_embedding_openai_error(self, service):
        service.openai_client.embeddings.create.side_effect = Exception("OpenAI API error")
        
        with pytest.raises(VectorDatabaseError, match="Failed to generate embedding"):
            service.generate_embedding("test text")
    
    def test_add_document_success(self, service):
        document = DocumentFactory.build(
            id='doc123',
            extracted_text='This is test document content',
            document_type='financial',
            filename='test.pdf'
        )
        
        result = service.add_document(document)
        
        assert result is True
        service.collection.add.assert_called_once()
        
        # Verify the call arguments
        call_args = service.collection.add.call_args
        assert call_args[1]['ids'] == ['doc123']
        assert call_args[1]['documents'] == ['This is test document content']
        assert 'embeddings' in call_args[1]
        assert 'metadatas' in call_args[1]
    
    def test_add_document_no_text(self, service):
        document = DocumentFactory.build(extracted_text='')
        
        with pytest.raises(VectorDatabaseError, match="Document has no extractable text"):
            service.add_document(document)
    
    def test_add_document_chroma_error(self, service):
        document = DocumentFactory.build(extracted_text='Test content')
        service.collection.add.side_effect = Exception("ChromaDB error")
        
        with pytest.raises(VectorDatabaseError, match="Failed to add document"):
            service.add_document(document)
    
    def test_search_documents_success(self, service):
        query = "financial analysis report"
        
        results = service.search_documents(query)
        
        assert isinstance(results, list)
        assert len(results) == 2
        
        for result in results:
            assert isinstance(result, VectorSearchResult)
            assert hasattr(result, 'document_id')
            assert hasattr(result, 'content')
            assert hasattr(result, 'similarity_score')
            assert hasattr(result, 'metadata')
        
        # Check specific results
        assert results[0].document_id == 'doc1'
        assert results[0].content == 'Document 1 content'
        assert results[0].similarity_score == 0.8  # 1 - 0.2 distance
        assert results[0].metadata == {'id': 'doc1', 'type': 'financial'}
    
    def test_search_documents_empty_query(self, service):
        with pytest.raises(VectorDatabaseError, match="Query cannot be empty"):
            service.search_documents("")
    
    def test_search_documents_no_results(self, service):
        service.collection.query.return_value = {
            'ids': [[]],
            'distances': [[]],
            'documents': [[]],
            'metadatas': [[]]
        }
        
        results = service.search_documents("no matching query")
        
        assert results == []
    
    def test_search_documents_with_filters(self, service):
        query = "technical documentation"
        filters = {'document_type': 'technical'}
        
        results = service.search_documents(query, filters=filters, max_results=5)
        
        assert isinstance(results, list)
        
        # Verify filter was applied in the query
        service.collection.query.assert_called_once()
        call_args = service.collection.query.call_args[1]
        assert call_args['n_results'] == 5
        assert call_args['where'] == filters
    
    def test_search_documents_chroma_error(self, service):
        service.collection.query.side_effect = Exception("ChromaDB query error")
        
        with pytest.raises(VectorDatabaseError, match="Failed to search documents"):
            service.search_documents("test query")
    
    def test_update_document_success(self, service):
        document = DocumentFactory.build(
            id='doc123',
            extracted_text='Updated document content'
        )
        
        result = service.update_document(document)
        
        assert result is True
        service.collection.update.assert_called_once()
        
        # Verify the call arguments
        call_args = service.collection.update.call_args[1]
        assert call_args['ids'] == ['doc123']
        assert call_args['documents'] == ['Updated document content']
    
    def test_update_document_not_found(self, service):
        service.collection.update.side_effect = Exception("Document not found")
        document = DocumentFactory.build(id='nonexistent')
        
        with pytest.raises(VectorDatabaseError, match="Failed to update document"):
            service.update_document(document)
    
    def test_delete_document_success(self, service):
        result = service.delete_document('doc123')
        
        assert result is True
        service.collection.delete.assert_called_once_with(ids=['doc123'])
    
    def test_delete_document_not_found(self, service):
        service.collection.delete.side_effect = Exception("Document not found")
        
        with pytest.raises(VectorDatabaseError, match="Failed to delete document"):
            service.delete_document('nonexistent')
    
    def test_get_document_count(self, service):
        count = service.get_document_count()
        
        assert count == 100
        service.collection.count.assert_called_once()
    
    def test_get_document_count_error(self, service):
        service.collection.count.side_effect = Exception("Count error")
        
        count = service.get_document_count()
        
        assert count == 0  # Should return 0 on error
    
    def test_batch_add_documents_success(self, service):
        documents = [
            DocumentFactory.build(id=f'doc{i}', extracted_text=f'Content {i}')
            for i in range(3)
        ]
        
        results = service.batch_add_documents(documents)
        
        assert results == [True, True, True]
        assert service.collection.add.call_count == 3
    
    def test_batch_add_documents_partial_failure(self, service):
        documents = [
            DocumentFactory.build(id='doc1', extracted_text='Content 1'),
            DocumentFactory.build(id='doc2', extracted_text=''),  # Should fail
            DocumentFactory.build(id='doc3', extracted_text='Content 3')
        ]
        
        results = service.batch_add_documents(documents, skip_errors=True)
        
        assert len(results) == 3
        assert results[0] is True
        assert results[1] is False
        assert results[2] is True
    
    def test_batch_add_documents_stop_on_error(self, service):
        documents = [
            DocumentFactory.build(id='doc1', extracted_text='Content 1'),
            DocumentFactory.build(id='doc2', extracted_text=''),  # Should fail
            DocumentFactory.build(id='doc3', extracted_text='Content 3')
        ]
        
        with pytest.raises(VectorDatabaseError):
            service.batch_add_documents(documents, skip_errors=False)
    
    def test_find_similar_documents_success(self, service):
        document_id = 'doc123'
        
        # Mock the document retrieval
        service.collection.get = Mock(return_value={
            'ids': ['doc123'],
            'embeddings': [[0.1, 0.2, 0.3] * 512],
            'documents': ['Original document content'],
            'metadatas': [{'type': 'financial'}]
        })
        
        similar_docs = service.find_similar_documents(document_id)
        
        assert isinstance(similar_docs, list)
        assert len(similar_docs) == 2  # Based on mock query response
    
    def test_find_similar_documents_not_found(self, service):
        service.collection.get = Mock(return_value={
            'ids': [],
            'embeddings': [],
            'documents': [],
            'metadatas': []
        })
        
        with pytest.raises(VectorDatabaseError, match="Document not found"):
            service.find_similar_documents('nonexistent')
    
    def test_get_collection_stats(self, service):
        stats = service.get_collection_stats()
        
        assert isinstance(stats, dict)
        assert 'total_documents' in stats
        assert 'collection_name' in stats
        assert 'embedding_model' in stats
        
        assert stats['total_documents'] == 100
        assert stats['collection_name'] == 'test_documents'
        assert stats['embedding_model'] == 'text-embedding-ada-002'
    
    def test_clear_collection_success(self, service):
        # Mock collection recreation
        service.client.delete_collection = Mock()
        service.client.get_or_create_collection = Mock(return_value=service.collection)
        
        result = service.clear_collection()
        
        assert result is True
        service.client.delete_collection.assert_called_once_with('test_documents')
        service.client.get_or_create_collection.assert_called()
    
    def test_clear_collection_error(self, service):
        service.client.delete_collection.side_effect = Exception("Delete error")
        
        with pytest.raises(VectorDatabaseError, match="Failed to clear collection"):
            service.clear_collection()
    
    def test_semantic_search_with_context(self, service):
        query = "revenue analysis"
        context_docs = ['doc1', 'doc2']
        
        results = service.semantic_search_with_context(query, context_docs)
        
        assert isinstance(results, list)
        # Should call search with additional context filtering
        service.collection.query.assert_called_once()
    
    def test_get_document_embedding_success(self, service):
        document_id = 'doc123'
        
        service.collection.get = Mock(return_value={
            'ids': ['doc123'],
            'embeddings': [[0.1, 0.2, 0.3] * 512]
        })
        
        embedding = service.get_document_embedding(document_id)
        
        assert isinstance(embedding, list)
        assert len(embedding) == 1536
    
    def test_get_document_embedding_not_found(self, service):
        service.collection.get = Mock(return_value={
            'ids': [],
            'embeddings': []
        })
        
        embedding = service.get_document_embedding('nonexistent')
        
        assert embedding is None


class TestVectorSearchResult:
    """Test VectorSearchResult data class"""
    
    def test_vector_search_result_creation(self):
        result = VectorSearchResult(
            document_id='doc123',
            content='Test document content',
            similarity_score=0.85,
            metadata={'type': 'financial', 'date': '2023-01-01'}
        )
        
        assert result.document_id == 'doc123'
        assert result.content == 'Test document content'
        assert result.similarity_score == 0.85
        assert result.metadata == {'type': 'financial', 'date': '2023-01-01'}
    
    def test_vector_search_result_comparison(self):
        result1 = VectorSearchResult('doc1', 'content1', 0.9, {})
        result2 = VectorSearchResult('doc2', 'content2', 0.7, {})
        
        # Should compare by similarity score (descending)
        assert result1 > result2
        assert result2 < result1
    
    def test_vector_search_result_to_dict(self):
        result = VectorSearchResult(
            document_id='doc123',
            content='Test content',
            similarity_score=0.8,
            metadata={'test': 'value'}
        )
        
        result_dict = result.to_dict()
        
        assert isinstance(result_dict, dict)
        assert result_dict['document_id'] == 'doc123'
        assert result_dict['content'] == 'Test content'
        assert result_dict['similarity_score'] == 0.8
        assert result_dict['metadata'] == {'test': 'value'}


class TestDocumentEmbedding:
    """Test DocumentEmbedding data class"""
    
    def test_document_embedding_creation(self):
        embedding = DocumentEmbedding(
            document_id='doc123',
            embedding=[0.1, 0.2, 0.3],
            model='text-embedding-ada-002',
            created_at=datetime.utcnow()
        )
        
        assert embedding.document_id == 'doc123'
        assert embedding.embedding == [0.1, 0.2, 0.3]
        assert embedding.model == 'text-embedding-ada-002'
        assert isinstance(embedding.created_at, datetime)
    
    def test_document_embedding_similarity(self):
        embedding1 = DocumentEmbedding('doc1', [1.0, 0.0, 0.0], 'model', datetime.utcnow())
        embedding2 = DocumentEmbedding('doc2', [0.0, 1.0, 0.0], 'model', datetime.utcnow())
        embedding3 = DocumentEmbedding('doc3', [1.0, 0.0, 0.0], 'model', datetime.utcnow())
        
        # Test cosine similarity
        similarity_12 = embedding1.cosine_similarity(embedding2)
        similarity_13 = embedding1.cosine_similarity(embedding3)
        
        assert similarity_12 == 0.0  # Orthogonal vectors
        assert similarity_13 == 1.0  # Identical vectors
    
    def test_document_embedding_euclidean_distance(self):
        embedding1 = DocumentEmbedding('doc1', [0.0, 0.0], 'model', datetime.utcnow())
        embedding2 = DocumentEmbedding('doc2', [3.0, 4.0], 'model', datetime.utcnow())
        
        distance = embedding1.euclidean_distance(embedding2)
        
        assert distance == 5.0  # 3-4-5 triangle


class TestEmbeddingModel:
    """Test EmbeddingModel enum"""
    
    def test_embedding_model_values(self):
        assert EmbeddingModel.ADA_002.value == 'text-embedding-ada-002'
        assert EmbeddingModel.ADA_003_SMALL.value == 'text-embedding-3-small'
        assert EmbeddingModel.ADA_003_LARGE.value == 'text-embedding-3-large'
    
    def test_embedding_model_dimensions(self):
        assert EmbeddingModel.ADA_002.dimensions == 1536
        assert EmbeddingModel.ADA_003_SMALL.dimensions == 1536
        assert EmbeddingModel.ADA_003_LARGE.dimensions == 3072
    
    def test_embedding_model_from_string(self):
        assert EmbeddingModel.from_string('text-embedding-ada-002') == EmbeddingModel.ADA_002
        assert EmbeddingModel.from_string('text-embedding-3-small') == EmbeddingModel.ADA_003_SMALL
        
        with pytest.raises(ValueError, match="Unknown embedding model"):
            EmbeddingModel.from_string('unknown-model')


if __name__ == "__main__":
    pytest.main([__file__])