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
    here_api_key: str = ""

    # Routing provider: "google", "mapbox", "here", "mock", or "" (auto-detect)
    routing_provider: str = ""

    # SMS provider: "twilio", "msg91", "console", or "" (auto-detect)
    sms_provider: str = ""

    # Twilio
    twilio_account_sid: str = ""
    twilio_auth_token: str = ""
    twilio_phone_number: str = ""

    # MSG91
    msg91_auth_key: str = ""
    msg91_template_id: str = ""

    # Crypto provider: "xrp", "sol", "eth", "mock", or "" (auto-detect)
    crypto_provider: str = ""

    # Platform wallet (used to send rewards — NEVER expose seed publicly)
    platform_wallet_address: str = ""
    platform_wallet_seed: str = ""  # private key / seed for signing

    # XRP (XRPL)
    xrpl_network_url: str = "wss://s.altnet.rippletest.net:51233"  # testnet
    xrpl_wallet_seed: str = ""  # platform XRP wallet seed
    xrp_coins_per_xrp: int = 10000  # 10,000 Route Coins = 1 XRP

    # Solana (coming soon)
    solana_rpc_url: str = "https://api.devnet.solana.com"
    solana_wallet_seed: str = ""
    sol_coins_per_sol: int = 5000  # 5,000 Route Coins = 1 SOL

    # Ethereum / Polygon (coming soon)
    eth_rpc_url: str = ""
    eth_wallet_private_key: str = ""
    eth_coins_per_eth: int = 50000  # 50,000 Route Coins = 1 ETH

    # Referrals
    referral_bonus_referrer: int = 200  # coins for referrer when referred qualifies
    referral_bonus_referred: int = 100  # coins for new user on signup with code
    referral_qualify_routes: int = 3  # referred must complete N routes to qualify
    app_base_url: str = "https://leadme.app"  # for share URLs

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
