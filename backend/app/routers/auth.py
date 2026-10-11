"""Simulated OTP authentication; no SMS or external identity provider is used."""

from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from ..config import settings
from ..authz import make_token
from ..db import get_db
from ..models import Lender, Merchant
from ..schemas import OTPRequest, OTPVerify
from .helpers import response

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/request-otp")
def request_otp(payload: OTPRequest) -> dict:
    return response(
        {
            "phone": payload.phone,
            "otp_requested": True,
            "demo_code": settings.demo_otp_code,
            "message": "A simulated OTP is ready for this prototype.",
        }
    )


@router.post("/verify-otp")
def verify_otp(payload: OTPVerify, db: Session = Depends(get_db)) -> dict:
    if payload.code != settings.demo_otp_code:
        raise HTTPException(status_code=401, detail="Invalid simulated OTP")
    merchant = db.query(Merchant).filter(Merchant.phone == payload.phone).first()
    if merchant is None:
        raise HTTPException(status_code=404, detail="Merchant is not seeded")
    token = make_token("merchant", payload.phone, merchant_id=merchant.id)
    return response({"verified": True, "session_token": token, "role": "merchant", "phone": payload.phone, "merchant_id": merchant.id})


@router.post("/lender/request-otp")
def request_lender_otp(payload: OTPRequest) -> dict:
    return response(
        {
            "phone": payload.phone,
            "otp_requested": True,
            "demo_code": settings.demo_otp_code,
            "role": "lender",
            "message": "A simulated lender OTP is ready for this prototype.",
        }
    )


@router.post("/lender/verify-otp")
def verify_lender_otp(payload: OTPVerify, db: Session = Depends(get_db)) -> dict:
    if payload.code != settings.demo_otp_code:
        raise HTTPException(status_code=401, detail="Invalid simulated OTP")
    lender = db.query(Lender).filter(Lender.phone == payload.phone).first()
    if lender is None:
        raise HTTPException(status_code=404, detail="Demo lender is not seeded")
    token = make_token("lender", payload.phone, lender_id=lender.id)
    return response({"verified": True, "session_token": token, "role": "lender", "phone": payload.phone, "lender_id": lender.id})
