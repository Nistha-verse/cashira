"""FastAPI application entry point."""

from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse

from .db import init_db
from .routers import auth, health, lender, loan, merchant, records

app = FastAPI(
    title="Cashira API",
    description="Synthetic, advisory monthly EMI decision-support prototype.",
    version="0.1.0",
)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.exception_handler(HTTPException)
async def http_error(_: Request, exc: HTTPException) -> JSONResponse:
    return JSONResponse(status_code=exc.status_code, content={"prototype": True, "notice": "Prototype only: all data is synthetic and simulated; Cashira is an advisory decision-support layer, not a lender.", "error": exc.detail})


@app.exception_handler(RequestValidationError)
async def validation_error(_: Request, exc: RequestValidationError) -> JSONResponse:
    return JSONResponse(status_code=422, content={"prototype": True, "notice": "Prototype only: all data is synthetic and simulated; Cashira is an advisory decision-support layer, not a lender.", "error": "Request validation failed", "details": exc.errors()})


@app.on_event("startup")
def startup() -> None:
    init_db()


app.include_router(auth.router)
app.include_router(merchant.router)
app.include_router(loan.router)
app.include_router(records.router)
app.include_router(lender.router)
app.include_router(health.router)
