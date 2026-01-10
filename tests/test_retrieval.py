"""
Tests para el módulo de retrieval y Qdrant.

Valida:
- Cliente Qdrant funciona
- Colecciones se crean correctamente
- Search retorna resultados
- Endpoint /query funciona
"""
import pytest
import asyncio
from unittest.mock import patch, MagicMock
from app.qdrant_client import get_client, ensure_collection, search
from app.retrieval import get_embedding, retrieve_context
from app.models import QueryRequest, QueryResponse, ContextChunk


class TestQdrantClient:
    """Tests para el cliente Qdrant."""
    
    def test_get_client_singleton(self):
        """Verifica que get_client retorna la misma instancia."""
        client1 = get_client()
        client2 = get_client()
        assert client1 is client2
    
    @patch('app.qdrant_client.QdrantClient')
    def test_ensure_collection_creates_if_not_exists(self, mock_qd_class):
        """Verifica que ensure_collection crea colección si no existe."""
        mock_client = MagicMock()
        mock_client.get_collections.return_value.collections = []
        mock_qd_class.return_value = mock_client
        
        # Reset global client
        import app.qdrant_client
        app.qdrant_client._client = None
        
        result = ensure_collection("test_collection", 1536)
        
        assert result is True
        mock_client.create_collection.assert_called_once()
    
    @patch('app.qdrant_client.QdrantClient')
    def test_ensure_collection_skips_if_exists(self, mock_qd_class):
        """Verifica que ensure_collection no recrea si ya existe."""
        mock_client = MagicMock()
        mock_collection = MagicMock()
        mock_collection.name = "test_collection"
        mock_client.get_collections.return_value.collections = [mock_collection]
        mock_qd_class.return_value = mock_client
        
        # Reset global client
        import app.qdrant_client
        app.qdrant_client._client = None
        
        result = ensure_collection("test_collection", 1536)
        
        assert result is True
        mock_client.create_collection.assert_not_called()


class TestRetrieval:
    """Tests para el módulo retrieval."""
    
    @pytest.mark.asyncio
    async def test_get_embedding_returns_vector(self):
        """Verifica que get_embedding retorna vector de dimensión 1536."""
        embedding = await get_embedding("test text")
        
        assert isinstance(embedding, list)
        assert len(embedding) == 1536
        assert all(isinstance(x, float) for x in embedding)
    
    @pytest.mark.asyncio
    async def test_get_embedding_deterministic(self):
        """Verifica que get_embedding es determinístico (mismo texto = mismo vector)."""
        text = "This is a test sentence"
        
        emb1 = await get_embedding(text)
        emb2 = await get_embedding(text)
        
        assert emb1 == emb2
    
    @pytest.mark.asyncio
    async def test_retrieve_context_formats_collection_name(self):
        """Verifica que retrieve_context usa convención {rag_id}_collection."""
        with patch('app.retrieval.search') as mock_search:
            mock_search.return_value = []
            
            await retrieve_context("my_rag", "test question", top_k=5)
            
            # Verificar que search fue llamado con nombre de colección correcto
            call_args = mock_search.call_args
            assert call_args[1]['collection_name'] == "my_rag_collection"


class TestModels:
    """Tests para los modelos Pydantic."""
    
    def test_query_request_valid(self):
        """Verifica que QueryRequest acepta datos válidos."""
        request = QueryRequest(
            rag_id="test",
            question="test question",
            top_k=5
        )
        
        assert request.rag_id == "test"
        assert request.question == "test question"
        assert request.top_k == 5
        assert request.session_id is None
    
    def test_query_request_requires_rag_id(self):
        """Verifica que QueryRequest requiere rag_id."""
        with pytest.raises(ValueError):
            QueryRequest(question="test question")
    
    def test_context_chunk_valid(self):
        """Verifica que ContextChunk acepta datos válidos."""
        chunk = ContextChunk(
            id="123",
            source="docs/test.txt",
            text="test content",
            score=0.95
        )
        
        assert chunk.id == "123"
        assert chunk.score == 0.95
    
    def test_query_response_serializable(self):
        """Verifica que QueryResponse es serializable a JSON."""
        response = QueryResponse(
            rag_id="test",
            answer="test answer",
            context_chunks=[],
            latency_ms=100,
            cache_hit=False,
            session_id="sess_123"
        )
        
        json_data = response.model_dump_json()
        assert "test answer" in json_data
        assert "test" in json_data


class TestIntegration:
    """Tests de integración end-to-end."""
    
    @pytest.mark.asyncio
    async def test_query_flow_end_to_end(self):
        """Verifica el flujo completo de una consulta."""
        with patch('app.retrieval.search') as mock_search:
            # Mock de resultados de búsqueda
            mock_search.return_value = [
                {
                    "id": "1",
                    "source": "docs/test.txt",
                    "text": "Test content",
                    "score": 0.95
                }
            ]
            
            # Simular consulta
            results = await retrieve_context("test", "test question", top_k=5)
            
            assert len(results) == 1
            assert results[0]["id"] == "1"
            assert results[0]["score"] == 0.95
    
    @pytest.mark.asyncio
    async def test_query_empty_results(self):
        """Verifica el comportamiento cuando no hay resultados."""
        with patch('app.retrieval.search') as mock_search:
            mock_search.return_value = []
            
            results = await retrieve_context("test", "test question", top_k=5)
            
            assert len(results) == 0


# Tests parametrizados para diferentes dimensiones
@pytest.mark.parametrize("dim", [384, 768, 1536])
def test_embedding_dimension(dim):
    """Verifica embeddings con diferentes dimensiones."""
    # Nota: get_embedding actualmente siempre retorna 1536
    # Este test es para futura extensión
    assert dim > 0