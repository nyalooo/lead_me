"""Abstract base for cryptocurrency providers.

Any crypto provider (XRP, SOL, ETH, etc.) must implement this interface.
The cashout service depends only on this abstraction, never on a concrete provider.

To add a new crypto provider:
1. Create a new file (e.g., sol.py) in this directory
2. Subclass CryptoProvider
3. Implement all abstract methods
4. Register it in the factory (registry.py)

Architecture:
    CryptoProvider (abstract)
    ├── XRPProvider        — XRPL (testnet/mainnet)
    ├── MockCryptoProvider  — In-memory ledger (dev/testing)
    ├── SolanaProvider      — Solana (coming soon)
    └── EthereumProvider    — Ethereum/Polygon (coming soon)
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum


class TransactionStatus(str, Enum):
    PENDING = "pending"
    CONFIRMED = "confirmed"
    FAILED = "failed"


@dataclass
class WalletInfo:
    """Wallet information returned by the provider."""
    address: str
    currency: str  # "XRP", "SOL", "ETH"
    network: str  # "xrpl-testnet", "solana-devnet", etc.
    balance: float = 0.0
    is_activated: bool = True  # some chains require minimum balance


@dataclass
class TransferResult:
    """Result of a crypto transfer."""
    tx_hash: str
    status: TransactionStatus
    amount: float
    currency: str
    from_address: str
    to_address: str
    fee: float = 0.0
    timestamp: datetime | None = None
    explorer_url: str | None = None  # link to block explorer
    raw_response: dict = field(default_factory=dict)


@dataclass
class TransferRequest:
    """Standardized input for crypto transfers."""
    from_address: str
    from_seed: str  # private key / seed (platform wallet)
    to_address: str
    amount: float
    memo: str | None = None  # optional on-chain memo


class CryptoProvider(ABC):
    """Abstract interface for cryptocurrency providers.

    Implement this to add support for a new blockchain/cryptocurrency.
    Each provider handles wallet operations and transfers for one currency.
    """

    @property
    @abstractmethod
    def name(self) -> str:
        """Provider identifier (e.g., 'xrp', 'sol', 'eth')."""
        ...

    @property
    @abstractmethod
    def currency_code(self) -> str:
        """ISO-style currency code (e.g., 'XRP', 'SOL', 'ETH')."""
        ...

    @property
    @abstractmethod
    def network_name(self) -> str:
        """Network identifier (e.g., 'xrpl-mainnet', 'solana-devnet')."""
        ...

    @abstractmethod
    async def validate_address(self, address: str) -> bool:
        """Validate that an address is well-formed for this chain.

        Does NOT check if the account exists or is funded —
        only validates format/checksum.
        """
        ...

    @abstractmethod
    async def get_balance(self, address: str) -> float:
        """Get the current balance of an address.

        Returns balance in the native currency unit (e.g., XRP, not drops).
        """
        ...

    @abstractmethod
    async def transfer(self, request: TransferRequest) -> TransferResult:
        """Execute a transfer from the platform wallet to a user wallet.

        The from_seed is the platform's signing credential.
        Implementations must handle gas/fee estimation internally.
        """
        ...

    @abstractmethod
    async def get_transaction(self, tx_hash: str) -> TransferResult | None:
        """Look up a transaction by hash.

        Returns None if the transaction is not found.
        """
        ...

    @abstractmethod
    async def health_check(self) -> bool:
        """Check if the blockchain node/API is reachable.

        Used for monitoring and automatic failover.
        """
        ...

    @abstractmethod
    async def get_min_transfer_amount(self) -> float:
        """Minimum transfer amount for this chain (e.g., XRP reserve)."""
        ...
