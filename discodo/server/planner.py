import functools
import ipaddress

from sanic import Blueprint, response
from sanic.exceptions import abort

from ..config import Config

app = Blueprint(__name__)


def authorized(func):
    @functools.wraps(func)
    def wrapper(request, *args, **kwargs):
        if request.headers.get("Authorization") != Config.PASSWORD:
            abort(403, "Password mismatch.")

        return func(request, *args, **kwargs)

    return wrapper


@app.get("/planner")
@authorized
async def plannerStatus(request):
    if not Config.RoutePlanner:
        abort(404, "RoutePlanner is not enabled.")

    return response.json(
        {
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
    )


@app.post("/planner/unmark")
@authorized
async def plannerUnmark(request):
    if not Config.RoutePlanner:
        abort(404, "RoutePlanner is not enabled.")

    address = "".join(request.args.get("address", [])).strip()
    if not address:
        abort(400, "Missing parameter address.")

    Config.RoutePlanner.unmark_failed_address(ipaddress.ip_address(address))

    return response.json({"status": 200})


@app.post("/planner/unmark/all")
@authorized
async def plannerUnmarkAll(request):
    if not Config.RoutePlanner:
        abort(404, "RoutePlanner is not enabled.")

    Config.RoutePlanner.failedAddress.clear()

    return response.json({"status": 200})
