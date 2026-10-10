"""Simulated OTP authentication; no SMS or external identity provider is used."""

from __future__ import annotations

import hashlib

from fastapi import APIRouter, HTTPException

from ..config import settings
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
def verify_otp(payload: OTPVerify) -> dict:
    if payload.code != settings.demo_otp_code:
        raise HTTPException(status_code=401, detail="Invalid simulated OTP")
    token = hashlib.sha256(f"cashira-demo:{payload.phone}:{payload.code}".encode()).hexdigest()
    return response({"verified": True, "session_token": token, "phone": payload.phone})
