from api.storage import connect
import os
import sqlite3
from pathlib import Path
from contextlib import closing

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field
from fastapi.middleware.cors import CORSMiddleware
from starlette.middleware.trustedhost import TrustedHostMiddleware
from starlette.responses import JSONResponse
from api.privacy import disconnect_local, delete_imported

from api.imported_home import DATABASE, imported_home
from api.categories import set_category
from api.csv_import import preview, confirm
from api.budgets import save_budget
from api.banking import simulated_import
from api.planned_payments import save_payment

app = FastAPI(title="Ahorra+ DEMO", version="0.1.0")
allowed_origins = os.getenv(
    "AHORRA_WEB_ORIGINS",
    "http://localhost:8081,http://127.0.0.1:8081,http://localhost:8082,http://127.0.0.1:8082",
).split(",")
app.add_middleware(TrustedHostMiddleware, allowed_hosts=["localhost", "127.0.0.1"])


@app.middleware("http")
async def local_access(request, call_next):
    origin = request.headers.get("origin")
    if not request.client or request.client.host not in ("127.0.0.1", "::1"):
        return JSONResponse({"detail": "Acceso local requerido"}, status_code=403)
    if origin and origin not in allowed_origins:
        return JSONResponse({"detail": "Origen no autorizado"}, status_code=403)
    if request.method not in ("GET", "HEAD", "OPTIONS") and origin not in allowed_origins:
        return JSONResponse({"detail": "Abre la aplicación local para realizar cambios"}, status_code=403)
    response = await call_next(request)
    response.headers["Cache-Control"] = "no-store"
    response.headers["X-Content-Type-Options"] = "nosniff"
    return response
app.add_middleware(
    CORSMiddleware,
    allow_origins=os.getenv(
        "AHORRA_WEB_ORIGINS",
        "http://localhost:8081,http://127.0.0.1:8081,"
        "http://localhost:8082,http://127.0.0.1:8082"
    ).split(","),
    allow_methods=["GET", "POST"],
    allow_headers=["Content-Type"],
)


@app.get("/api/v1/demo/home")
def home():
    return imported_home()


@app.get("/api/v1/demo/bank-simulation")
def bank_simulation():
    return simulated_import()


@app.post("/api/v1/demo/privacy/disconnect")
def disconnect():
    disconnect_local(DATABASE)
    return {"message": "Autorización y claves locales de prueba eliminadas. Modo simulación."}


class DeleteRequest(BaseModel):
    confirmation: str


@app.post("/api/v1/demo/privacy/delete-imported")
def erase_imported(payload: DeleteRequest):
    try:
        delete_imported(DATABASE, payload.confirmation)
    except ValueError as error:
        raise HTTPException(422, str(error)) from error
    return {"deleted": True}


class ImportRequest(BaseModel):
    content: str = Field(min_length=1, max_length=500000)


class PaymentRequest(BaseModel):
    id: str = Field(min_length=1, max_length=100)
    name: str
    date: str
    cents: int = Field(strict=True, gt=0, le=100000000)
    kind: str


@app.post("/api/v1/demo/payments")
def update_payment(payload: PaymentRequest):
    try:
        save_payment(DATABASE, payload.id, payload.name, payload.date, payload.cents, payload.kind)
    except ValueError as error:
        raise HTTPException(422, str(error)) from error
    return {"saved": True}


class CategoryRequest(BaseModel):
    movement_id: str = Field(min_length=1)
    category: str


class BudgetRequest(BaseModel):
    month: str
    category: str
    limit_cents: int = Field(strict=True, ge=0, le=100000000)


@app.post("/api/v1/demo/budgets")
def update_budget(payload: BudgetRequest):
    try:
        save_budget(DATABASE, payload.month, payload.category, payload.limit_cents)
    except ValueError as error:
        raise HTTPException(422, str(error)) from error
    return {"saved": True}


@app.post("/api/v1/demo/movements/category")
def update_category(payload: CategoryRequest):
    try:
        set_category(DATABASE, payload.movement_id, payload.category)
    except LookupError as error:
        raise HTTPException(404, str(error)) from error
    except ValueError as error:
        raise HTTPException(422, str(error)) from error
    return {"category": payload.category}


@app.post("/api/v1/demo/import/preview")
def preview_import(payload: ImportRequest):
    try:
        rows, errors = preview(payload.content)
    except ValueError as error:
        raise HTTPException(422, str(error)) from error
    return {"rows": rows, "errors": errors}


@app.post("/api/v1/demo/import/confirm")
def confirm_import(payload: ImportRequest):
    database = Path(__file__).resolve().parents[1] / "demo-import.sqlite3"
    try:
        with closing(connect(database)) as connection:
            inserted = confirm(connection, "demo", payload.content)
    except ValueError as error:
        raise HTTPException(409, str(error)) from error
    return {"inserted": inserted}


