import os
from typing import Any, AsyncIterator

import requests
from covalent import CovalentClient, Response
from covalent.services.balance_service import BalancesResponse
from fastapi import FastAPI, status
from fastapi.responses import HTMLResponse, JSONResponse
from requests.auth import HTTPBasicAuth

API_KEY = os.environ.get("API_KEY", "")


# Define lifespan to manage application startup and shutdown
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    app.state._state["covalent_client"] = CovalentClient(API_KEY)
    yield


app = FastAPI(lifespan=lifespan)


@app.get("/")
async def index() -> HTMLResponse:
    """The default endpoint of the API."""
    return HTMLResponse("Welcome to CryptoTrack!")


@app.get("/assets")
async def get_assets(wallet_address: str, chain: str = "eth-mainnet") -> Any:
    c: CovalentClient | None = app.state._state.get("covalent_client", None)
    if not c:
        return HTMLResponse(
            "Connection to Covalent is missing", status.HTTP_404_NOT_FOUND
        )

    b: Response[BalancesResponse] = (
        c.balance_service.get_token_balances_for_wallet_address(chain, wallet_address)
    )
    if not b.error:
        response = {
            item.contract_name: item.contract_decimals
            for item in b.data.items
            if item is not None
        }
        return JSONResponse(response, headers={"Content-Type": "application/json"})

    else:
        return JSONResponse(b.error_message, b.error_code)


@app.get("/total_usd")
async def get_total_usd(
    wallet_address: str, chain: str = "eth-mainnet"
) -> HTMLResponse:
    c: CovalentClient | None = app.state._state.get("covalent_client", None)
    if not c:
        return HTMLResponse(
            "Connection to Covalent is missing", status.HTTP_404_NOT_FOUND
        )

    b: Response[BalancesResponse] = (
        c.balance_service.get_token_balances_for_wallet_address(
            chain, wallet_address, quote_currency="USD"
        )
    )
    if not b.error:
        balance = sum(iter(item.quote for item in b.data.items if item and item.quote))
        return JSONResponse(
            f"Your total USD balance is: {balance:.2f}$",
            headers={"Content-Type": "application/json"},
        )
    else:
        return JSONResponse(b.error_message, b.error_code)


@app.get("/transactions")
async def get_transactions(
    wallet_address: str, chain: str = "eth-mainnet", page: str = "0"
) -> HTMLResponse:
    c: CovalentClient | None = app.state._state.get("covalent_client", None)
    if not c:
        return HTMLResponse(
            "Connection to Covalent is missing", status.HTTP_404_NOT_FOUND
        )

    basic = HTTPBasicAuth(API_KEY, "")

    response = requests.get(
        f"https://api.covalenthq.com/v1/eth-mainnet/address/{wallet_address}/transactions_v3/page/{page}/?",
        headers={
            "accept": "application/json",
        },
        auth=basic,
    )

    return HTMLResponse(response.text, response.status_code)
