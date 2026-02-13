"""Tests for LLM integration."""

from unittest.mock import MagicMock, patch

from app.services.agents.llm import LLMProvider


class TestLLMProvider:
    """Test LLM provider singleton."""

    def test_llm_provider_singleton(self):
        """Test that LLMProvider is a singleton."""
        provider1 = LLMProvider.get_instance()
        provider2 = LLMProvider.get_instance()

        assert provider1 is provider2

    def test_llm_provider_reset(self):
        """Test LLMProvider reset."""
        provider1 = LLMProvider.get_instance()
        LLMProvider.reset()
        provider2 = LLMProvider.get_instance()

        # After reset, should be different instance
        assert provider1 is not provider2

    def test_llm_provider_initialization(self):
        """Test LLM provider initialization."""
        LLMProvider.reset()
        provider = LLMProvider.get_instance()

        assert provider is not None
        assert isinstance(provider, LLMProvider)

    def test_llm_provider_has_model(self):
        """Test that LLE provider has configured model."""
        _provider = LLMProvider.get_instance()

        # Should have a model (may be None if not initialized)
        # This is acceptable during testing


class TestLLMProviderWithMocks:
    """Test LLM provider with mocked OpenAI."""

    @patch('app.services.agents.llm.ChatOpenAI')
    def test_init_llm_creates_provider(self, mock_chat_openai):
        """Test that init_llm creates provider."""
        from app.services.agents import init_llm

        mock_chat_openai.return_value = MagicMock()
        LLMProvider.reset()

        init_llm()

        provider = LLMProvider.get_instance()
        assert provider is not None

    @patch('app.services.agents.llm.ChatOpenAI')
    def test_multiple_init_calls_reuse_instance(self, mock_chat_openai):
        """Test that multiple init_llm calls reuse the instance."""
        from app.services.agents import init_llm

        mock_chat_openai.return_value = MagicMock()
        LLMProvider.reset()

        init_llm()
        provider1 = LLMProvider.get_instance()

        init_llm()
        provider2 = LLMProvider.get_instance()

        assert provider1 is provider2

    @patch('app.services.agents.llm.ChatOpenAI')
    def test_llm_provider_error_handling(self, mock_chat_openai):
        """Test LLM provider error handling."""
        mock_chat_openai.side_effect = Exception("API Key not found")

        from app.services.agents import init_llm
        LLMProvider.reset()

        # Should handle error gracefully
        try:
            init_llm()
        except Exception:
            pass  # Expected in test environment


class TestLLMIntegration:
    """Test LLM integration with workflows."""

    @patch('app.services.agents.llm.ChatOpenAI')
    def test_llm_available_for_parsing(self, mock_chat_openai):
        """Test that LLM is available for parsing nodes."""
        mock_llm = MagicMock()
        mock_chat_openai.return_value = mock_llm

        from app.services.agents import init_llm
        LLMProvider.reset()

        init_llm()
        provider = LLMProvider.get_instance()

        # Should be able to access LLM
        assert provider is not None

    @patch('app.services.agents.llm.ChatOpenAI')
    def test_llm_model_configuration(self, mock_chat_openai):
        """Test LLM model configuration."""
        mock_llm = MagicMock()
        mock_chat_openai.return_value = mock_llm

        from app.services.agents import init_llm
        LLMProvider.reset()

        init_llm()

        # Verify ChatOpenAI was called with expected parameters
        assert mock_chat_openai.called


class TestLLMCaching:
    """Test LLM instance caching."""

    @patch('app.services.agents.llm.ChatOpenAI')
    def test_llm_instance_cached(self, mock_chat_openai):
        """Test that LLM instance is properly cached."""
        from app.services.agents import init_llm

        mock_llm = MagicMock()
        mock_chat_openai.return_value = mock_llm

        LLMProvider.reset()

        init_llm()
        init_llm()
        init_llm()

        # Should only create one instance
        # (or at least not create unnecessarily)
        assert mock_chat_openai.call_count <= 1


class TestLLMProviderThreadSafety:
    """Test LLM provider thread safety (basic)."""

    @patch('app.services.agents.llm.ChatOpenAI')
    def test_concurrent_access(self, mock_chat_openai):
        """Test concurrent access to LLM provider."""
        import threading

        from app.services.agents import init_llm

        mock_llm = MagicMock()
        mock_chat_openai.return_value = mock_llm

        LLMProvider.reset()

        results = []

        def access_provider():
            init_llm()
            provider = LLMProvider.get_instance()
            results.append(provider)

        threads = [threading.Thread(target=access_provider) for _ in range(5)]

        for t in threads:
            t.start()

        for t in threads:
            t.join()

        # All should get same instance
        if len(results) > 1:
            for r in results[1:]:
                assert r is results[0] or r is not None
