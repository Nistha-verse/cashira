"""FastAPI application entry point."""

from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session

from .db import init_db
from .routers import auth, demo, health, lender, loan, merchant, records

app = FastAPI(
    title="Cashira API",
    description="Synthetic, advisory monthly EMI decision-support prototype.",
    version="0.2.0",
)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://127.0.0.1:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.exception_handler(HTTPException)
async def http_error(_: Request, exc: HTTPException) -> JSONResponse:
    code = "http_error" if not isinstance(exc.detail, str) else f"http_{exc.status_code}"
    return JSONResponse(status_code=exc.status_code, content={"prototype": True, "notice": "Prototype only: all data is synthetic and simulated; Cashira is an advisory decision-support layer, not a lender.", "error": {"code": code, "message": str(exc.detail)}})


@app.exception_handler(RequestValidationError)
async def validation_error(_: Request, exc: RequestValidationError) -> JSONResponse:
    return JSONResponse(status_code=422, content={"prototype": True, "notice": "Prototype only: all data is synthetic and simulated; Cashira is an advisory decision-support layer, not a lender.", "error": {"code": "validation_error", "message": "Request validation failed"}})


@app.exception_handler(Exception)
async def unhandled_error(_: Request, __: Exception) -> JSONResponse:
    return JSONResponse(status_code=500, content={"prototype": True, "notice": "Prototype only: all data is synthetic and simulated; Cashira is an advisory decision-support layer, not a lender.", "error": {"code": "internal_error", "message": "The backend could not complete this request."}})


@app.on_event("startup")
def startup() -> None:
    init_db()


app.include_router(auth.router)
app.include_router(merchant.router)
app.include_router(loan.router)
app.include_router(records.router)
app.include_router(lender.router)
app.include_router(demo.router)
app.include_router(health.router)
