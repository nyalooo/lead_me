"""XRP Ledger (XRPL) crypto provider.

Supports both testnet and mainnet via configurable network URL.
Uses xrpl-py for all XRPL interactions.

Testnet faucet: https://xrpl.org/xrp-testnet-faucet.html
Explorer: https://testnet.xrpl.org/ (testnet) / https://xrpl.org/ (mainnet)
"""

import logging
from datetime import datetime, timezone

from app.config import settings
from app.providers.crypto.base import (
    CryptoProvider,
    TransferRequest,
    TransferResult,
    TransactionStatus,
)

logger = logging.getLogger(__name__)


class XRPProvider(CryptoProvider):
    """XRPL cryptocurrency provider.

    Connects to XRPL testnet or mainnet via WebSocket.
    All amounts are in XRP (converted to/from drops internally).
    1 XRP = 1,000,000 drops.
    """

    DROPS_PER_XRP = 1_000_000
    MIN_RESERVE = 10.0  # XRP account reserve (10 XRP on mainnet)
    TRANSFER_FEE = 0.000012  # typical XRPL fee in XRP

    @property
    def name(self) -> str:
        return "xrp"

    @property
    def currency_code(self) -> str:
        return "XRP"

    @property
    def network_name(self) -> str:
        url = settings.xrpl_network_url
        if "testnet" in url or "altnet" in url:
            return "xrpl-testnet"
        elif "devnet" in url:
            return "xrpl-devnet"
        return "xrpl-mainnet"

    def _get_explorer_url(self, tx_hash: str) -> str:
        if "testnet" in self.network_name or "devnet" in self.network_name:
            return f"https://testnet.xrpl.org/transactions/{tx_hash}"
        return f"https://xrpl.org/transactions/{tx_hash}"

    async def validate_address(self, address: str) -> bool:
        """Validate an XRPL address (starts with 'r', base58 encoded)."""
        try:
            from xrpl.core.addresscodec import is_valid_classic_address
            return is_valid_classic_address(address)
        except ImportError:
            logger.warning("xrpl-py not installed — using basic validation")
            return address.startswith("r") and 25 <= len(address) <= 35
        except Exception:
            return False

    async def get_balance(self, address: str) -> float:
        """Get XRP balance for an address."""
        try:
            from xrpl.asyncio.clients import AsyncWebsocketClient
            from xrpl.models.requests import AccountInfo

            async with AsyncWebsocketClient(settings.xrpl_network_url) as client:
                response = await client.request(
                    AccountInfo(account=address, ledger_index="validated")
                )
                if response.is_successful():
                    balance_drops = int(response.result["account_data"]["Balance"])
                    return balance_drops / self.DROPS_PER_XRP
                else:
                    logger.error(f"XRPL balance check failed: {response.result}")
                    return 0.0
        except ImportError:
            logger.error("xrpl-py not installed — cannot check balance")
            return 0.0
        except Exception as e:
            logger.error(f"XRPL balance check error: {e}")
            return 0.0

    async def transfer(self, request: TransferRequest) -> TransferResult:
        """Send XRP from platform wallet to user wallet."""
        try:
            from xrpl.asyncio.clients import AsyncWebsocketClient
            from xrpl.asyncio.transaction import submit_and_wait
            from xrpl.models.transactions import Payment
            from xrpl.wallet import Wallet
            from xrpl.utils import xrp_to_drops

            wallet = Wallet.from_seed(request.from_seed)
            amount_drops = xrp_to_drops(request.amount)

            payment = Payment(
                account=wallet.address,
                amount=amount_drops,
                destination=request.to_address,
            )

            # Add memo if provided
            if request.memo:
                from xrpl.models.transactions import Memo
                memo_data = request.memo.encode("utf-8").hex()
                payment.memos = [Memo(memo_data=memo_data, memo_type="746578742f706c61696e")]

            async with AsyncWebsocketClient(settings.xrpl_network_url) as client:
                response = await submit_and_wait(payment, client, wallet)

                if response.is_successful():
                    tx_hash = response.result.get("hash", "")
                    return TransferResult(
                        tx_hash=tx_hash,
                        status=TransactionStatus.CONFIRMED,
                        amount=request.amount,
                        currency="XRP",
                        from_address=wallet.address,
                        to_address=request.to_address,
                        fee=self.TRANSFER_FEE,
                        timestamp=datetime.now(timezone.utc),
                        explorer_url=self._get_explorer_url(tx_hash),
                        raw_response=response.result,
                    )
                else:
                    logger.error(f"XRPL payment failed: {response.result}")
                    return TransferResult(
                        tx_hash="",
                        status=TransactionStatus.FAILED,
                        amount=request.amount,
                        currency="XRP",
                        from_address=wallet.address,
                        to_address=request.to_address,
                        raw_response=response.result,
                    )

        except ImportError:
            logger.error("xrpl-py not installed — cannot transfer")
            return TransferResult(
                tx_hash="",
                status=TransactionStatus.FAILED,
                amount=request.amount,
                currency="XRP",
                from_address=request.from_address,
                to_address=request.to_address,
            )
        except Exception as e:
            logger.error(f"XRPL transfer error: {e}")
            return TransferResult(
                tx_hash="",
                status=TransactionStatus.FAILED,
                amount=request.amount,
                currency="XRP",
                from_address=request.from_address,
                to_address=request.to_address,
            )

    async def get_transaction(self, tx_hash: str) -> TransferResult | None:
        """Look up a transaction on XRPL."""
        try:
            from xrpl.asyncio.clients import AsyncWebsocketClient
            from xrpl.models.requests import Tx

            async with AsyncWebsocketClient(settings.xrpl_network_url) as client:
                response = await client.request(Tx(transaction=tx_hash))
                if response.is_successful():
                    result = response.result
                    validated = result.get("validated", False)
                    amount_drops = int(result.get("Amount", 0)) if isinstance(result.get("Amount"), str) else 0

                    return TransferResult(
                        tx_hash=tx_hash,
                        status=TransactionStatus.CONFIRMED if validated else TransactionStatus.PENDING,
                        amount=amount_drops / self.DROPS_PER_XRP,
                        currency="XRP",
                        from_address=result.get("Account", ""),
                        to_address=result.get("Destination", ""),
                        fee=int(result.get("Fee", 0)) / self.DROPS_PER_XRP,
                        explorer_url=self._get_explorer_url(tx_hash),
                        raw_response=result,
                    )
                return None
        except ImportError:
            logger.error("xrpl-py not installed")
            return None
        except Exception as e:
            logger.error(f"XRPL tx lookup error: {e}")
            return None

    async def health_check(self) -> bool:
        """Check if XRPL node is reachable."""
        try:
            from xrpl.asyncio.clients import AsyncWebsocketClient
            from xrpl.models.requests import ServerInfo

            async with AsyncWebsocketClient(settings.xrpl_network_url) as client:
                response = await client.request(ServerInfo())
                return response.is_successful()
        except ImportError:
            logger.warning("xrpl-py not installed — health check skipped")
            return False
        except Exception as e:
            logger.error(f"XRPL health check failed: {e}")
            return False

    async def get_min_transfer_amount(self) -> float:
        """XRPL minimum is the account reserve (10 XRP for new accounts)."""
        return 0.001  # min payment amount, not reserve
