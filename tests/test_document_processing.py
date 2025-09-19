"""
Tests for Document Processing Service

Tests file upload, processing, text extraction, and security features.
"""

import pytest
import tempfile
import os
import io
from unittest.mock import Mock, patch, MagicMock
from pathlib import Path

from services.document_processing import (
    DocumentProcessingService,
    FileUpload,
    DocumentMetadata,
    DocumentType,
    SensitivityLevel,
    FileProcessingError,
    SecurityScanError
)


class TestDocumentProcessingService:
    """Test cases for DocumentProcessingService"""
    
    @pytest.fixture
    def service(self):
        """Create a DocumentProcessingService instance for testing"""
        config = {
            'upload_directory': tempfile.mkdtemp(),
            'max_file_size': 10 * 1024 * 1024,  # 10MB
            'allowed_extensions': ['pdf', 'docx', 'txt', 'csv']
        }
        return DocumentProcessingService(config)
    
    @pytest.fixture
    def sample_txt_file(self):
        """Create a sample text file for testing"""
        content = "This is a test document with some sample content.\nIt contains multiple lines.\nAnd some financial keywords like revenue and profit."
        return FileUpload(
            filename="test_document.txt",
            content=content.encode('utf-8'),
            content_type="text/plain",
            size=len(content.encode('utf-8'))
        )
    
    @pytest.fixture
    def sample_csv_file(self):
        """Create a sample CSV file for testing"""
        content = "Name,Age,Department\nJohn Doe,30,Engineering\nJane Smith,25,Marketing\n"
        return FileUpload(
            filename="test_data.csv",
            content=content.encode('utf-8'),
            content_type="text/csv",
            size=len(content.encode('utf-8'))
        )
    
    @pytest.fixture
    def malicious_file(self):
        """Create a file with malicious content for security testing"""
        content = "<script>alert('xss')</script>\nSome normal content here."
        return FileUpload(
            filename="malicious.txt",
            content=content.encode('utf-8'),
            content_type="text/plain",
            size=len(content.encode('utf-8'))
        )
    
    @pytest.fixture
    def metadata(self):
        """Create sample document metadata"""
        return DocumentMetadata(
            title="Test Document",
            description="A test document for unit testing",
            tags=["test", "sample"],
            document_type=DocumentType.TECHNICAL,
            sensitivity_level=SensitivityLevel.INTERNAL,
            author="Test User",
            department="Engineering"
        )
    
    def test_file_validation_success(self, service, sample_txt_file):
        """Test successful file validation"""
        # Should not raise any exception
        service._validate_file(sample_txt_file)
    
    def test_file_validation_size_limit(self, service):
        """Test file size validation"""
        large_content = b"x" * (service.max_file_size + 1)
        large_file = FileUpload(
            filename="large_file.txt",
            content=large_content,
            content_type="text/plain",
            size=len(large_content)
        )
        
        with pytest.raises(ValueError, match="exceeds maximum allowed size"):
            service._validate_file(large_file)
    
    def test_file_validation_empty_file(self, service):
        """Test empty file validation"""
        empty_file = FileUpload(
            filename="empty.txt",
            content=b"",
            content_type="text/plain",
            size=0
        )
        
        with pytest.raises(ValueError, match="File is empty"):
            service._validate_file(empty_file)
    
    def test_file_validation_dangerous_filename(self, service):
        """Test dangerous filename validation"""
        dangerous_file = FileUpload(
            filename="../../../etc/passwd",
            content=b"content",
            content_type="text/plain",
            size=7
        )
        
        with pytest.raises(ValueError, match="dangerous characters"):
            service._validate_file(dangerous_file)
    
    def test_file_validation_unsupported_extension(self, service):
        """Test unsupported file extension validation"""
        unsupported_file = FileUpload(
            filename="test.exe",
            content=b"content",
            content_type="application/octet-stream",
            size=7
        )
        
        with pytest.raises(ValueError, match="not allowed"):
            service._validate_file(unsupported_file)
    
    def test_security_scan_clean_file(self, service, sample_txt_file):
        """Test security scan with clean file"""
        # Should not raise any exception
        service._security_scan(sample_txt_file)
    
    def test_security_scan_malicious_content(self, service, malicious_file):
        """Test security scan with malicious content"""
        with pytest.raises(SecurityScanError, match="malicious content detected"):
            service._security_scan(malicious_file)
    
    def test_security_scan_executable_file(self, service):
        """Test security scan with executable file"""
        # PE executable signature
        executable_content = b'\x4d\x5a' + b'x' * 100
        executable_file = FileUpload(
            filename="malware.exe",
            content=executable_content,
            content_type="application/octet-stream",
            size=len(executable_content)
        )
        
        with pytest.raises(SecurityScanError, match="Executable files are not allowed"):
            service._security_scan(executable_file)
    
    def test_filename_sanitization(self, service):
        """Test filename sanitization"""
        dangerous_filename = '<script>alert("xss")</script>.txt'
        sanitized = service._sanitize_filename(dangerous_filename)
        
        assert '<' not in sanitized
        assert '>' not in sanitized
        assert 'script' in sanitized  # Content should remain, just dangerous chars removed
    
    def test_content_hash_generation(self, service, sample_txt_file):
        """Test content hash generation"""
        hash1 = service._generate_content_hash(sample_txt_file.content)
        hash2 = service._generate_content_hash(sample_txt_file.content)
        
        assert hash1 == hash2  # Same content should produce same hash
        assert len(hash1) == 64  # SHA-256 produces 64-character hex string
        assert all(c in '0123456789abcdef' for c in hash1)  # Should be valid hex
    
    def test_text_extraction_txt(self, service, sample_txt_file):
        """Test text extraction from plain text file"""
        extracted_text = service._extract_text(sample_txt_file, 'txt')
        
        assert "test document" in extracted_text.lower()
        assert "multiple lines" in extracted_text.lower()
        assert "financial keywords" in extracted_text.lower()
    
    def test_text_extraction_csv(self, service, sample_csv_file):
        """Test text extraction from CSV file"""
        extracted_text = service._extract_text(sample_csv_file, 'csv')
        
        assert "Name | Age | Department" in extracted_text
        assert "John Doe | 30 | Engineering" in extracted_text
        assert "Jane Smith | 25 | Marketing" in extracted_text
    
    def test_document_classification(self, service):
        """Test document type classification"""
        financial_text = "This document contains revenue, profit, budget, and financial statements."
        technical_text = "This document describes system architecture, software development, and APIs."
        strategic_text = "This document outlines our business strategy, market analysis, and roadmap."
        
        assert service._classify_document(financial_text) == DocumentType.FINANCIAL
        assert service._classify_document(technical_text) == DocumentType.TECHNICAL
        assert service._classify_document(strategic_text) == DocumentType.STRATEGIC
    
    def test_key_insights_extraction(self, service):
        """Test key insights extraction"""
        text_with_financial = "This document discusses revenue growth and investment opportunities."
        insights = service._extract_key_insights(text_with_financial)
        
        assert any("financial" in insight.lower() for insight in insights)
        assert any("words" in insight for insight in insights)  # Word count insight
    
    def test_summary_generation(self, service):
        """Test document summary generation"""
        short_text = "This is a short document."
        long_text = "This is a very long document. " * 100  # Make it longer than 500 chars
        
        short_summary = service._generate_summary(short_text)
        long_summary = service._generate_summary(long_text)
        
        assert short_summary == short_text  # Short text returned as-is
        assert len(long_summary) < len(long_text)  # Long text should be truncated
        assert long_summary.endswith("...")  # Should end with ellipsis
    
    @patch('services.document_processing.HAS_MAGIC', False)
    def test_mime_detection_fallback(self, service, sample_txt_file):
        """Test MIME type detection fallback when python-magic is not available"""
        detected_type = service._detect_file_type(sample_txt_file)
        assert detected_type == 'txt'  # Should fall back to extension-based detection
    
    def test_file_save(self, service, sample_txt_file):
        """Test file saving functionality"""
        content_hash = service._generate_content_hash(sample_txt_file.content)
        file_path = service._save_file(sample_txt_file, content_hash)
        
        assert os.path.exists(file_path)
        assert content_hash[:2] in file_path  # Should be in subdirectory based on hash
        
        # Verify file content
        with open(file_path, 'rb') as f:
            saved_content = f.read()
        
        assert saved_content == sample_txt_file.get_content_bytes()
        
        # Cleanup
        os.remove(file_path)
    
    def test_upload_document_success(self, service, sample_txt_file, metadata):
        """Test successful document upload and processing"""
        document = service.upload_document(sample_txt_file, metadata, "user123")
        
        assert document.id is not None
        assert document.user_id == "user123"
        assert document.filename == "test_document.txt"
        assert document.file_type == "txt"
        assert document.extracted_text is not None
        assert document.summary is not None
        assert document.key_insights is not None
        assert document.document_type in [DocumentType.TECHNICAL, DocumentType.OTHER]  # Based on content
        assert document.created_at is not None
        assert document.processed_at is not None
    
    def test_upload_document_validation_failure(self, service, metadata):
        """Test document upload with validation failure"""
        invalid_file = FileUpload(
            filename="test.exe",
            content=b"content",
            content_type="application/octet-stream",
            size=7
        )
        
        with pytest.raises(FileProcessingError):
            service.upload_document(invalid_file, metadata, "user123")
    
    def test_upload_document_security_failure(self, service, malicious_file, metadata):
        """Test document upload with security scan failure"""
        with pytest.raises(FileProcessingError):
            service.upload_document(malicious_file, metadata, "user123")
    
    def test_extract_context_placeholder(self, service):
        """Test context extraction (placeholder implementation)"""
        contexts = service.extract_context("doc123", "test query")
        
        assert len(contexts) == 1
        assert contexts[0].document_id == "doc123"
        assert contexts[0].relevance_score == 0.85
    
    def test_search_documents_placeholder(self, service):
        """Test document search (placeholder implementation)"""
        results = service.search_documents("test query")
        
        assert isinstance(results, list)
        assert len(results) == 0  # Placeholder returns empty list
    
    def test_get_document_by_id_placeholder(self, service):
        """Test get document by ID (placeholder implementation)"""
        document = service.get_document_by_id("doc123")
        
        assert document is None  # Placeholder returns None
    
    def test_delete_document_placeholder(self, service):
        """Test document deletion (placeholder implementation)"""
        result = service.delete_document("doc123", "user123")
        
        assert result is True  # Placeholder returns True


class TestFileUpload:
    """Test cases for FileUpload class"""
    
    def test_get_content_bytes_from_bytes(self):
        """Test getting content bytes when content is already bytes"""
        content = b"test content"
        file_upload = FileUpload("test.txt", content, "text/plain", len(content))
        
        assert file_upload.get_content_bytes() == content
    
    def test_get_content_bytes_from_io(self):
        """Test getting content bytes when content is BinaryIO"""
        content = b"test content"
        content_io = io.BytesIO(content)
        file_upload = FileUpload("test.txt", content_io, "text/plain", len(content))
        
        assert file_upload.get_content_bytes() == content
        # Verify stream position is reset
        assert content_io.tell() == 0
    
    def test_get_content_bytes_invalid_type(self):
        """Test getting content bytes with invalid content type"""
        file_upload = FileUpload("test.txt", "invalid", "text/plain", 7)
        
        with pytest.raises(ValueError, match="Invalid content type"):
            file_upload.get_content_bytes()


if __name__ == '__main__':
    pytest.main([__file__])