"""Application configuration via environment variables."""

from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """App settings loaded from environment variables or .env file."""

    # App
    app_name: str = "LeadMe"
    debug: bool = False
    api_v1_prefix: str = "/api/v1"

    # Database
    database_url: str = "postgresql+asyncpg://postgres:postgres@localhost:5432/leadme"
    redis_url: str = "redis://localhost:6379/0"

    # Auth
    jwt_secret_key: str = "change-me-in-production"
    jwt_algorithm: str = "HS256"
    jwt_expire_minutes: int = 60 * 24 * 7  # 7 days
    otp_expire_seconds: int = 300  # 5 minutes

    # External APIs
    google_routes_api_key: str = ""
    mapbox_access_token: str = ""

    # XRP
    xrpl_network_url: str = "wss://s.altnet.rippletest.net:51233"  # testnet
    xrp_coins_per_xrp: int = 10000  # 10,000 Route Coins = 1 XRP

    # Route Engine
    max_detour_percent: float = 15.0  # never assign route >15% longer
    max_alternative_routes: int = 3

    # Mumbai bounding box (for validation)
    mumbai_lat_min: float = 18.89
    mumbai_lat_max: float = 19.27
    mumbai_lng_min: float = 72.77
    mumbai_lng_max: float = 72.98

    model_config = {"env_file": ".env", "env_file_encoding": "utf-8"}


settings = Settings()
