# Document Processing System

A comprehensive document processing system for the AI Executive Suite that provides secure file upload, advanced text analysis, vector-based semantic search, and intelligent document categorization.

## Features

### 🔒 Secure File Upload & Processing
- **Multi-format Support**: PDF, Word (DOCX/DOC), Excel (XLSX/XLS), Text (TXT), CSV
- **Security Scanning**: Malware detection, content validation, executable file blocking
- **File Validation**: Size limits, type verification, filename sanitization
- **Storage Management**: Organized file storage with deduplication

### 🧠 Advanced Document Analysis
- **Intelligent Summarization**: Multi-level summaries (executive, detailed, key points)
- **Key Insight Extraction**: Categorized insights with confidence scoring
- **Document Classification**: Automatic categorization (financial, technical, strategic, legal, operational)
- **Sentiment Analysis**: Tone and emotional analysis
- **Entity Extraction**: People, organizations, dates, monetary amounts, technologies
- **Topic Modeling**: Main themes and topic distribution
- **Specialized Analysis**: Financial metrics, technical specs, strategic points

### 🔍 Vector-Based Semantic Search
- **ChromaDB Integration**: Persistent vector storage
- **OpenAI Embeddings**: High-quality text embeddings (when API key provided)
- **Semantic Search**: Find relevant content based on meaning, not just keywords
- **Context Extraction**: Retrieve relevant document sections for specific queries
- **Similarity Scoring**: Relevance ranking for search results

## Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                    Document Processing System               │
├─────────────────────────────────────────────────────────────┤
│  ┌─────────────────┐  ┌─────────────────┐  ┌──────────────┐ │
│  │   File Upload   │  │ Document        │  │ Vector       │ │
│  │   & Security    │  │ Analysis        │  │ Database     │ │
│  │   Scanning      │  │ Service         │  │ Service      │ │
│  └─────────────────┘  └─────────────────┘  └──────────────┘ │
│           │                     │                   │       │
│           ▼                     ▼                   ▼       │
│  ┌─────────────────┐  ┌─────────────────┐  ┌──────────────┐ │
│  │ Text Extraction │  │ AI Analysis     │  │ ChromaDB     │ │
│  │ (PDF, Word,     │  │ (Summarization, │  │ (Embeddings, │ │
│  │  Excel, etc.)   │  │  Classification)│  │  Search)     │ │
│  └─────────────────┘  └─────────────────┘  └──────────────┘ │
└─────────────────────────────────────────────────────────────┘
```

## Services

### DocumentProcessingService
Main orchestrator that handles the complete document processing pipeline.

**Key Methods:**
- `upload_document()`: Process and store uploaded documents
- `extract_context()`: Get relevant content based on queries
- `search_documents()`: Semantic search across all documents
- `get_document_by_id()`: Retrieve specific documents
- `delete_document()`: Remove documents and associated data

### VectorDatabaseService
Manages vector embeddings and semantic search capabilities.

**Key Methods:**
- `create_document_embeddings()`: Generate and store embeddings
- `search_similar_content()`: Find semantically similar content
- `get_document_context()`: Extract relevant context from specific documents
- `delete_document_embeddings()`: Remove embeddings for deleted documents

### DocumentAnalysisService
Provides advanced text analysis and intelligence extraction.

**Key Methods:**
- `analyze_document()`: Comprehensive document analysis
- `generate_summary()`: Multi-level summarization
- `extract_key_insights()`: Intelligent insight extraction
- `categorize_document()`: Automatic document classification
- `analyze_sentiment()`: Sentiment and tone analysis
- `extract_entities()`: Named entity recognition
- `extract_financial_metrics()`: Financial data extraction
- `extract_technical_specs()`: Technical specification extraction
- `extract_strategic_points()`: Strategic insight extraction

## Configuration

### Environment Variables
```bash
# OpenAI API (optional - system works without it using fallback methods)
OPENAI_API_KEY=your_openai_api_key_here

# File Upload Settings
UPLOAD_FOLDER=uploads
MAX_CONTENT_LENGTH=52428800  # 50MB

# Vector Database Settings
CHROMA_PATH=./chroma_db
COLLECTION_NAME=ai_executive_documents

# Analysis Settings
EMBEDDING_MODEL=text-embedding-3-small
ANALYSIS_MODEL=gpt-3.5-turbo
CHUNK_SIZE=1000
CHUNK_OVERLAP=200
```

### Service Configuration
```python
config = {
    'upload_directory': 'uploads',
    'max_file_size': 50 * 1024 * 1024,  # 50MB
    'allowed_extensions': ['pdf', 'docx', 'doc', 'xlsx', 'xls', 'txt', 'csv'],
    'openai_api_key': os.getenv('OPENAI_API_KEY'),
    'chroma_path': './chroma_db',
    'collection_name': 'ai_executive_documents',
    'embedding_model': 'text-embedding-3-small',
    'analysis_model': 'gpt-3.5-turbo',
    'chunk_size': 1000,
    'chunk_overlap': 200
}
```

## API Endpoints

### Upload Document
```http
POST /api/documents/upload
Content-Type: multipart/form-data

Form Data:
- file: Document file
- title: Document title (optional)
- description: Document description (optional)
- document_type: financial|technical|strategic|legal|operational (optional)
- sensitivity_level: public|internal|confidential|restricted (optional)
- tags: Comma-separated tags (optional)
- author: Author name (optional)
- department: Department name (optional)
```

### List Documents
```http
GET /api/documents/
Query Parameters:
- document_type: Filter by document type
- sensitivity_level: Filter by sensitivity level
- tags: Filter by tags (comma-separated)
- limit: Maximum results (default: 50, max: 100)
- offset: Results offset (default: 0)
```

### Get Document
```http
GET /api/documents/{document_id}
```

### Delete Document
```http
DELETE /api/documents/{document_id}
```

### Extract Context
```http
POST /api/documents/{document_id}/context
Content-Type: application/json

{
  "query": "search query or context request",
  "max_results": 5
}
```

### Search Documents
```http
POST /api/documents/search
Content-Type: application/json

{
  "query": "search query",
  "document_types": ["financial", "technical"],
  "sensitivity_levels": ["internal", "confidential"],
  "max_results": 10
}
```

## Usage Examples

### Basic Document Upload
```python
from services.document_processing import DocumentProcessingService, FileUpload, DocumentMetadata

# Initialize service
service = DocumentProcessingService(config)

# Create file upload
with open('report.pdf', 'rb') as f:
    file_upload = FileUpload(
        filename='quarterly_report.pdf',
        content=f.read(),
        content_type='application/pdf',
        size=os.path.getsize('report.pdf')
    )

# Create metadata
metadata = DocumentMetadata(
    title='Q4 Financial Report',
    description='Quarterly financial performance report',
    tags=['financial', 'quarterly', 'report'],
    document_type=DocumentType.FINANCIAL,
    sensitivity_level=SensitivityLevel.CONFIDENTIAL
)

# Process document
document = service.upload_document(file_upload, metadata, user_id='user123')
print(f"Document processed: {document.id}")
```

### Context Extraction
```python
# Extract relevant context from a document
contexts = service.extract_context(
    document_id='doc123',
    query='revenue growth and profitability',
    max_results=3
)

for context in contexts:
    print(f"Relevance: {context.relevance_score:.2f}")
    print(f"Content: {context.content[:200]}...")
```

### Semantic Search
```python
# Search across all documents
results = service.search_documents(
    query='artificial intelligence strategy',
    max_results=5
)

for result in results:
    print(f"Document: {result.document.filename}")
    print(f"Relevance: {result.relevance_score:.2f}")
    print(f"Excerpts: {len(result.matching_excerpts)}")
```

## Dependencies

### Core Dependencies
```
flask>=2.3.0
flask-sqlalchemy>=3.0.0
flask-login>=0.6.0
```

### Document Processing
```
PyPDF2>=3.0.0
python-docx>=0.8.11
openpyxl>=3.1.0
pdfplumber>=0.9.0
python-magic>=0.4.27
```

### AI & Vector Database
```
openai>=1.0.0
chromadb>=0.4.0
```

### Analysis & Utilities
```
pandas>=2.0.0
numpy>=1.24.0
```

## Installation

1. **Install Dependencies**
   ```bash
   pip install -r requirements.txt
   ```

2. **Install System Dependencies** (macOS)
   ```bash
   brew install libmagic
   ```

3. **Set Environment Variables**
   ```bash
   export OPENAI_API_KEY=your_api_key_here
   export UPLOAD_FOLDER=uploads
   ```

4. **Initialize Database**
   ```bash
   python -c "from models import db; db.create_all()"
   ```

## Testing

The system includes comprehensive tests covering all functionality:

```bash
# Run document processing tests
python -m pytest tests/test_document_processing.py -v

# Test with sample documents
python test_complete_system.py
```

## Security Features

### File Security
- **Malware Detection**: Scans for executable signatures and malicious patterns
- **Content Validation**: Validates file types using magic numbers
- **Size Limits**: Configurable file size restrictions
- **Filename Sanitization**: Removes dangerous characters from filenames

### Data Protection
- **Sensitivity Levels**: Four-tier classification system
- **Access Control**: User-based document access
- **Audit Logging**: Complete activity tracking
- **Secure Storage**: Encrypted file storage with hash-based deduplication

### API Security
- **Authentication Required**: All endpoints require user authentication
- **Input Validation**: Comprehensive request validation
- **Rate Limiting**: Configurable request rate limits
- **Error Handling**: Secure error responses without information leakage

## Performance Considerations

### Optimization Features
- **Chunked Processing**: Large documents processed in chunks
- **Async Operations**: Non-blocking document processing
- **Caching**: Redis caching for frequently accessed data
- **Database Indexing**: Optimized database queries
- **Vector Optimization**: Efficient similarity search

### Scalability
- **Horizontal Scaling**: Stateless service design
- **Load Balancing**: Multiple service instances
- **Database Scaling**: Read replicas for analytics
- **Storage Scaling**: Cloud storage integration ready

## Monitoring & Logging

### Logging Levels
- **INFO**: Normal operations and processing status
- **WARNING**: Fallback operations and recoverable errors
- **ERROR**: Processing failures and system errors
- **DEBUG**: Detailed processing information

### Metrics Tracked
- Document processing times
- Vector search performance
- Analysis accuracy metrics
- Storage utilization
- API response times

## Future Enhancements

### Planned Features
- **Advanced OCR**: Enhanced text extraction from images and scanned documents
- **Multi-language Support**: Document processing in multiple languages
- **Real-time Collaboration**: Live document editing and commenting
- **Advanced Analytics**: Machine learning-powered insights
- **Integration APIs**: Connectors for popular business tools

### AI Enhancements
- **Custom Models**: Fine-tuned models for specific industries
- **Advanced NLP**: Named entity recognition and relationship extraction
- **Automated Workflows**: AI-powered document routing and processing
- **Predictive Analytics**: Document trend analysis and forecasting

## Support

For technical support or questions about the document processing system:

1. Check the logs for detailed error information
2. Verify configuration settings and environment variables
3. Ensure all dependencies are properly installed
4. Test with the provided sample documents

The system is designed to be robust and will gracefully degrade functionality when external services (like OpenAI) are unavailable, ensuring continuous operation even without AI enhancements.