import ipaddress

from fastapi import APIRouter, Depends, Header, HTTPException

from ..config import Config

app = APIRouter()


def authorized(Authorization: str = Header(None)) -> str:
    if Authorization != Config.PASSWORD:
        raise HTTPException(403, "Password mismatch.")

    return Authorization


@app.get("/planner", dependencies=[Depends(authorized)])
async def plannerStatus() -> dict:
    if not Config.RoutePlanner:
        raise HTTPException(status_code=404, detail="RoutePlanner is not enabled.")

    return {
        "ipBlocks": [
            {
                "version": ipBlock.version,
                "broadcast_address": ipBlock.broadcast_address,
                "size": ipBlock.num_addresses,
            }
            for ipBlock in Config.RoutePlanner.ipBlocks
        ],
        "failedAddresses": [
            dict(data, address=address)
            for address, data in Config.RoutePlanner.failedAddress.items()
        ],
    }


@app.post("/planner/unmark", dependencies=[Depends(authorized)])
async def plannerUnmark(address: str) -> dict:
    if not Config.RoutePlanner:
        raise HTTPException(status_code=404, detail="RoutePlanner is not enabled.")

    Config.RoutePlanner.unmark_failed_address(ipaddress.ip_address(address))

    return {"status": 200}


@app.post("/planner/unmark/all", dependencies=[Depends(authorized)])
async def plannerUnmark() -> dict:
    if not Config.RoutePlanner:
        raise HTTPException(status_code=404, detail="RoutePlanner is not enabled.")

    Config.RoutePlanner.failedAddress.clear()

    return {"status": 200}
