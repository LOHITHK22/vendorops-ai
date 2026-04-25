from app.config.settings import Settings, get_settings


def test_settings_defaults_load() -> None:
    settings = get_settings()

    assert isinstance(settings, Settings)
    assert settings.app_name == "VendorOps AI"
    assert settings.api_prefix == "/v1"
    assert settings.database_url.startswith("sqlite+aiosqlite:///")

