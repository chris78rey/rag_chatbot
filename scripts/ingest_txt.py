#!/usr/bin/env python3
"""
Script para ingestar archivos TXT en RAF Chatbot con embeddings reales.

Usa sentence-transformers local (GRATIS, sin API key).
Modelo: paraphrase-multilingual-MiniLM-L12-v2 (384 dimensiones, multilingüe recomendado)

Uso:
    python scripts/ingest_txt.py <archivo.txt> [--rag-id <id>]
    python scripts/ingest_txt.py documento.txt --rag-id mi_proyecto
    python scripts/ingest_txt.py carpeta/ --rag-id default

Requiere:
    pip install sentence-transformers qdrant-client

Autor: RAF Chatbot Team
"""

import argparse
import hashlib
import os
import sys
from pathlib import Path
from typing import List, Dict, Any

# Agregar path del proyecto
sys.path.insert(0, str(Path(__file__).parent.parent))

# Configuración de embeddings
EMBEDDING_MODEL = "paraphrase-multilingual-MiniLM-L12-v2"  # Multilingüe, recomendado para español
EMBEDDING_DIM = 384

# Modelo global (singleton)
_model = None


def get_model():
    """Carga el modelo de sentence-transformers (singleton)."""
    global _model
    if _model is None:
        print(f"   Cargando modelo: {EMBEDDING_MODEL}...")
        from sentence_transformers import SentenceTransformer
        _model = SentenceTransformer(EMBEDDING_MODEL)
        print(f"   ✓ Modelo cargado (dim={EMBEDDING_DIM})")
    return _model


def get_embeddings_batch(texts: List[str], show_progress: bool = True) -> List[List[float]]:
    """
    Genera embeddings para múltiples textos usando sentence-transformers.
    
    Args:
        texts: Lista de textos a vectorizar
        show_progress: Mostrar barra de progreso
        
    Returns:
        Lista de vectores de embeddings (384 dimensiones cada uno)
    """
    if not texts:
        return []
    
    model = get_model()
    
    # Generar embeddings en batch (más eficiente)
    embeddings = model.encode(
        texts, 
        convert_to_numpy=True, 
        show_progress_bar=show_progress,
        batch_size=64
    )
    
    # Convertir a lista de listas de floats
    return [emb.tolist() for emb in embeddings]


def read_text_file(file_path: str) -> str:
    """Lee contenido de un archivo de texto."""
    encodings = ['utf-8', 'latin-1', 'cp1252', 'iso-8859-1']
    
    for encoding in encodings:
        try:
            with open(file_path, 'r', encoding=encoding) as f:
                return f.read()
        except UnicodeDecodeError:
            continue
    
    raise ValueError(f"No se pudo leer el archivo: {file_path}")


def chunk_text(text: str, chunk_size: int = 500, overlap: int = 50) -> List[str]:
    """Divide texto en chunks con overlap."""
    if len(text) <= chunk_size:
        return [text]
    
    chunks = []
    start = 0
    
    while start < len(text):
        end = start + chunk_size
        
        if end < len(text):
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


def chunk_by_lines(text: str, lines_per_chunk: int = 3) -> List[str]:
    """Divide texto por líneas (útil para archivos Q&A)."""
    lines = [line.strip() for line in text.split('\n') if line.strip()]
    
    chunks = []
    for i in range(0, len(lines), lines_per_chunk):
        chunk = '\n'.join(lines[i:i + lines_per_chunk])
        if chunk:
            chunks.append(chunk)
    
    return chunks


def ensure_collection(client, collection_name: str, vector_dim: int = EMBEDDING_DIM):
    """Crea colección en Qdrant si no existe."""
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
            print(f"✓ Colección '{collection_name}' creada (dim={vector_dim})")
        else:
            # Verificar dimensión
            info = client.get_collection(collection_name)
            current_dim = info.config.params.vectors.size
            if current_dim != vector_dim:
                print(f"⚠ Colección existe con dim={current_dim}, recreando...")
                client.delete_collection(collection_name)
                client.create_collection(
                    collection_name=collection_name,
                    vectors_config=models.VectorParams(
                        size=vector_dim,
                        distance=models.Distance.COSINE
                    )
                )
                print(f"✓ Colección '{collection_name}' recreada (dim={vector_dim})")
            else:
                print(f"✓ Colección '{collection_name}' ya existe (dim={vector_dim})")
            
    except Exception as e:
        print(f"✗ Error con colección: {e}")
        raise


def ingest_txt(
    txt_path: str,
    rag_id: str = "default",
    qdrant_url: str = None,
    chunk_size: int = 500,
    chunk_overlap: int = 50,
    by_lines: bool = False,
    lines_per_chunk: int = 3
) -> int:
    """
    Ingesta un archivo TXT con embeddings reales de sentence-transformers.
    
    Args:
        txt_path: Ruta al archivo TXT
        rag_id: ID del RAG (nombre de colección)
        qdrant_url: URL de Qdrant
        chunk_size: Tamaño de chunks
        chunk_overlap: Overlap entre chunks
        by_lines: Dividir por líneas
        lines_per_chunk: Líneas por chunk
        
    Returns:
        Número de chunks insertados
    """
    from qdrant_client import QdrantClient
    from qdrant_client.http import models
    
    # Configuración
    qdrant_url = qdrant_url or os.getenv("QDRANT_URL", "http://localhost:6333")
    
    print(f"\n{'='*60}")
    print(f"Ingestando: {txt_path}")
    print(f"RAG ID: {rag_id}")
    print(f"Qdrant: {qdrant_url}")
    print(f"Modelo: {EMBEDDING_MODEL} (dim={EMBEDDING_DIM})")
    print(f"Modo: {'por líneas' if by_lines else 'por caracteres'}")
    print(f"{'='*60}\n")
    
    # Verificar archivo
    if not os.path.exists(txt_path):
        print(f"✗ Error: Archivo no encontrado: {txt_path}")
        return 0
    
    # Leer archivo
    print("1. Leyendo archivo...")
    try:
        text = read_text_file(txt_path)
        print(f"   ✓ {len(text):,} caracteres leídos")
    except Exception as e:
        print(f"   ✗ Error: {e}")
        return 0
    
    if not text.strip():
        print("   ⚠ Archivo vacío")
        return 0
    
    # Crear chunks
    print("2. Dividiendo en chunks...")
    filename = os.path.basename(txt_path)
    
    if by_lines:
        text_chunks = chunk_by_lines(text, lines_per_chunk)
    else:
        text_chunks = chunk_text(text, chunk_size, chunk_overlap)
    
    print(f"   ✓ {len(text_chunks):,} chunks creados")
    
    # Generar embeddings
    print("3. Generando embeddings (esto puede tomar unos minutos)...")
    try:
        vectors = get_embeddings_batch(text_chunks, show_progress=True)
        print(f"   ✓ {len(vectors):,} embeddings generados")
    except Exception as e:
        print(f"   ✗ Error: {e}")
        return 0
    
    # Conectar a Qdrant
    print("4. Conectando a Qdrant...")
    try:
        client = QdrantClient(url=qdrant_url)
        print(f"   ✓ Conectado")
    except Exception as e:
        print(f"   ✗ Error: {e}")
        return 0
    
    # Asegurar colección
    print(f"5. Verificando colección '{rag_id}'...")
    ensure_collection(client, rag_id, EMBEDDING_DIM)
    
    # Crear puntos
    print("6. Subiendo a Qdrant...")
    points = []
    
    for i, (chunk_text_content, vector) in enumerate(zip(text_chunks, vectors)):
        chunk_id = f"{filename}_c{i}"
        point_id = int(hashlib.md5(chunk_id.encode()).hexdigest()[:15], 16)
        
        points.append(models.PointStruct(
            id=point_id,
            vector=vector,
            payload={
                "text": chunk_text_content,
                "source_path": filename,
                "source": filename,
                "chunk_index": i,
                "chunk_id": chunk_id,
            }
        ))
    
    # Upsert en batches
    batch_size = 100
    for i in range(0, len(points), batch_size):
        batch = points[i:i + batch_size]
        client.upsert(collection_name=rag_id, points=batch)
        print(f"   ✓ Batch {i//batch_size + 1}/{(len(points)-1)//batch_size + 1} subido")
    
    # Verificar
    print("7. Verificando...")
    info = client.get_collection(rag_id)
    print(f"   ✓ Colección '{rag_id}' tiene {info.points_count:,} puntos")
    
    print(f"\n{'='*60}")
    print(f"✅ Ingesta completada: {len(text_chunks):,} chunks")
    print(f"{'='*60}\n")
    
    return len(text_chunks)


def ingest_directory(directory: str, **kwargs) -> int:
    """Ingesta todos los TXT de un directorio."""
    txt_files = list(Path(directory).glob("*.txt"))
    
    if not txt_files:
        print(f"⚠ No se encontraron archivos TXT en: {directory}")
        return 0
    
    print(f"Encontrados {len(txt_files)} archivos TXT")
    
    total_chunks = 0
    for txt_path in txt_files:
        chunks = ingest_txt(str(txt_path), **kwargs)
        total_chunks += chunks
    
    return total_chunks


def main():
    parser = argparse.ArgumentParser(
        description="Ingestar archivos TXT con sentence-transformers (GRATIS)",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Ejemplos:
    python scripts/ingest_txt.py documento.txt
    python scripts/ingest_txt.py documento.txt --rag-id mi_proyecto
    python scripts/ingest_txt.py qa.txt --by-lines --lines-per-chunk 3
    
Modelo: paraphrase-multilingual-MiniLM-L12-v2 (384 dimensiones, multilingüe)
No requiere API key - 100% local y gratis.
        """
    )
    
    parser.add_argument("path", help="Archivo TXT o directorio")
    parser.add_argument("--rag-id", "-r", default="default", help="ID del RAG")
    parser.add_argument("--qdrant-url", "-q", default=None, help="URL de Qdrant")
    parser.add_argument("--chunk-size", "-c", type=int, default=500, help="Tamaño de chunks")
    parser.add_argument("--chunk-overlap", "-o", type=int, default=50, help="Overlap")
    parser.add_argument("--by-lines", "-l", action="store_true", help="Dividir por líneas")
    parser.add_argument("--lines-per-chunk", type=int, default=3, help="Líneas por chunk")
    
    args = parser.parse_args()
    
    path = Path(args.path)
    
    kwargs = {
        "rag_id": args.rag_id,
        "qdrant_url": args.qdrant_url,
        "chunk_size": args.chunk_size,
        "chunk_overlap": args.chunk_overlap,
        "by_lines": args.by_lines,
        "lines_per_chunk": args.lines_per_chunk,
    }
    
    if path.is_dir():
        total = ingest_directory(str(path), **kwargs)
    elif path.is_file():
        total = ingest_txt(str(path), **kwargs)
    else:
        print(f"✗ Error: '{args.path}' no existe")
        sys.exit(1)
    
    if total == 0:
        sys.exit(1)


if __name__ == "__main__":
    main()