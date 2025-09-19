"""
Vector Database Service

Handles document embeddings, vector storage, and semantic search
using ChromaDB and OpenAI embeddings.
"""

import logging
import os
import uuid
from typing import List, Dict, Optional, Any, Tuple
from dataclasses import dataclass
import json

# Vector database and embeddings
import chromadb
from chromadb.config import Settings
import openai
from openai import OpenAI

logger = logging.getLogger(__name__)


@dataclass
class DocumentChunk:
    """Document chunk for vector storage"""
    chunk_id: str
    document_id: str
    content: str
    metadata: Dict[str, Any]
    chunk_index: int
    start_position: Optional[int] = None
    end_position: Optional[int] = None


@dataclass
class SearchResult:
    """Vector search result"""
    chunk_id: str
    document_id: str
    content: str
    similarity_score: float
    metadata: Dict[str, Any]
    chunk_index: int


@dataclass
class EmbeddingStats:
    """Statistics about embeddings"""
    total_chunks: int
    total_tokens: int
    embedding_model: str
    created_at: str


class VectorDatabaseService:
    """Service for vector database operations and semantic search"""
    
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.logger = logging.getLogger(__name__)
        
        # Configuration
        self.openai_api_key = config.get('openai_api_key') or os.getenv('OPENAI_API_KEY')
        self.embedding_model = config.get('embedding_model', 'text-embedding-3-small')
        self.chunk_size = config.get('chunk_size', 1000)
        self.chunk_overlap = config.get('chunk_overlap', 200)
        self.collection_name = config.get('collection_name', 'ai_executive_documents')
        
        # ChromaDB setup
        self.chroma_path = config.get('chroma_path', './chroma_db')
        os.makedirs(self.chroma_path, exist_ok=True)
        
        # Initialize ChromaDB client
        self.chroma_client = chromadb.PersistentClient(
            path=self.chroma_path,
            settings=Settings(
                anonymized_telemetry=False,
                allow_reset=True
            )
        )
        
        # Get or create collection
        try:
            self.collection = self.chroma_client.get_collection(name=self.collection_name)
            self.logger.info(f"Using existing ChromaDB collection: {self.collection_name}")
        except Exception:
            self.collection = self.chroma_client.create_collection(
                name=self.collection_name,
                metadata={"description": "AI Executive Suite document embeddings"}
            )
            self.logger.info(f"Created new ChromaDB collection: {self.collection_name}")
        
        # Initialize OpenAI client
        if self.openai_api_key:
            self.openai_client = OpenAI(api_key=self.openai_api_key)
            self.logger.info("OpenAI client initialized for embeddings")
        else:
            self.openai_client = None
            self.logger.warning("OpenAI API key not provided - embeddings will not work")
    
    def create_document_embeddings(
        self, 
        document_id: str, 
        content: str, 
        metadata: Dict[str, Any] = None
    ) -> List[str]:
        """
        Create embeddings for a document by chunking and storing in vector database
        
        Args:
            document_id: Unique document identifier
            content: Document text content
            metadata: Additional metadata for the document
            
        Returns:
            List of chunk IDs created
            
        Raises:
            ValueError: If OpenAI client is not configured
            Exception: If embedding creation fails
        """
        if not self.openai_client:
            raise ValueError("OpenAI client not configured - cannot create embeddings")
        
        try:
            self.logger.info(f"Creating embeddings for document: {document_id}")
            
            # Remove existing embeddings for this document
            self.delete_document_embeddings(document_id)
            
            # Split content into chunks
            chunks = self._split_text_into_chunks(content)
            self.logger.info(f"Split document into {len(chunks)} chunks")
            
            # Create embeddings for each chunk
            chunk_ids = []
            embeddings = []
            chunk_contents = []
            chunk_metadatas = []
            
            for i, chunk_content in enumerate(chunks):
                chunk_id = f"{document_id}_chunk_{i}"
                chunk_ids.append(chunk_id)
                
                # Create embedding
                embedding = self._create_embedding(chunk_content)
                embeddings.append(embedding)
                chunk_contents.append(chunk_content)
                
                # Prepare metadata
                chunk_metadata = {
                    'document_id': document_id,
                    'chunk_index': i,
                    'chunk_length': len(chunk_content),
                    'embedding_model': self.embedding_model,
                    **(metadata or {})
                }
                chunk_metadatas.append(chunk_metadata)
            
            # Store in ChromaDB
            self.collection.add(
                ids=chunk_ids,
                embeddings=embeddings,
                documents=chunk_contents,
                metadatas=chunk_metadatas
            )
            
            self.logger.info(f"Successfully created {len(chunk_ids)} embeddings for document {document_id}")
            return chunk_ids
            
        except Exception as e:
            self.logger.error(f"Error creating embeddings for document {document_id}: {str(e)}")
            raise
    
    def search_similar_content(
        self, 
        query: str, 
        n_results: int = 5,
        document_ids: Optional[List[str]] = None,
        metadata_filter: Optional[Dict[str, Any]] = None
    ) -> List[SearchResult]:
        """
        Search for similar content using semantic search
        
        Args:
            query: Search query text
            n_results: Number of results to return
            document_ids: Optional list of document IDs to search within
            metadata_filter: Optional metadata filters
            
        Returns:
            List of search results ordered by similarity
            
        Raises:
            ValueError: If OpenAI client is not configured
        """
        if not self.openai_client:
            raise ValueError("OpenAI client not configured - cannot perform semantic search")
        
        try:
            self.logger.info(f"Searching for similar content: {query[:100]}...")
            
            # Create embedding for query
            query_embedding = self._create_embedding(query)
            
            # Build where clause for filtering
            where_clause = {}
            if document_ids:
                where_clause['document_id'] = {'$in': document_ids}
            
            if metadata_filter:
                where_clause.update(metadata_filter)
            
            # Search in ChromaDB
            results = self.collection.query(
                query_embeddings=[query_embedding],
                n_results=n_results,
                where=where_clause if where_clause else None
            )
            
            # Convert to SearchResult objects
            search_results = []
            if results['ids'] and results['ids'][0]:  # Check if we have results
                for i in range(len(results['ids'][0])):
                    chunk_id = results['ids'][0][i]
                    content = results['documents'][0][i]
                    distance = results['distances'][0][i] if results['distances'] else 0.0
                    metadata = results['metadatas'][0][i] if results['metadatas'] else {}
                    
                    # Convert distance to similarity score (1 - distance for cosine similarity)
                    similarity_score = max(0.0, 1.0 - distance)
                    
                    search_result = SearchResult(
                        chunk_id=chunk_id,
                        document_id=metadata.get('document_id', ''),
                        content=content,
                        similarity_score=similarity_score,
                        metadata=metadata,
                        chunk_index=metadata.get('chunk_index', 0)
                    )
                    search_results.append(search_result)
            
            self.logger.info(f"Found {len(search_results)} similar content pieces")
            return search_results
            
        except Exception as e:
            self.logger.error(f"Error searching for similar content: {str(e)}")
            raise
    
    def get_document_context(
        self, 
        document_id: str, 
        query: str, 
        max_chunks: int = 3
    ) -> List[SearchResult]:
        """
        Get relevant context from a specific document
        
        Args:
            document_id: Document to search within
            query: Context query
            max_chunks: Maximum number of chunks to return
            
        Returns:
            List of relevant document chunks
        """
        return self.search_similar_content(
            query=query,
            n_results=max_chunks,
            document_ids=[document_id]
        )
    
    def delete_document_embeddings(self, document_id: str) -> bool:
        """
        Delete all embeddings for a document
        
        Args:
            document_id: Document identifier
            
        Returns:
            True if successful
        """
        try:
            # Get all chunk IDs for this document
            results = self.collection.get(
                where={'document_id': document_id}
            )
            
            if results['ids']:
                self.collection.delete(ids=results['ids'])
                self.logger.info(f"Deleted {len(results['ids'])} embeddings for document {document_id}")
            
            return True
            
        except Exception as e:
            self.logger.error(f"Error deleting embeddings for document {document_id}: {str(e)}")
            return False
    
    def get_collection_stats(self) -> EmbeddingStats:
        """
        Get statistics about the vector database collection
        
        Returns:
            Collection statistics
        """
        try:
            count = self.collection.count()
            
            # Get sample metadata to determine embedding model
            sample_results = self.collection.get(limit=1)
            embedding_model = self.embedding_model
            if sample_results['metadatas'] and sample_results['metadatas'][0]:
                embedding_model = sample_results['metadatas'][0].get('embedding_model', self.embedding_model)
            
            return EmbeddingStats(
                total_chunks=count,
                total_tokens=0,  # Would need to calculate from chunk lengths
                embedding_model=embedding_model,
                created_at=self.collection.get()['metadatas'][0].get('created_at', '') if count > 0 else ''
            )
            
        except Exception as e:
            self.logger.error(f"Error getting collection stats: {str(e)}")
            return EmbeddingStats(
                total_chunks=0,
                total_tokens=0,
                embedding_model=self.embedding_model,
                created_at=''
            )
    
    def reset_collection(self) -> bool:
        """
        Reset the entire collection (delete all embeddings)
        
        Returns:
            True if successful
        """
        try:
            self.chroma_client.delete_collection(name=self.collection_name)
            self.collection = self.chroma_client.create_collection(
                name=self.collection_name,
                metadata={"description": "AI Executive Suite document embeddings"}
            )
            self.logger.info(f"Reset collection: {self.collection_name}")
            return True
            
        except Exception as e:
            self.logger.error(f"Error resetting collection: {str(e)}")
            return False
    
    def _create_embedding(self, text: str) -> List[float]:
        """
        Create embedding for text using OpenAI
        
        Args:
            text: Text to embed
            
        Returns:
            Embedding vector
        """
        try:
            response = self.openai_client.embeddings.create(
                model=self.embedding_model,
                input=text.replace('\n', ' ')  # Clean text
            )
            return response.data[0].embedding
            
        except Exception as e:
            self.logger.error(f"Error creating embedding: {str(e)}")
            raise
    
    def _split_text_into_chunks(self, text: str) -> List[str]:
        """
        Split text into chunks for embedding
        
        Args:
            text: Text to split
            
        Returns:
            List of text chunks
        """
        if len(text) <= self.chunk_size:
            return [text]
        
        chunks = []
        start = 0
        
        while start < len(text):
            end = start + self.chunk_size
            
            # If this isn't the last chunk, try to break at a sentence or word boundary
            if end < len(text):
                # Look for sentence boundary
                sentence_end = text.rfind('.', start, end)
                if sentence_end > start + self.chunk_size // 2:
                    end = sentence_end + 1
                else:
                    # Look for word boundary
                    word_end = text.rfind(' ', start, end)
                    if word_end > start + self.chunk_size // 2:
                        end = word_end
            
            chunk = text[start:end].strip()
            if chunk:
                chunks.append(chunk)
            
            # Move start position with overlap
            start = max(start + 1, end - self.chunk_overlap)
        
        return chunks
    
    def optimize_collection(self) -> bool:
        """
        Optimize the vector database collection
        
        Returns:
            True if successful
        """
        try:
            # ChromaDB doesn't have explicit optimization, but we can log stats
            stats = self.get_collection_stats()
            self.logger.info(f"Collection optimization check - Total chunks: {stats.total_chunks}")
            return True
            
        except Exception as e:
            self.logger.error(f"Error optimizing collection: {str(e)}")
            return False