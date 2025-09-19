"""
Unit tests for Document Analysis Service
"""

import pytest
from unittest.mock import Mock, patch, MagicMock
from datetime import datetime
import tempfile
import os

from services.document_analysis import (
    DocumentAnalysisService,
    DocumentSummary,
    KeyInsight,
    DocumentCategory,
    AnalysisError
)
from tests.factories import DocumentFactory, UserFactory


class TestDocumentAnalysisService:
    """Test DocumentAnalysisService functionality"""
    
    @pytest.fixture
    def mock_config(self):
        return {
            'document_analysis': {
                'max_summary_length': 500,
                'min_confidence_score': 0.7,
                'supported_formats': ['pdf', 'docx', 'txt', 'xlsx']
            },
            'ai_integration': {
                'model': 'gpt-4',
                'max_tokens': 2000
            }
        }
    
    @pytest.fixture
    def mock_ai_service(self):
        ai_service = Mock()
        ai_service.generate_completion.return_value = Mock(
            content='{"summary": "Test summary", "key_insights": ["Insight 1", "Insight 2"], "category": "financial", "confidence_score": 0.85}'
        )
        return ai_service
    
    @pytest.fixture
    def service(self, mock_config, mock_ai_service):
        return DocumentAnalysisService(mock_config, mock_ai_service)
    
    def test_service_initialization(self, service, mock_config):
        assert service.config == mock_config
        assert service.ai_service is not None
    
    def test_analyze_document_success(self, service):
        document = DocumentFactory.build(
            extracted_text="This is a financial report showing revenue growth of 15%",
            document_type="financial"
        )
        
        result = service.analyze_document(document)
        
        assert isinstance(result, DocumentSummary)
        assert result.summary == "Test summary"
        assert result.key_insights == ["Insight 1", "Insight 2"]
        assert result.category == DocumentCategory.FINANCIAL
        assert result.confidence_score == 0.85
    
    def test_analyze_document_with_empty_text(self, service):
        document = DocumentFactory.build(extracted_text="")
        
        with pytest.raises(AnalysisError, match="No text content"):
            service.analyze_document(document)
    
    def test_analyze_document_ai_error(self, service):
        document = DocumentFactory.build(
            extracted_text="Test content"
        )
        
        service.ai_service.generate_completion.side_effect = Exception("AI service error")
        
        with pytest.raises(AnalysisError, match="AI analysis failed"):
            service.analyze_document(document)
    
    def test_analyze_document_invalid_json_response(self, service):
        document = DocumentFactory.build(
            extracted_text="Test content"
        )
        
        service.ai_service.generate_completion.return_value = Mock(
            content="Invalid JSON response"
        )
        
        with pytest.raises(AnalysisError, match="Invalid AI response format"):
            service.analyze_document(document)
    
    def test_extract_key_insights_success(self, service):
        text = "The company's revenue increased by 15% this quarter. Operating expenses remained stable. Market share grew by 3%."
        
        insights = service.extract_key_insights(text)
        
        assert isinstance(insights, list)
        assert len(insights) > 0
        assert all(isinstance(insight, KeyInsight) for insight in insights)
    
    def test_extract_key_insights_empty_text(self, service):
        insights = service.extract_key_insights("")
        assert insights == []
    
    def test_categorize_document_financial(self, service):
        text = "Revenue increased by 15%. Profit margins improved. Cash flow is positive."
        
        category = service.categorize_document(text)
        
        assert category == DocumentCategory.FINANCIAL
    
    def test_categorize_document_technical(self, service):
        text = "System architecture uses microservices. Database performance optimized. API endpoints secured."
        
        service.ai_service.generate_completion.return_value = Mock(
            content='{"category": "technical", "confidence": 0.9}'
        )
        
        category = service.categorize_document(text)
        
        assert category == DocumentCategory.TECHNICAL
    
    def test_categorize_document_strategic(self, service):
        text = "Market expansion strategy. Competitive analysis. Long-term growth plans."
        
        service.ai_service.generate_completion.return_value = Mock(
            content='{"category": "strategic", "confidence": 0.85}'
        )
        
        category = service.categorize_document(text)
        
        assert category == DocumentCategory.STRATEGIC
    
    def test_categorize_document_legal(self, service):
        text = "Contract terms and conditions. Compliance requirements. Legal obligations."
        
        service.ai_service.generate_completion.return_value = Mock(
            content='{"category": "legal", "confidence": 0.8}'
        )
        
        category = service.categorize_document(text)
        
        assert category == DocumentCategory.LEGAL
    
    def test_categorize_document_unknown(self, service):
        text = "Random text without clear category indicators."
        
        service.ai_service.generate_completion.return_value = Mock(
            content='{"category": "unknown", "confidence": 0.3}'
        )
        
        category = service.categorize_document(text)
        
        assert category == DocumentCategory.OTHER
    
    def test_generate_summary_success(self, service):
        text = "This is a long document with multiple paragraphs containing important information about business operations and financial performance."
        
        summary = service.generate_summary(text, max_length=100)
        
        assert isinstance(summary, str)
        assert len(summary) <= 100
        assert len(summary) > 0
    
    def test_generate_summary_short_text(self, service):
        text = "Short text."
        
        summary = service.generate_summary(text)
        
        # Should return original text if it's already short
        assert summary == text
    
    def test_generate_summary_empty_text(self, service):
        summary = service.generate_summary("")
        assert summary == ""
    
    def test_analyze_sentiment_positive(self, service):
        text = "Excellent performance this quarter. Revenue exceeded expectations. Team morale is high."
        
        service.ai_service.generate_completion.return_value = Mock(
            content='{"sentiment": "positive", "score": 0.8, "confidence": 0.9}'
        )
        
        sentiment = service.analyze_sentiment(text)
        
        assert sentiment['sentiment'] == 'positive'
        assert sentiment['score'] == 0.8
        assert sentiment['confidence'] == 0.9
    
    def test_analyze_sentiment_negative(self, service):
        text = "Poor performance this quarter. Revenue declined significantly. Major challenges ahead."
        
        service.ai_service.generate_completion.return_value = Mock(
            content='{"sentiment": "negative", "score": -0.7, "confidence": 0.85}'
        )
        
        sentiment = service.analyze_sentiment(text)
        
        assert sentiment['sentiment'] == 'negative'
        assert sentiment['score'] == -0.7
    
    def test_analyze_sentiment_neutral(self, service):
        text = "Standard quarterly report. Regular business operations. No significant changes."
        
        service.ai_service.generate_completion.return_value = Mock(
            content='{"sentiment": "neutral", "score": 0.1, "confidence": 0.75}'
        )
        
        sentiment = service.analyze_sentiment(text)
        
        assert sentiment['sentiment'] == 'neutral'
        assert sentiment['score'] == 0.1
    
    def test_extract_entities_success(self, service):
        text = "Apple Inc. reported revenue of $100 billion in Q4 2023. CEO Tim Cook announced new initiatives."
        
        service.ai_service.generate_completion.return_value = Mock(
            content='{"entities": [{"text": "Apple Inc.", "type": "ORGANIZATION"}, {"text": "$100 billion", "type": "MONEY"}, {"text": "Q4 2023", "type": "DATE"}, {"text": "Tim Cook", "type": "PERSON"}]}'
        )
        
        entities = service.extract_entities(text)
        
        assert isinstance(entities, list)
        assert len(entities) == 4
        assert entities[0]['text'] == 'Apple Inc.'
        assert entities[0]['type'] == 'ORGANIZATION'
    
    def test_extract_entities_empty_text(self, service):
        entities = service.extract_entities("")
        assert entities == []
    
    def test_calculate_readability_score(self, service):
        text = "This is a simple sentence. It has basic words. The structure is clear."
        
        score = service.calculate_readability_score(text)
        
        assert isinstance(score, float)
        assert 0 <= score <= 100
    
    def test_calculate_readability_score_empty_text(self, service):
        score = service.calculate_readability_score("")
        assert score == 0.0
    
    def test_detect_language_english(self, service):
        text = "This is an English document with standard business content."
        
        service.ai_service.generate_completion.return_value = Mock(
            content='{"language": "en", "confidence": 0.95}'
        )
        
        language = service.detect_language(text)
        
        assert language['language'] == 'en'
        assert language['confidence'] == 0.95
    
    def test_detect_language_spanish(self, service):
        text = "Este es un documento en español con contenido empresarial."
        
        service.ai_service.generate_completion.return_value = Mock(
            content='{"language": "es", "confidence": 0.92}'
        )
        
        language = service.detect_language(text)
        
        assert language['language'] == 'es'
        assert language['confidence'] == 0.92
    
    def test_analyze_document_quality_high(self, service):
        document = DocumentFactory.build(
            extracted_text="This is a well-structured document with clear headings, proper formatting, and comprehensive content that provides valuable insights into business operations.",
            file_size=50000  # 50KB
        )
        
        quality = service.analyze_document_quality(document)
        
        assert isinstance(quality, dict)
        assert 'overall_score' in quality
        assert 'content_quality' in quality
        assert 'structure_quality' in quality
        assert 'completeness' in quality
        assert 0 <= quality['overall_score'] <= 1
    
    def test_analyze_document_quality_low(self, service):
        document = DocumentFactory.build(
            extracted_text="Short text.",
            file_size=100  # Very small file
        )
        
        quality = service.analyze_document_quality(document)
        
        assert quality['overall_score'] < 0.5  # Should be low quality
    
    def test_batch_analyze_documents(self, service):
        documents = [
            DocumentFactory.build(extracted_text=f"Document {i} content") 
            for i in range(3)
        ]
        
        results = service.batch_analyze_documents(documents)
        
        assert isinstance(results, list)
        assert len(results) == 3
        assert all(isinstance(result, DocumentSummary) for result in results)
    
    def test_batch_analyze_documents_empty_list(self, service):
        results = service.batch_analyze_documents([])
        assert results == []
    
    def test_batch_analyze_documents_with_errors(self, service):
        documents = [
            DocumentFactory.build(extracted_text="Valid content"),
            DocumentFactory.build(extracted_text=""),  # This should cause an error
            DocumentFactory.build(extracted_text="More valid content")
        ]
        
        # Configure service to handle errors gracefully
        service.ai_service.generate_completion.side_effect = [
            Mock(content='{"summary": "Valid summary", "key_insights": ["Insight"], "category": "other", "confidence_score": 0.8}'),
            Exception("Analysis error"),
            Mock(content='{"summary": "Another summary", "key_insights": ["Another insight"], "category": "other", "confidence_score": 0.75}')
        ]
        
        results = service.batch_analyze_documents(documents, skip_errors=True)
        
        # Should return results for successful analyses only
        assert len(results) == 2
    
    def test_get_analysis_statistics(self, service):
        # Mock some analysis history
        service._analysis_history = [
            {'category': 'financial', 'confidence': 0.9, 'processing_time': 1.5},
            {'category': 'technical', 'confidence': 0.8, 'processing_time': 2.0},
            {'category': 'financial', 'confidence': 0.85, 'processing_time': 1.8}
        ]
        
        stats = service.get_analysis_statistics()
        
        assert isinstance(stats, dict)
        assert 'total_analyses' in stats
        assert 'average_confidence' in stats
        assert 'average_processing_time' in stats
        assert 'category_distribution' in stats
        
        assert stats['total_analyses'] == 3
        assert stats['category_distribution']['financial'] == 2
        assert stats['category_distribution']['technical'] == 1


class TestDocumentSummary:
    """Test DocumentSummary data class"""
    
    def test_document_summary_creation(self):
        summary = DocumentSummary(
            summary="Test summary",
            key_insights=["Insight 1", "Insight 2"],
            category=DocumentCategory.FINANCIAL,
            confidence_score=0.85,
            metadata={'test': 'value'}
        )
        
        assert summary.summary == "Test summary"
        assert summary.key_insights == ["Insight 1", "Insight 2"]
        assert summary.category == DocumentCategory.FINANCIAL
        assert summary.confidence_score == 0.85
        assert summary.metadata == {'test': 'value'}
    
    def test_document_summary_to_dict(self):
        summary = DocumentSummary(
            summary="Test summary",
            key_insights=["Insight 1"],
            category=DocumentCategory.TECHNICAL,
            confidence_score=0.9
        )
        
        result = summary.to_dict()
        
        assert isinstance(result, dict)
        assert result['summary'] == "Test summary"
        assert result['key_insights'] == ["Insight 1"]
        assert result['category'] == 'technical'
        assert result['confidence_score'] == 0.9


class TestKeyInsight:
    """Test KeyInsight data class"""
    
    def test_key_insight_creation(self):
        insight = KeyInsight(
            text="Revenue increased by 15%",
            importance=0.9,
            category="financial",
            confidence=0.85
        )
        
        assert insight.text == "Revenue increased by 15%"
        assert insight.importance == 0.9
        assert insight.category == "financial"
        assert insight.confidence == 0.85
    
    def test_key_insight_comparison(self):
        insight1 = KeyInsight("Text 1", 0.9, "cat1", 0.8)
        insight2 = KeyInsight("Text 2", 0.7, "cat2", 0.9)
        
        # Should compare by importance
        assert insight1 > insight2
        assert insight2 < insight1


class TestDocumentCategory:
    """Test DocumentCategory enum"""
    
    def test_document_category_values(self):
        assert DocumentCategory.FINANCIAL.value == 'financial'
        assert DocumentCategory.TECHNICAL.value == 'technical'
        assert DocumentCategory.STRATEGIC.value == 'strategic'
        assert DocumentCategory.LEGAL.value == 'legal'
        assert DocumentCategory.OTHER.value == 'other'
    
    def test_document_category_from_string(self):
        assert DocumentCategory.from_string('financial') == DocumentCategory.FINANCIAL
        assert DocumentCategory.from_string('technical') == DocumentCategory.TECHNICAL
        assert DocumentCategory.from_string('unknown') == DocumentCategory.OTHER


if __name__ == "__main__":
    pytest.main([__file__])