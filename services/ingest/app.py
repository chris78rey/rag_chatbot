# =============================================================================
# RAF Chatbot — Ingest Service: Shared Application Module
# =============================================================================
#
# This module provides shared utilities for the ingest service:
# - Document loaders (PDF, TXT, MD, DOCX)
# - Text splitters (chunking strategies)
# - File operations (move, delete, archive)
# - Error handling and logging
#
# Implementation Note:
# This is a skeleton file with docstrings defining the interface.
# Actual implementation will be completed in Subproject 5+.
#

"""
Ingest Service Application Module

Provides utilities for document loading, chunking, embedding, and file management.
"""


class DocumentLoader:
    """
    Load documents from various file formats.
    
    Supported formats:
    - PDF (.pdf)
    - Plain text (.txt)
    - Markdown (.md)
    - Microsoft Word (.docx)
    
    Responsibilities:
    - Detect file type from extension
    - Load and parse document content
    - Extract text from complex formats
    - Handle encoding issues
    - Validate file integrity
    """
    
    def __init__(self, config):
        """
        Initialize document loader.
        
        Args:
            config: Configuration dict with:
                - sources.allowed_extensions: List of allowed file types
                - sources.max_file_size_mb: Maximum file size in MB
                - chunking: Chunking configuration
        """
        pass
    
    def load(self, file_path):
        """
        Load and parse document from file path.
        
        Args:
            file_path (str): Absolute path to document file
            
        Returns:
            Document: Parsed document with:
                - content (str): Full text content
                - metadata (dict): Extracted metadata
                
        Raises:
            FileNotFoundError: File does not exist
            UnsupportedFileTypeError: File type not supported
            ParseError: Could not parse document
            ValidationError: File fails validation
        """
        pass
    
    def load_pdf(self, file_path):
        """Load PDF document."""
        pass
    
    def load_txt(self, file_path):
        """Load plain text document."""
        pass
    
    def load_md(self, file_path):
        """Load Markdown document."""
        pass
    
    def load_docx(self, file_path):
        """Load Microsoft Word document."""
        pass
    
    def validate_file(self, file_path):
        """
        Validate file before loading.
        
        Checks:
        - File exists and is readable
        - File size within limits
        - File extension supported
        - File is not corrupted
        
        Returns:
            bool: True if valid
            
        Raises:
            ValidationError: If file fails validation
        """
        pass


class TextSplitter:
    """
    Split documents into chunks for embedding.
    
    Strategies:
    - recursive_character: Split by hierarchy of separators
    - semantic: Split by semantic boundaries (future)
    
    Responsibilities:
    - Split text into manageable chunks
    - Maintain context with overlap
    - Preserve metadata (source, position)
    - Handle edge cases (empty chunks, very large chunks)
    """
    
    def __init__(self, config):
        """
        Initialize text splitter.
        
        Args:
            config: Configuration dict with:
                - chunking.splitter: Strategy (recursive_character, semantic)
                - chunking.chunk_size: Characters per chunk
                - chunking.chunk_overlap: Overlap between chunks
                - chunking.separator: Primary separator
                - chunking.secondary_separators: Fallback separators
        """
        pass
    
    def split(self, text, metadata=None):
        """
        Split text into chunks.
        
        Args:
            text (str): Document text to split
            metadata (dict): Original document metadata (preserved in chunks)
            
        Returns:
            List[Chunk]: List of chunks, each with:
                - content (str): Chunk text
                - metadata (dict): Chunk metadata
                - chunk_index (int): Position in document
                - source (str): Original document path (if provided)
        """
        pass
    
    def split_recursive_character(self, text, metadata=None):
        """
        Split recursively by separator hierarchy.
        
        Algorithm:
        1. Try splitting by primary separator
        2. If chunks > size, try secondary separators
        3. Continue until chunks fit size limit
        """
        pass
    
    def split_semantic(self, text, metadata=None):
        """
        Split by semantic boundaries (future implementation).
        
        Uses embeddings to detect semantic breaks.
        Requires embedding model (expensive).
        """
        pass


class EmbeddingGenerator:
    """
    Generate embeddings for text chunks.
    
    Responsibilities:
    - Generate embeddings using configured model
    - Batch process multiple chunks efficiently
    - Handle embedding API failures
    - Cache embeddings (optional)
    
    Note: Implementation deferred to Subproject 6+
    """
    
    def __init__(self, config):
        """
        Initialize embedding generator.
        
        Args:
            config: Configuration dict with:
                - embeddings.model_name: Hugging Face model ID
                - embeddings.dimension: Expected vector dimension
                - embeddings.batch_size: Batch size for processing
                - embeddings.normalize: Whether to L2 normalize
        """
        pass
    
    def generate(self, chunks):
        """
        Generate embeddings for text chunks.
        
        Args:
            chunks: List of Chunk objects with content
            
        Returns:
            List[np.ndarray]: Vector embeddings (dimension x vector_size)
            
        Note:
            Actual implementation in Subproject 6+
        """
        pass
    
    def generate_batch(self, texts, batch_size=None):
        """
        Generate embeddings for multiple texts in batches.
        
        Args:
            texts (List[str]): Texts to embed
            batch_size (int): Batch size (default from config)
            
        Returns:
            List[np.ndarray]: Embeddings
        """
        pass


class FileManager:
    """
    Manage file operations for ingestion workflow.
    
    Operations:
    - Move files between directories (incoming → processed/failed)
    - Create/manage directory structure
    - Archive old files
    - Clean up temporary files
    - Write metadata and error logs
    
    Responsibilities:
    - Atomic file operations (no partial states)
    - Preserve file metadata (timestamps, permissions)
    - Create error logs with details
    - Maintain directory structure
    """
    
    def __init__(self, config):
        """
        Initialize file manager.
        
        Args:
            config: Configuration dict with:
                - paths.sources_root: Root directory for sources
                - sources.directory: Subdirectory for this RAG
        """
        pass
    
    def move_to_processed(self, file_path, rag_id, job_id, metadata=None):
        """
        Move successfully processed file to processed directory.
        
        Actions:
        1. Move file to data/sources/<rag_id>/processed/
        2. Write metadata to .meta.json file
        3. Update file timestamps
        4. Remove from incoming directory
        
        Args:
            file_path (str): Current file path
            rag_id (str): RAG identifier
            job_id (str): Job identifier
            metadata (dict): Processing metadata (chunks, embeddings, etc.)
            
        Returns:
            str: New file path
        """
        pass
    
    def move_to_failed(self, file_path, rag_id, job_id, error_details=None):
        """
        Move failed file to failed directory.
        
        Actions:
        1. Move file to data/sources/<rag_id>/failed/
        2. Write error details to .error.json file
        3. Preserve original file timestamps
        4. Log error for debugging
        
        Args:
            file_path (str): Current file path
            rag_id (str): RAG identifier
            job_id (str): Job identifier
            error_details (dict): Error information
            
        Returns:
            str: New file path
        """
        pass
    
    def write_metadata(self, file_path, metadata):
        """
        Write metadata JSON file.
        
        Creates <file_path>.meta.json with processing details.
        
        Args:
            file_path (str): File path
            metadata (dict): Metadata to save
        """
        pass
    
    def write_error_log(self, file_path, error_details):
        """
        Write error log JSON file.
        
        Creates <file_path>.error.json with error details.
        
        Args:
            file_path (str): File path
            error_details (dict): Error information
        """
        pass
    
    def ensure_directories(self, rag_id):
        """
        Ensure directory structure exists.
        
        Creates:
        - data/sources/<rag_id>/incoming
        - data/sources/<rag_id>/processed
        - data/sources/<rag_id>/failed
        
        Args:
            rag_id (str): RAG identifier
        """
        pass
    
    def clean_temp_files(self, rag_id):
        """
        Clean up temporary files in RAG directory.
        
        Removes:
        - Files with .tmp extension
        - Lock files (.lock)
        - Old temporary files (>24 hours)
        
        Args:
            rag_id (str): RAG identifier
        """
        pass


class ErrorHandler:
    """
    Handle and categorize ingest errors.
    
    Error Categories:
    - Validation errors: Bad input (file not found, wrong type)
    - Parse errors: Cannot read file format
    - Processing errors: Chunking, embedding generation fails
    - Storage errors: Cannot write to Qdrant or Redis
    - Retry errors: Temporary failures (network, service)
    
    Responsibilities:
    - Categorize errors
    - Determine if recoverable (retry vs fail)
    - Generate helpful error messages
    - Log errors with context
    """
    
    def __init__(self, logger):
        """
        Initialize error handler.
        
        Args:
            logger: Logger instance for logging errors
        """
        pass
    
    def categorize(self, error):
        """
        Categorize error and determine recovery action.
        
        Args:
            error (Exception): Caught exception
            
        Returns:
            dict with:
                - error_type: Category (ValidationError, ParseError, etc.)
                - error_code: Unique code (ERR_FILE_NOT_FOUND, etc.)
                - recoverable: Whether to retry
                - message: User-friendly message
                - suggestions: How to fix
        """
        pass
    
    def is_recoverable(self, error_type):
        """
        Determine if error is recoverable (should retry).
        
        Args:
            error_type (str): Error category
            
        Returns:
            bool: True if should retry
        """
        pass
    
    def format_error_details(self, error, job_id, rag_id, filename):
        """
        Format error details for logging and storage.
        
        Returns dict suitable for JSON serialization:
        - error: Error message
        - error_type: Category
        - error_code: Unique code
        - traceback: Stack trace
        - suggestions: Fix recommendations
        - context: Job and file context
        """
        pass


class Logger:
    """
    Centralized logging for ingest service.
    
    Logs to:
    - Console (INFO and above)
    - File (DEBUG and above)
    - Structured logs (JSON for parsing)
    
    Responsibilities:
    - Log job lifecycle (submitted, processing, done, failed)
    - Log detailed processing steps
    - Include context (job_id, rag_id, filename)
    - Handle different log levels
    """
    
    def __init__(self, config):
        """
        Initialize logger.
        
        Args:
            config: Configuration with:
                - app.log_level: Log level (DEBUG, INFO, WARNING, ERROR)
                - paths.logs_dir: Directory for log files
        """
        pass
    
    def info(self, message, context=None):
        """Log informational message."""
        pass
    
    def debug(self, message, context=None):
        """Log debug message."""
        pass
    
    def warning(self, message, context=None):
        """Log warning message."""
        pass
    
    def error(self, message, context=None, exception=None):
        """Log error message with exception details."""
        pass
    
    def job_submitted(self, job_id, rag_id, filename):
        """Log job submission."""
        pass
    
    def job_processing(self, job_id, step, details=None):
        """Log processing step (load, chunk, embed, upsert)."""
        pass
    
    def job_completed(self, job_id, chunks, duration):
        """Log successful completion."""
        pass
    
    def job_failed(self, job_id, error, retry_count=0):
        """Log job failure and retry attempt."""
        pass


# =============================================================================
# Data Models
# =============================================================================

class Document:
    """Loaded document with content and metadata."""
    
    def __init__(self, content, metadata=None, source_path=None):
        """
        Args:
            content (str): Full document text
            metadata (dict): Extracted metadata (title, date, author, etc.)
            source_path (str): Original file path
        """
        pass


class Chunk:
    """Document chunk with content and metadata."""
    
    def __init__(self, content, metadata=None, chunk_index=0, source=None):
        """
        Args:
            content (str): Chunk text
            metadata (dict): Chunk metadata
            chunk_index (int): Position in document (0-indexed)
            source (str): Source document path
        """
        pass


class JobMessage:
    """Job message structure (from queue)."""
    
    def __init__(self, job_id, rag_id, source_path, source_type, 
                 filename, submitted_at, options=None, retry_count=0):
        """
        Args:
            job_id (str): Unique job identifier
            rag_id (str): RAG identifier
            source_path (str): Path to document
            source_type (str): File type (pdf, txt, md, docx)
            filename (str): Original filename
            submitted_at (str): ISO timestamp
            options (dict): Processing options
            retry_count (int): Retry attempt number
        """
        pass


class JobStatus:
    """Job status record (stored in Redis)."""
    
    def __init__(self, job_id, status, metadata=None):
        """
        Args:
            job_id (str): Job identifier
            status (str): Current status (submitted, queued, processing, done, failed)
            metadata (dict): Status details (chunks, embeddings, error, etc.)
        """
        pass
```

Now let me create the worker.py skeleton:

```
# =============================================================================
# RAF Chatbot — Ingest Service: Worker
# =============================================================================
#
# This module implements the background worker that processes documents.
#
# Responsibilities:
# - Poll Redis queue for ingestion jobs
# - Load and parse documents
# - Split documents into chunks
# - Generate embeddings
# - Upsert vectors to Qdrant
# - Move files (incoming → processed/failed)
# - Update job status
# - Handle errors and retries
#
# Execution:
# Runs as Docker service: ingest-worker (see docker-compose.yml)
# Starts: python -m services.ingest.worker
#
# Implementation Note:
# This is a skeleton file with docstrings defining the interface.
# Actual implementation will be completed in Subproject 6+.
#

"""
Ingest Service Worker

Background service for processing document ingestion jobs.
"""

import asyncio
import json
import logging
from typing import Dict, Optional, List


class IngestWorker:
    """
    Background worker for document ingestion.
    
    Main loop:
    1. Connect to Redis and Qdrant
    2. Poll queue for jobs
    3. Process each job (load, chunk, embed, upsert)
    4. Move files and update status
    5. Handle errors and retries
    6. Sleep briefly before next poll
    
    Responsibilities:
    - Long-running service (polls indefinitely)
    - Asynchronous processing (handles multiple jobs)
    - Graceful shutdown (complete current job before exiting)
    - Health monitoring (heartbeat, error tracking)
    """
    
    def __init__(self, config):
        """
        Initialize worker.
        
        Args:
            config: Configuration dict with:
                - redis.url: Redis connection URL
                - qdrant.url: Qdrant connection URL
                - embeddings.model_name: Embedding model
                - chunking: Chunking configuration
                - paths: Directory paths
        
        Initializes:
        - Redis client (queue, status)
        - Qdrant client (vector storage)
        - Document loader
        - Text splitter
        - Embedding generator
        - File manager
        - Logger
        """
        pass
    
    async def run(self):
        """
        Main worker loop.
        
        Algorithm:
        ```
        while True:
            try:
                job = poll_queue()  # Wait for job from Redis
                if job is None:
                    sleep(0.5)  # Queue empty, wait and retry
                    continue
                
                process_job(job)  # Load, chunk, embed, upsert
                
            except RecoverableError:
                retry_job(job)  # Put back in queue with backoff
            except FatalError:
                fail_job(job)  # Move to failed/, mark as failed
            except Exception as e:
                log_unexpected_error(e)
                await asyncio.sleep(5)  # Brief pause before retry
        ```
        
        Runs indefinitely until:
        - Shutdown signal received
        - Fatal error with no recovery
        """
        pass
    
    async def poll_queue(self, timeout=1.0) -> Optional[Dict]:
        """
        Poll Redis queue for next job.
        
        Uses RPOP with timeout (blocks waiting for job).
        
        Args:
            timeout (float): Seconds to wait for job (0 = no wait)
            
        Returns:
            dict: Job message (JSON from queue)
            None: No job available after timeout
        """
        pass
    
    async def process_job(self, job_message: Dict) -> bool:
        """
        Process a single ingestion job.
        
        Steps:
        1. Load JobMessage from dict
        2. Update status to "processing"
        3. Load document from file
        4. Split into chunks
        5. Generate embeddings
        6. Upsert to Qdrant
        7. Move file to processed/
        8. Update status to "done"
        9. Return success
        
        Args:
            job_message (dict): Job message from queue
            
        Returns:
            bool: True if successful
            
        Raises:
            RecoverableError: Retry this job
            FatalError: Move to failed, don't retry
        """
        pass
    
    async def load_document(self, file_path: str) -> Dict:
        """
        Load and parse document from file.
        
        Args:
            file_path (str): Absolute path to document
            
        Returns:
            dict with:
                - content (str): Full text
                - metadata (dict): Extracted metadata
                - source_path (str): Original path
                
        Raises:
            ParseError: Cannot read file
            ValidationError: File is corrupted
        """
        pass
    
    async def split_document(self, document: Dict) -> List[Dict]:
        """
        Split document into chunks.
        
        Args:
            document (dict): Document with content and metadata
            
        Returns:
            List[dict]: Chunks with:
                - content (str): Chunk text
                - metadata (dict): Chunk metadata
                - chunk_index (int): Position
                - source (str): Source document path
        """
        pass
    
    async def generate_embeddings(self, chunks: List[Dict]) -> List:
        """
        Generate embeddings for chunks.
        
        Args:
            chunks (list): Document chunks with content
            
        Returns:
            List[np.ndarray]: Embeddings vectors
            
        Note:
            Implementation in Subproject 6+
        """
        pass
    
    async def upsert_to_qdrant(self, rag_id: str, chunks: List[Dict], 
                               embeddings: List, collection_name: str) -> int:
        """
        Upsert vectors to Qdrant collection.
        
        Creates points in Qdrant:
        - Vector: embedding
        - Payload: chunk content, metadata, source
        
        Args:
            rag_id (str): RAG identifier
            chunks (list): Document chunks
            embeddings (list): Vector embeddings
            collection_name (str): Qdrant collection name
            
        Returns:
            int: Number of points upserted
            
        Raises:
            ConnectionError: Qdrant unavailable
            StorageError: Upsert failed
        """
        pass
    
    async def update_job_status(self, job_id: str, status: str, 
                               metadata: Optional[Dict] = None):
        """
        Update job status in Redis.
        
        Stores in: rag:ingest:job:<job_id>
        
        Args:
            job_id (str): Job identifier
            status (str): New status (processing, done, failed)
            metadata (dict): Status details
        """
        pass
    
    async def retry_job(self, job_message: Dict, error_details: Dict):
        """
        Retry job (put back in queue with backoff).
        
        Algorithm:
        1. Increment retry_count
        2. Check if < max_retries
        3. Calculate backoff delay (exponential)
        4. Schedule job to re-enter queue after delay
        5. Log retry attempt
        
        Args:
            job_message (dict): Original job message
            error_details (dict): Error that triggered retry
        """
        pass
    
    async def fail_job(self, job_id: str, rag_id: str, file_path: str,
                      error_details: Dict):
        """
        Mark job as failed and move file to failed directory.
        
        Actions:
        1. Move file to data/sources/<rag_id>/failed/
        2. Write error details to .error.json
        3. Update status to "failed"
        4. Log failure
        
        Args:
            job_id (str): Job identifier
            rag_id (str): RAG identifier
            file_path (str): File path
            error_details (dict): Error information
        """
        pass
    
    async def handle_error(self, error: Exception, 
                          job_message: Dict) -> bool:
        """
        Handle error from job processing.
        
        Determines:
        - Is error recoverable? (retry vs fail)
        - Error category and code
        - User-friendly message
        - Suggestions for fixing
        
        Args:
            error (Exception): Caught exception
            job_message (dict): Job context
            
        Returns:
            bool: True if recoverable (will retry)
        """
        pass
    
    async def shutdown(self):
        """
        Graceful shutdown.
        
        Actions:
        1. Stop polling new jobs
        2. Complete current job (or timeout after 30 seconds)
        3. Close connections (Redis, Qdrant)
        4. Log shutdown completion
        """
        pass
    
    async def health_check(self) -> Dict:
        """
        Check worker health.
        
        Returns dict with:
        - redis_connected (bool)
        - qdrant_connected (bool)
        - queue_length (int)
        - last_job_completed (timestamp)
        - uptime_seconds (int)
        - error_count (int)
        """
        pass


async def main():
    """
    Entry point for worker.
    
    Usage:
        python -m services.ingest.worker
    
    Reads configuration from:
    - configs/client/client.yaml
    - configs/rags/*.yaml
    
    Creates worker and runs main loop.
    """
    pass


if __name__ == "__main__":
    asyncio.run(main())
```

Now let me create the cli.py skeleton:

```
# =============================================================================
# RAF Chatbot — Ingest Service: CLI
# =============================================================================
#
# Command-line interface for document ingestion.
#
# Commands:
# - ingest submit: Submit documents for processing
# - ingest status: Check job status
# - ingest reindex: Reindex entire RAG
# - queue status: Check queue health
#
# Usage:
#   python -m services.ingest.cli ingest submit --rag <id> --path <path>
#   python -m services.ingest.cli ingest status --job <job_id>
#   python -m services.ingest.cli ingest reindex --rag <id>
#   python -m services.ingest.cli queue status
#
# Implementation Note:
# This is a skeleton file with docstrings defining the interface.
# Actual implementation will be completed in Subproject 5+.
#

"""
Ingest Service CLI

Command-line interface for document ingestion management.
"""

import argparse
import json
import sys
import logging
from typing import Optional, Dict, List


class IngestCLI:
    """
    Command-line interface for ingest service.
    
    Commands:
    1. ingest submit: Submit documents to queue
    2. ingest status: Check job status
    3. ingest reindex: Reindex entire RAG
    4. queue status: Check queue health
    
    Responsibilities:
    - Parse command-line arguments
    - Validate inputs
    - Create job messages
    - Push to Redis queue
    - Query job status
    - Display results to user
    """
    
    def __init__(self, config):
        """
        Initialize CLI.
        
        Args:
            config: Configuration loaded from YAML
                - redis.url: Redis connection
                - paths: Directory configuration
                - qdrant.url: Qdrant connection
        """
        pass
    
    def ingest_submit(self, rag_id: str, path: str, 
                     reindex: bool = False,
                     skip_validation: bool = False,
                     dry_run: bool = False) -> str:
        """
        Submit documents for ingestion.
        
        Algorithm:
        1. Validate inputs (RAG exists, path exists)
        2. Find all files in path matching allowed extensions
        3. For each file:
           a. Generate unique job_id
           b. Create job message
           c. If not dry_run, push to Redis queue
           d. Create status entry in Redis
        4. Return primary job_id
        
        Args:
            rag_id (str): RAG identifier
            path (str): Directory with documents
            reindex (bool): Clear collection first
            skip_validation (bool): Skip file validation
            dry_run (bool): Show what would happen, don't submit
            
        Returns:
            str: Primary job_id
            
        Raises:
            ValidationError: RAG not found or path invalid
            ValueError: No valid files found
        """
        pass
    
    def ingest_status(self, job_id: str, 
                     follow: bool = False,
                     verbose: bool = False,
                     output_format: str = "text") -> Dict:
        """
        Check job status.
        
        Retrieves from Redis:
        - rag:ingest:job:<job_id>
        
        Fields:
        - status (queued, processing, done, failed)
        - submitted_at, started_at, completed_at
        - chunks_created, embeddings_generated
        - error (if failed)
        
        Args:
            job_id (str): Job identifier
            follow (bool): Watch status in real-time (poll every 2s)
            verbose (bool): Show detailed timing information
            output_format (str): "text" or "json"
            
        Returns:
            dict: Status information
            
        Raises:
            KeyError: Job not found
        """
        pass
    
    def ingest_reindex(self, rag_id: str,
                      force: bool = False,
                      from_processed: bool = False) -> str:
        """
        Reindex entire RAG (clear and rebuild collection).
        
        Algorithm:
        1. Validate RAG exists
        2. If not force, ask user for confirmation
        3. Clear Qdrant collection
        4. Find all files:
           - If from_processed: data/sources/<rag_id>/processed/
           - Else: data/sources/<rag_id>/incoming/
        5. Submit all files as single batch job
        6. Return job_id
        
        Args:
            rag_id (str): RAG identifier
            force (bool): Skip confirmation prompt
            from_processed (bool): Use processed/ instead of incoming/
            
        Returns:
            str: Reindex job_id
            
        Raises:
            ValidationError: RAG not found
            OperationError: Collection clear failed
        """
        pass
    
    def queue_status(self, watch: bool = False,
                    timeout: int = 300,
                    output_format: str = "text") -> Dict:
        """
        Check ingestion queue status.
        
        Information:
        - Queue length (total, processing, queued)
        - Active jobs
        - Worker connection status
        - Redis connection status
        
        Args:
            watch (bool): Monitor in real-time
            timeout (int): How long to watch (seconds)
            output_format (str): "text" or "json"
            
        Returns:
            dict: Queue status
        """
        pass
    
    def validate_rag_exists(self, rag_id: str) -> bool:
        """
        Check if RAG configuration exists.
        
        Verifies: configs/rags/<rag_id>.yaml
        
        Args:
            rag_id (str): RAG identifier
            
        Returns:
            bool: True if exists
            
        Raises:
            ValidationError: RAG not found
        """
        pass
    
    def validate_path_exists(self, path: str) -> bool:
        """
        Check if directory path exists.
        
        Args:
            path (str): Directory path
            
        Returns:
            bool: True if exists and is readable
            
        Raises:
            ValidationError: Path invalid
        """
        pass
    
    def find_documents(self, directory: str, rag_id: str) -> List[str]:
        """
        Find all processable documents in directory.
        
        Filters:
        - File extension in sources.allowed_extensions
        - File size < sources.max_file_size_mb
        - File is readable
        
        Args:
            directory (str): Directory to search
            rag_id (str): RAG (for configuration lookup)
            
        Returns:
            List[str]: Absolute paths to valid documents
        """
        pass
    
    def create_job_message(self, rag_id: str, file_path: str) -> Dict:
        """
        Create job message for Redis queue.
        
        Generates:
        - job_id: rag-<rag_id>-<timestamp>-<random>
        - rag_id, source_path, source_type, filename
        - submitted_at: ISO timestamp
        - options: reindex, skip_validation, etc.
        
        Args:
            rag_id (str): RAG identifier
            file_path (str): Document file path
            
        Returns:
            dict: Job message ready for queue
        """
        pass
    
    def submit_to_queue(self, job_message: Dict) -> str:
        """
        Submit job message to Redis queue.
        
        Actions:
        1. Serialize to JSON
        2. LPUSH to rag:ingest:queue
        3. Create status entry
        4. Return job_id
        
        Args:
            job_message (dict): Job message
            
        Returns:
            str: job_id
        """
        pass
    
    def print_status_text(self, status: Dict):
        """Format and print status as human-readable text."""
        pass
    
    def print_status_json(self, status: Dict):
        """Format and print status as JSON."""
        pass


def parse_arguments() -> argparse.Namespace:
    """
    Parse command-line arguments.
    
    Returns:
        Namespace with parsed arguments
    """
    pass


def main():
    """
    Main entry point for CLI.
    
    Usage:
        python -m services.ingest.cli ingest submit --rag <id> --path <path>
    """
    pass


if __name__ == "__main__":
    main()