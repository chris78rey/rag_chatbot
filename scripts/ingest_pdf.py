#!/usr/bin/env python3
"""
Script simple para ingestar PDFs en RAF Chatbot.

Uso:
    python scripts/ingest_pdf.py <archivo.pdf> [--rag-id <id>]
    python scripts/ingest_pdf.py documento.pdf --rag-id mi_proyecto
    python scripts/ingest_pdf.py carpeta/ --rag-id default  # Todos los PDFs de una carpeta

Requiere:
    pip install PyPDF2 qdrant-client

Este script:
1. Lee el PDF y extrae texto
2. Divide en chunks
3. Genera embeddings (placeholder por ahora)
4. Sube a Qdrant

Autor: RAF Chatbot Team
Fecha: 2026-01-09
"""

import argparse
import hashlib
import os
import random
import sys
from pathlib import Path
from typing import List, Dict, Any, Optional

# Agregar path del proyecto
sys.path.insert(0, str(Path(__file__).parent.parent))


def extract_text_from_pdf(pdf_path: str) -> List[Dict[str, Any]]:
    """
    Extrae texto de un PDF página por página.
    
    Args:
        pdf_path: Ruta al archivo PDF
        
    Returns:
        Lista de dicts con {page, text}
    """
    try:
        from PyPDF2 import PdfReader
    except ImportError:
        print("Error: PyPDF2 no está instalado.")
        print("Instala con: pip install PyPDF2")
        sys.exit(1)
    
    pages = []
    reader = PdfReader(pdf_path)
    
    for i, page in enumerate(reader.pages):
        text = page.extract_text()
        if text and text.strip():
            pages.append({
                "page": i + 1,
                "text": text.strip()
            })
    
    return pages


def chunk_text(text: str, chunk_size: int = 500, overlap: int = 50) -> List[str]:
    """
    Divide texto en chunks con overlap.
    
    Args:
        text: Texto a dividir
        chunk_size: Tamaño máximo de cada chunk (caracteres)
        overlap: Caracteres de overlap entre chunks
        
    Returns:
        Lista de chunks
    """
    if len(text) <= chunk_size:
        return [text]
    
    chunks = []
    start = 0
    
    while start < len(text):
        end = start + chunk_size
        
        # Intentar cortar en un espacio o punto
        if end < len(text):
            # Buscar punto o salto de línea cerca del final
            for sep in ['. ', '.\n', '\n\n', '\n', ' ']:
                last_sep = text.rfind(sep, start + chunk_size // 2, end)
                if last_sep != -1:
                    end = last_sep + len(sep)
                    break
        
        chunk = text[start:end].strip()
        if chunk:
            chunks.append(chunk)
        
        start = end - overlap
        if start >= len(text):
            break
    
    return chunks


def generate_embedding(text: str, dim: int = 384) -> List[float]:
    """
    Genera embedding para texto.
    
    NOTA: Esto es un placeholder que genera vectores pseudo-aleatorios
    basados en el hash del texto. En producción, usar un modelo real
    como sentence-transformers o OpenAI embeddings.
    
    Args:
        text: Texto a vectorizar
        dim: Dimensión del vector
        
    Returns:
        Vector de embeddings
    """
    # Placeholder: vector determinístico basado en hash
    hash_val = int(hashlib.md5(text.encode()).hexdigest(), 16)
    random.seed(hash_val)
    return [random.uniform(-1, 1) for _ in range(dim)]


def ensure_collection(client, collection_name: str, vector_dim: int = 384):
    """
    Crea colección en Qdrant si no existe.
    """
    from qdrant_client.http import models
    
    try:
        collections = client.get_collections().collections
        exists = any(c.name == collection_name for c in collections)
        
        if not exists:
            client.create_collection(
                collection_name=collection_name,
                vectors_config=models.VectorParams(
                    size=vector_dim,
                    distance=models.Distance.COSINE
                )
            )
            print(f"✓ Colección '{collection_name}' creada")
        else:
            print(f"✓ Colección '{collection_name}' ya existe")
            
    except Exception as e:
        print(f"✗ Error con colección: {e}")
        raise


def ingest_pdf(
    pdf_path: str,
    rag_id: str = "default",
    qdrant_url: str = None,
    chunk_size: int = 500,
    chunk_overlap: int = 50,
    vector_dim: int = 384
) -> int:
    """
    Ingesta un PDF completo a Qdrant.
    
    Args:
        pdf_path: Ruta al PDF
        rag_id: ID del RAG (será el nombre de la colección)
        qdrant_url: URL de Qdrant
        chunk_size: Tamaño de chunks
        chunk_overlap: Overlap entre chunks
        vector_dim: Dimensión de embeddings
        
    Returns:
        Número de chunks insertados
    """
    from qdrant_client import QdrantClient
    from qdrant_client.http import models
    
    # Configurar URL de Qdrant
    qdrant_url = qdrant_url or os.getenv("QDRANT_URL", "http://localhost:6333")
    
    print(f"\n{'='*60}")
    print(f"Ingestando: {pdf_path}")
    print(f"RAG ID: {rag_id}")
    print(f"Qdrant: {qdrant_url}")
    print(f"{'='*60}\n")
    
    # Verificar que el archivo existe
    if not os.path.exists(pdf_path):
        print(f"✗ Error: Archivo no encontrado: {pdf_path}")
        return 0
    
    # Extraer texto del PDF
    print("1. Extrayendo texto del PDF...")
    pages = extract_text_from_pdf(pdf_path)
    print(f"   ✓ {len(pages)} páginas extraídas")
    
    if not pages:
        print("   ⚠ No se encontró texto en el PDF")
        return 0
    
    # Crear chunks
    print("2. Dividiendo en chunks...")
    all_chunks = []
    filename = os.path.basename(pdf_path)
    
    for page_data in pages:
        page_chunks = chunk_text(page_data["text"], chunk_size, chunk_overlap)
        
        for i, chunk_text_content in enumerate(page_chunks):
            all_chunks.append({
                "id": f"{filename}_p{page_data['page']}_c{i}",
                "text": chunk_text_content,
                "source_path": filename,
                "page": page_data["page"],
                "chunk_index": i,
            })
    
    print(f"   ✓ {len(all_chunks)} chunks creados")
    
    # Generar embeddings
    print("3. Generando embeddings...")
    vectors = [generate_embedding(c["text"], vector_dim) for c in all_chunks]
    print(f"   ✓ {len(vectors)} embeddings generados (dim={vector_dim})")
    
    # Conectar a Qdrant
    print("4. Conectando a Qdrant...")
    try:
        client = QdrantClient(url=qdrant_url)
        print(f"   ✓ Conectado a {qdrant_url}")
    except Exception as e:
        print(f"   ✗ Error conectando a Qdrant: {e}")
        return 0
    
    # Asegurar que la colección existe
    print(f"5. Verificando colección '{rag_id}'...")
    ensure_collection(client, rag_id, vector_dim)
    
    # Crear puntos para Qdrant
    print("6. Subiendo a Qdrant...")
    points = []
    
    for i, (chunk, vector) in enumerate(zip(all_chunks, vectors)):
        # Generar ID numérico único basado en hash
        point_id = int(hashlib.md5(chunk["id"].encode()).hexdigest()[:15], 16)
        
        points.append(models.PointStruct(
            id=point_id,
            vector=vector,
            payload={
                "text": chunk["text"],
                "source_path": chunk["source_path"],
                "source": chunk["source_path"],  # Alias para compatibilidad
                "page": chunk["page"],
                "chunk_index": chunk["chunk_index"],
                "chunk_id": chunk["id"],
            }
        ))
    
    # Upsert en batches de 100
    batch_size = 100
    for i in range(0, len(points), batch_size):
        batch = points[i:i + batch_size]
        client.upsert(collection_name=rag_id, points=batch)
        print(f"   ✓ Batch {i//batch_size + 1}/{(len(points)-1)//batch_size + 1} subido")
    
    # Verificar
    print("7. Verificando...")
    info = client.get_collection(rag_id)
    print(f"   ✓ Colección '{rag_id}' tiene {info.points_count} puntos")
    
    print(f"\n{'='*60}")
    print(f"✅ Ingesta completada: {len(all_chunks)} chunks")
    print(f"{'='*60}\n")
    
    return len(all_chunks)


def ingest_directory(
    directory: str,
    rag_id: str = "default",
    qdrant_url: str = None,
    **kwargs
) -> int:
    """
    Ingesta todos los PDFs de un directorio.
    """
    pdf_files = list(Path(directory).glob("*.pdf"))
    
    if not pdf_files:
        print(f"⚠ No se encontraron PDFs en: {directory}")
        return 0
    
    print(f"Encontrados {len(pdf_files)} PDFs en {directory}")
    
    total_chunks = 0
    for pdf_path in pdf_files:
        chunks = ingest_pdf(str(pdf_path), rag_id, qdrant_url, **kwargs)
        total_chunks += chunks
    
    print(f"\n{'='*60}")
    print(f"✅ Total: {total_chunks} chunks de {len(pdf_files)} PDFs")
    print(f"{'='*60}\n")
    
    return total_chunks


def main():
    parser = argparse.ArgumentParser(
        description="Ingestar PDFs en RAF Chatbot",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Ejemplos:
    python scripts/ingest_pdf.py documento.pdf
    python scripts/ingest_pdf.py documento.pdf --rag-id mi_proyecto
    python scripts/ingest_pdf.py ./pdfs/ --rag-id documentos
    python scripts/ingest_pdf.py doc.pdf --chunk-size 1000
        """
    )
    
    parser.add_argument(
        "path",
        help="Archivo PDF o directorio con PDFs"
    )
    parser.add_argument(
        "--rag-id", "-r",
        default="default",
        help="ID del RAG / nombre de colección (default: 'default')"
    )
    parser.add_argument(
        "--qdrant-url", "-q",
        default=None,
        help="URL de Qdrant (default: QDRANT_URL env o localhost:6333)"
    )
    parser.add_argument(
        "--chunk-size", "-c",
        type=int,
        default=500,
        help="Tamaño de chunks en caracteres (default: 500)"
    )
    parser.add_argument(
        "--chunk-overlap", "-o",
        type=int,
        default=50,
        help="Overlap entre chunks (default: 50)"
    )
    parser.add_argument(
        "--vector-dim", "-d",
        type=int,
        default=384,
        help="Dimensión de embeddings (default: 384)"
    )
    
    args = parser.parse_args()
    
    # Verificar si es archivo o directorio
    path = Path(args.path)
    
    kwargs = {
        "rag_id": args.rag_id,
        "qdrant_url": args.qdrant_url,
        "chunk_size": args.chunk_size,
        "chunk_overlap": args.chunk_overlap,
        "vector_dim": args.vector_dim,
    }
    
    if path.is_dir():
        total = ingest_directory(str(path), **kwargs)
    elif path.is_file() and path.suffix.lower() == ".pdf":
        total = ingest_pdf(str(path), **kwargs)
    else:
        print(f"✗ Error: '{args.path}' no es un PDF válido ni un directorio")
        sys.exit(1)
    
    if total == 0:
        sys.exit(1)


if __name__ == "__main__":
    main()