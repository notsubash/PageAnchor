from pageanchor.config import (
    DEFAULT_DEEPSEEK_BASE_URL,
    DEFAULT_GENERATOR_MODEL,
    DEFAULT_TEXT_EMBEDDING_MODEL,
    DEFAULT_VISUAL_RETRIEVE_MODEL,
    generator_client,
    load_settings,
)


def test_load_settings_reads_deepseek_env(monkeypatch):
    monkeypatch.setenv("DEEPSEEK_API_KEY", "sk-test")
    monkeypatch.setenv("DEEPSEEK_BASE_URL", "https://api.deepseek.com")
    monkeypatch.setenv("GENERATOR_MODEL", "deepseek-v4-flash")
    monkeypatch.setenv("TEXT_EMBEDDING_MODEL", "Qwen/Qwen3-Embedding-0.6B")
    monkeypatch.setenv("VISUAL_RETRIEVE_MODEL", "vidore/colqwen2-v1.0")
    monkeypatch.setenv("STRICT_VERIFY", "true")
    settings = load_settings()
    assert settings.deepseek_api_key == "sk-test"
    assert settings.deepseek_base_url == "https://api.deepseek.com"
    assert settings.generator_model == "deepseek-v4-flash"
    assert settings.text_embedding_model == "Qwen/Qwen3-Embedding-0.6B"
    assert settings.visual_retrieve_model == "vidore/colqwen2-v1.0"
    assert settings.strict_verify is True


def test_defaults_are_deepseek_and_retrieval_models():
    assert DEFAULT_DEEPSEEK_BASE_URL == "https://api.deepseek.com"
    assert DEFAULT_GENERATOR_MODEL == "deepseek-v4-flash"
    assert DEFAULT_TEXT_EMBEDDING_MODEL == "Qwen/Qwen3-Embedding-0.6B"
    assert DEFAULT_VISUAL_RETRIEVE_MODEL == "vidore/colqwen2-v1.0"


def test_generator_client_points_at_deepseek(monkeypatch):
    monkeypatch.setenv("DEEPSEEK_API_KEY", "sk-test")
    monkeypatch.setenv("DEEPSEEK_BASE_URL", "https://api.deepseek.com")
    client = generator_client()
    assert "api.deepseek.com" in str(client.base_url)
    assert client.api_key == "sk-test"
