import pytest


@pytest.fixture(autouse=True)
def _env(monkeypatch):
    """Ambiente fictício: nenhum teste toca a nuvem."""
    monkeypatch.setenv("GCP_PROJECT_ID", "proj-teste")
    monkeypatch.setenv("BRONZE_BUCKET", "bucket-teste")
    monkeypatch.setenv("BQ_LOCATION", "US")
    from alfab import config

    config.settings.cache_clear()
    yield
    config.settings.cache_clear()
