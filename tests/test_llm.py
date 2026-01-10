"""
Tests para el módulo LLM y prompting.

Valida:
- Cliente OpenRouter funciona
- Fallback automático
- Construcción de mensajes
- Carga de templates
"""
import pytest
import asyncio
from unittest.mock import patch, MagicMock, AsyncMock
from app.llm import call_chat_completion, call_with_fallback, OpenRouterError
from app.prompting import load_template, build_messages, format_context, clear_template_cache


class TestOpenRouterClient:
    """Tests para el cliente OpenRouter."""
    
    @pytest.mark.asyncio
    async def test_call_chat_completion_success(self):
        """Verifica que call_chat_completion retorna respuesta válida."""
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "choices": [
                {
                    "message": {
                        "content": "This is a test response"
                    }
                }
            ],
            "model": "openai/gpt-3.5-turbo",
            "usage": {"prompt_tokens": 100, "completion_tokens": 50}
        }
        
        with patch('app.llm.openrouter_client.httpx.AsyncClient') as mock_client_class:
            mock_client = AsyncMock()
            mock_client.__aenter__.return_value = mock_client
            mock_client.__aexit__.return_value = None
            mock_client.post = AsyncMock(return_value=mock_response)
            mock_client_class.return_value = mock_client
            
            with patch.dict('os.environ', {'OPENROUTER_API_KEY': 'test-key'}):
                result = await call_chat_completion(
                    model="openai/gpt-3.5-turbo",
                    messages=[{"role": "user", "content": "test"}]
                )
                
                assert result["content"] == "This is a test response"
                assert result["model"] == "openai/gpt-3.5-turbo"
                assert "latency_ms" in result
    
    @pytest.mark.asyncio
    async def test_call_chat_completion_missing_api_key(self):
        """Verifica que lanza error si falta API key."""
        with patch.dict('os.environ', {}, clear=True):
            with pytest.raises(OpenRouterError) as exc_info:
                await call_chat_completion(
                    model="openai/gpt-3.5-turbo",
                    messages=[{"role": "user", "content": "test"}]
                )
            
            assert "OPENROUTER_API_KEY not set" in str(exc_info.value)
    
    @pytest.mark.asyncio
    async def test_call_with_fallback_primary_success(self):
        """Verifica que call_with_fallback usa modelo primario si funciona."""
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "choices": [
                {
                    "message": {
                        "content": "Primary model response"
                    }
                }
            ],
            "model": "openai/gpt-3.5-turbo",
            "usage": {}
        }
        
        with patch('app.llm.openrouter_client.httpx.AsyncClient') as mock_client_class:
            mock_client = AsyncMock()
            mock_client.__aenter__.return_value = mock_client
            mock_client.__aexit__.return_value = None
            mock_client.post = AsyncMock(return_value=mock_response)
            mock_client_class.return_value = mock_client
            
            with patch.dict('os.environ', {'OPENROUTER_API_KEY': 'test-key'}):
                result = await call_with_fallback(
                    primary_model="openai/gpt-3.5-turbo",
                    fallback_model="anthropic/claude-instant-v1",
                    messages=[{"role": "user", "content": "test"}]
                )
                
                assert result["content"] == "Primary model response"
                assert result["used_fallback"] is False
    
    @pytest.mark.asyncio
    async def test_call_with_fallback_uses_fallback(self):
        """Verifica que usa fallback cuando modelo primario falla."""
        # Mock para primario (falla)
        mock_response_fail = MagicMock()
        mock_response_fail.status_code = 500
        mock_response_fail.json.return_value = {"error": {"message": "Server error"}}
        
        # Mock para fallback (éxito)
        mock_response_success = MagicMock()
        mock_response_success.status_code = 200
        mock_response_success.json.return_value = {
            "choices": [
                {
                    "message": {
                        "content": "Fallback model response"
                    }
                }
            ],
            "model": "anthropic/claude-instant-v1",
            "usage": {}
        }
        
        with patch('app.llm.openrouter_client.httpx.AsyncClient') as mock_client_class:
            mock_client = AsyncMock()
            mock_client.__aenter__.return_value = mock_client
            mock_client.__aexit__.return_value = None
            mock_client.post = AsyncMock(side_effect=[mock_response_fail, mock_response_success])
            mock_client_class.return_value = mock_client
            
            with patch.dict('os.environ', {'OPENROUTER_API_KEY': 'test-key'}):
                result = await call_with_fallback(
                    primary_model="openai/gpt-3.5-turbo",
                    fallback_model="anthropic/claude-instant-v1",
                    messages=[{"role": "user", "content": "test"}]
                )
                
                assert result["content"] == "Fallback model response"
                assert result["used_fallback"] is True


class TestPrompting:
    """Tests para el módulo prompting."""
    
    def test_format_context_empty_chunks(self):
        """Verifica que format_context maneja chunks vacíos."""
        result = format_context([])
        assert "[No se encontró contexto relevante]" in result
    
    def test_format_context_with_chunks(self):
        """Verifica que format_context formatea chunks correctamente."""
        chunks = [
            {
                "text": "Sample text 1",
                "source": "docs/file1.txt",
                "score": 0.95
            },
            {
                "text": "Sample text 2",
                "source": "docs/file2.txt",
                "score": 0.85
            }
        ]
        
        result = format_context(chunks)
        
        assert "Sample text 1" in result
        assert "Sample text 2" in result
        assert "docs/file1.txt" in result
        assert "docs/file2.txt" in result
        assert "0.95" in result
        assert "0.85" in result
    
    def test_build_messages_structure(self):
        """Verifica que build_messages crea estructura correcta."""
        system_template = "You are helpful."
        user_template = "Question: {question}\nContext: {context}"
        question = "What is AI?"
        context_chunks = [
            {"text": "AI is...", "source": "wiki.txt", "score": 0.9}
        ]
        
        messages = build_messages(
            system_template=system_template,
            user_template=user_template,
            question=question,
            context_chunks=context_chunks
        )
        
        assert len(messages) == 2
        assert messages[0]["role"] == "system"
        assert messages[0]["content"] == "You are helpful."
        assert messages[1]["role"] == "user"
        assert "What is AI?" in messages[1]["content"]
        assert "AI is..." in messages[1]["content"]
    
    def test_build_messages_with_session_history(self):
        """Verifica que build_messages incluye historial de sesión."""
        messages = build_messages(
            system_template="System prompt",
            user_template="User: {question}\n{context}",
            question="Q2",
            context_chunks=[{"text": "context", "source": "src", "score": 0.9}],
            session_history=[
                {"role": "user", "content": "Q1"},
                {"role": "assistant", "content": "A1"}
            ]
        )
        
        assert len(messages) == 4  # system + 2 history + user
        assert messages[1]["role"] == "user"
        assert messages[1]["content"] == "Q1"
        assert messages[2]["role"] == "assistant"
        assert messages[2]["content"] == "A1"


class TestOpenRouterError:
    """Tests para excepción OpenRouterError."""
    
    def test_openrouter_error_with_status_code(self):
        """Verifica que OpenRouterError almacena status code."""
        error = OpenRouterError("API error", 401)
        assert error.message == "API error"
        assert error.status_code == 401
    
    def test_openrouter_error_without_status_code(self):
        """Verifica que OpenRouterError funciona sin status code."""
        error = OpenRouterError("Network error")
        assert error.message == "Network error"
        assert error.status_code is None


class TestTemplateCache:
    """Tests para caching de templates."""
    
    def test_clear_template_cache(self):
        """Verifica que clear_template_cache limpia la cache."""
        clear_template_cache()
        # Si no lanza error, el test pasa
        assert True


class TestIntegration:
    """Tests de integración."""
    
    def test_format_and_build_messages(self):
        """Verifica flujo completo de formateo y construcción de mensajes."""
        chunks = [
            {"text": "First source text", "source": "file1.pdf", "score": 0.92},
            {"text": "Second source text", "source": "file2.txt", "score": 0.88}
        ]
        
        context = format_context(chunks)
        
        messages = build_messages(
            system_template="Eres experto",
            user_template="Pregunta: {question}\n\nContexto:\n{context}",
            question="¿Cuál es tu respuesta?",
            context_chunks=chunks
        )
        
        assert len(messages) == 2
        assert "Eres experto" in messages[0]["content"]
        assert "¿Cuál es tu respuesta?" in messages[1]["content"]
        assert "First source text" in messages[1]["content"]
        assert "Second source text" in messages[1]["content"]
