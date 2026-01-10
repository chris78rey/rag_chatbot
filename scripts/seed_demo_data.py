import os
import sys
import subprocess
import time
from qdrant_client import QdrantClient

def wait_for_qdrant(url, timeout=30):
    """Espera a que Qdrant esté listo."""
    client = QdrantClient(url=url)
    start_time = time.time()
    while time.time() - start_time < timeout:
        try:
            client.get_collections()
            return True
        except Exception:
            time.sleep(2)
    return False

def run_seed():
    qdrant_url = os.getenv("QDRANT_URL", "http://qdrant:6333")
    print(f"Checking Qdrant at {qdrant_url}...")
    
    if not wait_for_qdrant(qdrant_url):
        print("Error: Qdrant not reachable")
        return

    client = QdrantClient(url=qdrant_url)
    collections = client.get_collections().collections
    
    # Si la colección 'default' no existe o está vacía
    exists = any(c.name == "default" for c in collections)
    points_count = 0
    if exists:
        try:
            points_count = client.get_collection("default").points_count
        except Exception:
            points_count = 0
    
    if not exists or points_count == 0:
        print("🌱 Database empty. Starting automatic ingestion...")
        # Ejecutamos el script de ingesta real
        cmd = [
            "python", "/workspace/scripts/ingest_txt.py", 
            "/workspace/data/ragpetro_2.txt", 
            "--rag-id", "default", 
            "--by-lines", "--lines-per-chunk", "3"
        ]
        result = subprocess.run(cmd, capture_output=True, text=True)
        print(result.stdout)
        if result.returncode == 0:
            print("✅ Automatic ingestion complete!")
        else:
            print("❌ Error during ingestion:")
            print(result.stderr)
    else:
        print(f"✅ Database already has data in 'default' collection ({points_count} points). Skipping seed.")

if __name__ == "__main__":
    run_seed()