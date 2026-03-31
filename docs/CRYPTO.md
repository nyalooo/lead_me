# Crypto Integration

LeadMe uses a multi-crypto adapter pattern for coin-to-cryptocurrency cashouts. XRP is the primary currency; Solana and Ethereum/Polygon are planned.

## Architecture

```
┌──────────────────┐     ┌─────────────────────────┐
│  Cashout Service │────▶│   CryptoProvider (ABC)   │
│  (business logic)│     │                         │
└──────────────────┘     │  validate_address()     │
                         │  get_balance()          │
                         │  transfer()             │
                         │  get_transaction()      │
                         │  health_check()         │
                         └────────┬────────────────┘
                                  │
                    ┌─────────────┼─────────────┐
                    │             │             │
              ┌─────┴─────┐ ┌────┴────┐  ┌─────┴─────┐
              │ XRPProvider│ │ Solana  │  │ Ethereum  │
              │ (active)   │ │ (soon)  │  │ (soon)    │
              └────────────┘ └─────────┘  └───────────┘
                    │
              ┌─────┴──────┐
              │MockProvider │
              │(dev/testing)│
              └────────────┘
```

## Supported Currencies

| Currency | Provider | Status | Network | Coins per Unit |
|----------|----------|--------|---------|---------------|
| XRP | XRPL | **Active** | Testnet / Mainnet | 10,000 |
| SOL | Solana | Coming Soon | Devnet | 5,000 |
| ETH | Ethereum/Polygon | Coming Soon | Polygon Amoy | 50,000 |
| MOCK | In-memory | Dev only | — | 10,000 |

## Provider Selection

Same pattern as routing and SMS providers:

1. **Explicit**: Set `CRYPTO_PROVIDER=xrp` in `.env`
2. **Auto-detect**: First provider with configured credentials wins
3. **Fallback**: Mock provider (no credentials needed)

```
CRYPTO_PROVIDER= (auto-detect) or xrp/sol/eth/mock
```

## Cashout Flow

```
User requests cashout (N coins → crypto)
  → Check eligibility:
    • Minimum 1,000 coins
    • Has linked wallet for chosen currency
    • 24h cooldown since last cashout
    • Currency is active (not "coming soon")
  → Calculate conversion:
    • base_amount = coins / conversion_rate
    • final_amount = base_amount × tier_bonus
  → Deduct coins from user balance
  → Record coin transaction (debit)
  → Execute crypto transfer via provider
  → On success: record tx_hash, explorer URL
  → On failure: refund coins automatically
```

## Tier Bonuses

Higher tiers earn more crypto per coin:

| Tier | Min Routes | Min Compliance | Cashout Bonus |
|------|-----------|---------------|---------------|
| Rookie | 0 | 0% | 1.0x |
| Regular | 25 | 70% | 1.1x (+10%) |
| Pro | 100 | 80% | 1.25x (+25%) |
| Legend | 500 | 90% | 1.5x (+50%) |

## Wallet Management

- Users link wallets per currency (one primary wallet per currency)
- **Non-custodial**: we never hold user private keys
- Address validation via the crypto provider
- Platform wallet (for sending rewards) configured via env vars

### Security

- Platform wallet seed is in environment variables, NEVER in code
- All cashouts are logged with full audit trail
- Failed transfers trigger automatic coin refunds
- 24-hour cooldown prevents abuse

## Adding a New Crypto Provider

1. Create `backend/app/providers/crypto/<name>.py`
2. Subclass `CryptoProvider` from `base.py`
3. Implement all abstract methods:
   - `validate_address(address)` → bool
   - `get_balance(address)` → float
   - `transfer(request)` → TransferResult
   - `get_transaction(tx_hash)` → TransferResult | None
   - `health_check()` → bool
   - `get_min_transfer_amount()` → float
4. Add to `registry.py` factory and auto-detect logic
5. Add config fields to `config.py`
6. Update conversion rate in settings

## Environment Variables

```bash
# Provider selection
CRYPTO_PROVIDER=       # xrp, sol, eth, mock, or empty (auto-detect)

# Platform wallet (for sending rewards)
PLATFORM_WALLET_ADDRESS=rXXXX...
PLATFORM_WALLET_SEED=sXXXX...       # KEEP SECRET

# XRP (XRPL)
XRPL_NETWORK_URL=wss://s.altnet.rippletest.net:51233
XRPL_WALLET_SEED=                    # XRP-specific seed

# Solana (coming soon)
SOLANA_RPC_URL=https://api.devnet.solana.com
SOLANA_WALLET_SEED=

# Ethereum / Polygon (coming soon)
ETH_RPC_URL=
ETH_WALLET_PRIVATE_KEY=
```

## API Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/v1/cashout/cryptos` | List supported cryptocurrencies |
| GET | `/api/v1/cashout/wallets` | List user's linked wallets |
| POST | `/api/v1/cashout/wallets` | Link a crypto wallet |
| DELETE | `/api/v1/cashout/wallets/{id}` | Remove a linked wallet |
| POST | `/api/v1/cashout/estimate` | Estimate cashout amount |
| POST | `/api/v1/cashout/cashout` | Execute cashout |
| GET | `/api/v1/cashout/history` | Cashout history |
