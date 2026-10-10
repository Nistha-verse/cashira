"""Pydantic request models used by the HTTP API."""

from __future__ import annotations

from datetime import date
from decimal import Decimal

from pydantic import BaseModel, ConfigDict, Field


class OTPRequest(BaseModel):
    phone: str = Field(min_length=3, max_length=40)


class OTPVerify(BaseModel):
    phone: str = Field(min_length=3, max_length=40)
    code: str = Field(min_length=1, max_length=20)


class PaymentRequest(BaseModel):
    amount: Decimal | None = Field(default=None, gt=0)
    payment_date: date | None = None


class VerifyRequest(BaseModel):
    record_id: int | None = None
    record: dict | None = None
    hash: str | None = None
    signature: str | None = None


class ORMModel(BaseModel):
    model_config = ConfigDict(from_attributes=True)
