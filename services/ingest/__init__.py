# =============================================================================
# RAF Chatbot — Ingest Service Package
# =============================================================================
#
# This package provides document ingestion capabilities for the RAG system.
#
# Modules:
# - app.py: Shared utilities (loaders, splitters, file management)
# - cli.py: Command-line interface for job submission
# - worker.py: Background worker for job processing
#
# Usage:
#   from services.ingest.app import DocumentLoader, TextSplitter
#   from services.ingest.cli import IngestCLI
#   from services.ingest.worker import IngestWorker
#

"""
Ingest Service Package

Provides document loading, chunking, embedding, and ingestion management.
"""

__version__ = "0.1.0"
__author__ = "RAF Chatbot Team"

# Module exports
__all__ = [
    "app",
    "cli",
    "worker",
]