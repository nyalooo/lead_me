"""Mock crypto provider for development and testing.

Simulates blockchain operations with an in-memory ledger.
No real transactions occur — perfect for local development.
"""

import uuid
import logging
from datetime import datetime, timezone

from app.providers.crypto.base import (
    CryptoProvider,
    TransferRequest,
    TransferResult,
    TransactionStatus,
)

logger = logging.getLogger(__name__)

# In-memory ledger for mock transactions
_mock_balances: dict[str, float] = {}
_mock_transactions: dict[str, TransferResult] = {}


class MockCryptoProvider(CryptoProvider):
    """Mock cryptocurrency provider for dev/testing.

    Simulates transfers with an in-memory ledger.
    All addresses are valid, all transfers succeed.
    Platform wallet starts with 1,000,000 units.
    """

    INITIAL_BALANCE = 1_000_000.0

    @property
    def name(self) -> str:
        return "mock"

    @property
    def currency_code(self) -> str:
        return "MOCK"

    @property
    def network_name(self) -> str:
        return "mock-devnet"

    async def validate_address(self, address: str) -> bool:
        """Any non-empty string is a valid mock address."""
        return bool(address) and len(address) >= 5

    async def get_balance(self, address: str) -> float:
        """Get mock balance (starts at INITIAL_BALANCE for new addresses)."""
        if address not in _mock_balances:
            _mock_balances[address] = self.INITIAL_BALANCE
        return _mock_balances[address]

    async def transfer(self, request: TransferRequest) -> TransferResult:
        """Simulate a crypto transfer."""
        # Initialize balances if needed
        if request.from_address not in _mock_balances:
            _mock_balances[request.from_address] = self.INITIAL_BALANCE
        if request.to_address not in _mock_balances:
            _mock_balances[request.to_address] = 0.0

        # Check sufficient balance
        if _mock_balances[request.from_address] < request.amount:
            return TransferResult(
                tx_hash="",
                status=TransactionStatus.FAILED,
                amount=request.amount,
                currency=self.currency_code,
                from_address=request.from_address,
                to_address=request.to_address,
            )

        # Execute mock transfer
        _mock_balances[request.from_address] -= request.amount
        _mock_balances[request.to_address] += request.amount

        tx_hash = f"mock_{uuid.uuid4().hex[:16]}"
        result = TransferResult(
            tx_hash=tx_hash,
            status=TransactionStatus.CONFIRMED,
            amount=request.amount,
            currency=self.currency_code,
            from_address=request.from_address,
            to_address=request.to_address,
            fee=0.0,
            timestamp=datetime.now(timezone.utc),
            explorer_url=None,
        )
        _mock_transactions[tx_hash] = result

        logger.info(
            f"[MOCK CRYPTO] Transfer: {request.amount} {self.currency_code} "
            f"from {request.from_address[:10]}... to {request.to_address[:10]}... "
            f"(tx: {tx_hash})"
        )
        return result

    async def get_transaction(self, tx_hash: str) -> TransferResult | None:
        """Look up a mock transaction."""
        return _mock_transactions.get(tx_hash)

    async def health_check(self) -> bool:
        """Mock provider is always healthy."""
        return True

    async def get_min_transfer_amount(self) -> float:
        return 0.001
