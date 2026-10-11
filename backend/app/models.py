"""Database models for merchants, monthly loans, payments, and audit records."""

from __future__ import annotations

from datetime import date, datetime
from decimal import Decimal

from sqlalchemy import Boolean, Date, DateTime, ForeignKey, Integer, Numeric, String, Text, UniqueConstraint
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship


class Base(DeclarativeBase):
    pass


class Merchant(Base):
    __tablename__ = "merchants"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    name: Mapped[str] = mapped_column(String(120), nullable=False)
    phone: Mapped[str] = mapped_column(String(40), nullable=False, unique=True)
    business_type: Mapped[str] = mapped_column(String(80), default="kirana store")
    city: Mapped[str] = mapped_column(String(80), default="Bengaluru")
    consented_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    preferred_language: Mapped[str] = mapped_column(String(5), default="en", nullable=False)
    scenario: Mapped[str] = mapped_column(String(60), default="stable", nullable=False)

    records: Mapped[list["Transaction"]] = relationship(
        back_populates="merchant", cascade="all, delete-orphan"
    )
    loans: Mapped[list["Loan"]] = relationship(
        back_populates="merchant", cascade="all, delete-orphan"
    )


class Transaction(Base):
    __tablename__ = "transactions"
    __table_args__ = (
        UniqueConstraint(
            "merchant_id", "transaction_date", "direction", "category", "amount",
            name="uq_transaction_record"
        ),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    merchant_id: Mapped[int] = mapped_column(ForeignKey("merchants.id"), nullable=False, index=True)
    transaction_date: Mapped[date] = mapped_column(Date, nullable=False, index=True)
    direction: Mapped[str] = mapped_column(String(16), nullable=False)
    category: Mapped[str] = mapped_column(String(80), nullable=False)
    amount: Mapped[Decimal] = mapped_column(Numeric(14, 2), nullable=False)
    description: Mapped[str] = mapped_column(String(200), default="Synthetic record")

    merchant: Mapped[Merchant] = relationship(back_populates="records")


class Loan(Base):
    __tablename__ = "loans"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    merchant_id: Mapped[int] = mapped_column(ForeignKey("merchants.id"), nullable=False, unique=True)
    principal: Mapped[Decimal] = mapped_column(Numeric(14, 2), nullable=False)
    annual_rate: Mapped[Decimal] = mapped_column(Numeric(7, 4), nullable=False)
    tenure_months: Mapped[int] = mapped_column(Integer, nullable=False)
    min_emi: Mapped[Decimal] = mapped_column(Numeric(14, 2), nullable=False)
    max_emi: Mapped[Decimal] = mapped_column(Numeric(14, 2), nullable=False)
    standard_emi: Mapped[Decimal] = mapped_column(Numeric(14, 2), nullable=False)
    due_day: Mapped[int] = mapped_column(Integer, default=5, nullable=False)
    current_balance: Mapped[Decimal] = mapped_column(Numeric(14, 2), nullable=False)
    carried_shortfall: Mapped[Decimal] = mapped_column(Numeric(14, 2), default=Decimal("0.00"), nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    merchant: Mapped[Merchant] = relationship(back_populates="loans")
    payments: Mapped[list["Payment"]] = relationship(
        back_populates="loan", cascade="all, delete-orphan", order_by="Payment.id"
    )
    recommendations: Mapped[list["Recommendation"]] = relationship(
        back_populates="loan", cascade="all, delete-orphan", order_by="Recommendation.id"
    )


class Recommendation(Base):
    __tablename__ = "recommendations"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    loan_id: Mapped[int] = mapped_column(ForeignKey("loans.id"), nullable=False, index=True)
    emi: Mapped[Decimal] = mapped_column(Numeric(14, 2), nullable=False)
    reasons_json: Mapped[str] = mapped_column(Text, nullable=False)
    explanation: Mapped[str] = mapped_column(Text, nullable=False)
    forecast_method: Mapped[str] = mapped_column(String(40), nullable=False)
    rule_version: Mapped[str] = mapped_column(String(40), nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    loan: Mapped[Loan] = relationship(back_populates="recommendations")


class Payment(Base):
    __tablename__ = "payments"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    loan_id: Mapped[int] = mapped_column(ForeignKey("loans.id"), nullable=False, index=True)
    amount: Mapped[Decimal] = mapped_column(Numeric(14, 2), nullable=False)
    payment_date: Mapped[date] = mapped_column(Date, nullable=False)
    interest_component: Mapped[Decimal] = mapped_column(Numeric(14, 2), nullable=False)
    principal_component: Mapped[Decimal] = mapped_column(Numeric(14, 2), nullable=False)
    balance_after: Mapped[Decimal] = mapped_column(Numeric(14, 2), nullable=False)
    carried_shortfall_after: Mapped[Decimal] = mapped_column(Numeric(14, 2), nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    due_date: Mapped[date | None] = mapped_column(Date, nullable=True)
    status: Mapped[str] = mapped_column(String(20), default="paid", nullable=False)
    days_late: Mapped[int] = mapped_column(Integer, default=0, nullable=False)

    loan: Mapped[Loan] = relationship(back_populates="payments")


class AuditRecord(Base):
    __tablename__ = "audit_records"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    loan_id: Mapped[int] = mapped_column(ForeignKey("loans.id"), nullable=False, index=True)
    record_type: Mapped[str] = mapped_column(String(30), nullable=False)
    record_json: Mapped[str] = mapped_column(Text, nullable=False)
    record_hash: Mapped[str] = mapped_column(String(128), nullable=False, unique=True)
    signature: Mapped[str] = mapped_column(Text, nullable=False)
    prev_hash: Mapped[str | None] = mapped_column(String(128), nullable=True)
    rule_version: Mapped[str] = mapped_column(String(40), nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    anchored_tx_hash: Mapped[str | None] = mapped_column(String(128), nullable=True)


class Lender(Base):
    __tablename__ = "lenders"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    name: Mapped[str] = mapped_column(String(120), nullable=False)
    phone: Mapped[str] = mapped_column(String(40), nullable=False, unique=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    portfolio: Mapped[list["LenderPortfolio"]] = relationship(
        back_populates="lender", cascade="all, delete-orphan"
    )


class LenderPortfolio(Base):
    __tablename__ = "lender_portfolio"
    __table_args__ = (UniqueConstraint("lender_id", "merchant_id", name="uq_lender_merchant"),)

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    lender_id: Mapped[int] = mapped_column(ForeignKey("lenders.id"), nullable=False, index=True)
    merchant_id: Mapped[int] = mapped_column(ForeignKey("merchants.id"), nullable=False, index=True)

    lender: Mapped[Lender] = relationship(back_populates="portfolio")
    merchant: Mapped[Merchant] = relationship()


class Consent(Base):
    __tablename__ = "consents"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    merchant_id: Mapped[int] = mapped_column(ForeignKey("merchants.id"), nullable=False, index=True)
    scope: Mapped[str] = mapped_column(String(80), default="transaction history", nullable=False)
    granted_at: Mapped[datetime] = mapped_column(DateTime, nullable=False)
    expires_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    revoked_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    status: Mapped[str] = mapped_column(String(20), default="active", nullable=False)

    merchant: Mapped[Merchant] = relationship()


class Alert(Base):
    __tablename__ = "alerts"
    __table_args__ = (
        UniqueConstraint("merchant_id", "signal_id", "week_key", name="uq_alert_signal_week"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    merchant_id: Mapped[int] = mapped_column(ForeignKey("merchants.id"), nullable=False, index=True)
    signal_id: Mapped[str] = mapped_column(String(10), nullable=False)
    severity: Mapped[str] = mapped_column(String(10), nullable=False)
    week_key: Mapped[str] = mapped_column(String(20), nullable=False)
    status: Mapped[str] = mapped_column(String(20), default="new", nullable=False)
    message_key: Mapped[str] = mapped_column(String(120), nullable=False)
    params_json: Mapped[str] = mapped_column(Text, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    rule_version: Mapped[str] = mapped_column(String(40), nullable=False)
    action_id: Mapped[int | None] = mapped_column(ForeignKey("lender_actions.id"), nullable=True)

    merchant: Mapped[Merchant] = relationship()


class LenderAction(Base):
    __tablename__ = "lender_actions"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    lender_id: Mapped[int] = mapped_column(ForeignKey("lenders.id"), nullable=False, index=True)
    merchant_id: Mapped[int] = mapped_column(ForeignKey("merchants.id"), nullable=False, index=True)
    action_type: Mapped[str] = mapped_column(String(20), nullable=False)
    note: Mapped[str] = mapped_column(Text, default="", nullable=False)
    alert_id: Mapped[int | None] = mapped_column(ForeignKey("alerts.id"), nullable=True)
    language: Mapped[str] = mapped_column(String(5), default="en", nullable=False)
    message_key: Mapped[str | None] = mapped_column(String(120), nullable=True)
    message_params_json: Mapped[str] = mapped_column(Text, default="{}", nullable=False)
    message_text: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    lender: Mapped[Lender] = relationship()
    merchant: Mapped[Merchant] = relationship()
    alert: Mapped[Alert | None] = relationship(foreign_keys=[alert_id])
