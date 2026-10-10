"""Environment-backed settings for the Cashira prototype."""

from __future__ import annotations

import os
from pathlib import Path

from dotenv import load_dotenv

BASE_DIR = Path(__file__).resolve().parents[1]
load_dotenv(BASE_DIR / ".env")


class Settings:
    app_name: str = "Cashira API"
    demo_otp_code: str = os.getenv("DEMO_OTP_CODE", "123456")
    signing_key: str = os.getenv(
        "SIGNING_KEY",
        "0x4f3edf983ac636a65a842ce7c78d9aa706d3b113bce036f9e2a3e7a7e6a0c8d1",
    )
    database_url: str = os.getenv(
        "DATABASE_URL", f"sqlite:///{BASE_DIR / 'data' / 'cashira.db'}"
    )
    chain_enabled: bool = os.getenv("CHAIN_ENABLED", "false").lower() == "true"
    chain_rpc_url: str = os.getenv("CHAIN_RPC_URL", "")
    chain_contract_address: str = os.getenv("CHAIN_CONTRACT_ADDRESS", "")
    chain_private_key: str = os.getenv("CHAIN_PRIVATE_KEY", "")
    chain_gas_limit: int = int(os.getenv("CHAIN_GAS_LIMIT", "300000"))
    use_prophet: bool = os.getenv("USE_PROPHET", "false").lower() == "true"


settings = Settings()
PROTOTYPE_NOTICE = (
    "Prototype only: all data is synthetic and simulated; Cashira is an advisory "
    "decision-support layer, not a lender."
)
AMORTIZATION_NOTICE = (
    "Prototype assumption: fixed-rate amortization is used; any shortfall versus "
    "the standard monthly EMI carries forward and does not reduce the total owed."
)
