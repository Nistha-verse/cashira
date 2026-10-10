"""Optional chain anchor boundary; disabled by default."""

from __future__ import annotations

from typing import Any

from sqlalchemy.orm import Session

from ..config import settings
from ..models import AuditRecord

ANCHOR_ABI = [
    {
        "inputs": [
            {"internalType": "string", "name": "loanRef", "type": "string"},
            {"internalType": "bytes32", "name": "recordHash", "type": "bytes32"},
            {"internalType": "string", "name": "ruleVersion", "type": "string"},
        ],
        "name": "anchor",
        "outputs": [],
        "stateMutability": "nonpayable",
        "type": "function",
    },
    {
        "inputs": [{"internalType": "bytes32", "name": "", "type": "bytes32"}],
        "name": "anchors",
        "outputs": [
            {"internalType": "string", "name": "loanRef", "type": "string"},
            {"internalType": "bytes32", "name": "recordHash", "type": "bytes32"},
            {"internalType": "string", "name": "ruleVersion", "type": "string"},
            {"internalType": "uint256", "name": "timestamp", "type": "uint256"},
        ],
        "stateMutability": "view",
        "type": "function",
    },
]


def anchor_record(loan_ref: str, record_hash: str, rule_version: str) -> dict[str, Any] | None:
    """Return an anchor receipt when enabled; never block the prototype.

    The concrete web3 implementation is added only in the optional final
    chain build. With the default flag this function is a no-op.
    """

    if not settings.chain_enabled:
        return None
    return None


def _web3_context() -> tuple[Any, Any, Any] | None:
    if not (settings.chain_enabled and settings.chain_rpc_url and settings.chain_contract_address and settings.chain_private_key):
        return None
    try:
        from web3 import Web3

        web3 = Web3(Web3.HTTPProvider(settings.chain_rpc_url))
        if not web3.is_connected():
            return None
        account = web3.eth.account.from_key(settings.chain_private_key)
        contract = web3.eth.contract(
            address=Web3.to_checksum_address(settings.chain_contract_address), abi=ANCHOR_ABI
        )
        return web3, account, contract
    except Exception:
        return None


def anchor_audit_record(db: Session, audit: AuditRecord) -> dict[str, Any] | None:
    """Best-effort write of only the audit hash; failure leaves the app usable."""

    context = _web3_context()
    if context is None:
        return None
    try:
        web3, account, contract = context
        record_hash = bytes.fromhex(audit.record_hash.removeprefix("0x"))
        nonce = web3.eth.get_transaction_count(account.address)
        transaction = contract.functions.anchor(
            str(audit.loan_id), record_hash, audit.rule_version
        ).build_transaction(
            {
                "from": account.address,
                "nonce": nonce,
                "chainId": web3.eth.chain_id,
                "gas": settings.chain_gas_limit,
                "gasPrice": web3.eth.gas_price,
            }
        )
        signed = account.sign_transaction(transaction)
        raw = getattr(signed, "raw_transaction", getattr(signed, "rawTransaction", None))
        tx_hash = web3.eth.send_raw_transaction(raw)
        receipt = web3.eth.wait_for_transaction_receipt(tx_hash)
        if receipt["status"] != 1:
            return None
        tx_hex = tx_hash.hex()
        audit.anchored_tx_hash = tx_hex
        db.flush()
        return {"tx_hash": tx_hex}
    except Exception:
        return None


def verify_anchor(audit: AuditRecord) -> bool | None:
    """Compare an existing anchor's stored values when the chain is reachable."""

    context = _web3_context()
    if context is None or not audit.anchored_tx_hash:
        return None
    try:
        web3, _, contract = context
        stored = contract.functions.anchors(bytes.fromhex(audit.record_hash.removeprefix("0x"))).call()
        return (
            stored[0] == str(audit.loan_id)
            and bytes(stored[1]).hex() == audit.record_hash.removeprefix("0x")
            and stored[2] == audit.rule_version
        )
    except Exception:
        return None
