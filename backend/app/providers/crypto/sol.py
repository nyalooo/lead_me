"""Solana crypto provider — COMING SOON.

This is a placeholder for future Solana integration.
When implemented, this will use solana-py or solders for:
- SOL transfers via Solana RPC
- SPL token support (for custom reward tokens)
- Solana Pay integration

Required packages (not yet added):
- solana>=0.34.0
- solders>=0.21.0

To activate:
1. Install dependencies
2. Set SOLANA_RPC_URL and SOLANA_WALLET_SEED in .env
3. Set CRYPTO_PROVIDER=sol or let auto-detect find it
"""

import logging

from app.providers.crypto.base import (
    CryptoProvider,
    TransferRequest,
    TransferResult,
    TransactionStatus,
)

logger = logging.getLogger(__name__)


class SolanaProvider(CryptoProvider):
    """Solana cryptocurrency provider (placeholder).

    Not yet implemented — raises NotImplementedError for all operations.
    """

    @property
    def name(self) -> str:
        return "sol"

    @property
    def currency_code(self) -> str:
        return "SOL"

    @property
    def network_name(self) -> str:
        return "solana-devnet"

    async def validate_address(self, address: str) -> bool:
        raise NotImplementedError("Solana provider coming soon")

    async def get_balance(self, address: str) -> float:
        raise NotImplementedError("Solana provider coming soon")

    async def transfer(self, request: TransferRequest) -> TransferResult:
        raise NotImplementedError("Solana provider coming soon")

    async def get_transaction(self, tx_hash: str) -> TransferResult | None:
        raise NotImplementedError("Solana provider coming soon")

    async def health_check(self) -> bool:
        return False  # not available yet

    async def get_min_transfer_amount(self) -> float:
        return 0.001
