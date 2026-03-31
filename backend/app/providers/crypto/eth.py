"""Ethereum / Polygon crypto provider — COMING SOON.

This is a placeholder for future Ethereum/Polygon integration.
When implemented, this will use web3.py for:
- ETH/MATIC transfers
- ERC-20 token support (for custom reward tokens)
- Polygon (low-fee L2) as default network

Required packages (not yet added):
- web3>=7.0.0

To activate:
1. Install dependencies
2. Set ETH_RPC_URL and ETH_WALLET_PRIVATE_KEY in .env
3. Set CRYPTO_PROVIDER=eth or let auto-detect find it
"""

import logging

from app.providers.crypto.base import (
    CryptoProvider,
    TransferRequest,
    TransferResult,
    TransactionStatus,
)

logger = logging.getLogger(__name__)


class EthereumProvider(CryptoProvider):
    """Ethereum/Polygon cryptocurrency provider (placeholder).

    Not yet implemented — raises NotImplementedError for all operations.
    """

    @property
    def name(self) -> str:
        return "eth"

    @property
    def currency_code(self) -> str:
        return "ETH"

    @property
    def network_name(self) -> str:
        return "polygon-amoy"  # testnet

    async def validate_address(self, address: str) -> bool:
        raise NotImplementedError("Ethereum provider coming soon")

    async def get_balance(self, address: str) -> float:
        raise NotImplementedError("Ethereum provider coming soon")

    async def transfer(self, request: TransferRequest) -> TransferResult:
        raise NotImplementedError("Ethereum provider coming soon")

    async def get_transaction(self, tx_hash: str) -> TransferResult | None:
        raise NotImplementedError("Ethereum provider coming soon")

    async def health_check(self) -> bool:
        return False  # not available yet

    async def get_min_transfer_amount(self) -> float:
        return 0.0001
