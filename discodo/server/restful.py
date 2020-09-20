from fastapi import APIRouter, Header, HTTPException, Request
from ..config import Config

app = APIRouter()


def verify_auth(Authorization: str = Header(None)) -> str:
    if Authorization != Config.PASSWORD:
        raise HTTPException(403, "Password mismatch.")

    return Authorization


def verify_id(
    request: Request,
    UserID: int = Header(None),
    GuildID: int = Header(None),
    VoiceClientID: str = Header(None),
):
    if (
        not hasattr(request.app, "ClientManagers")
        or UserID not in request.app.ClientManagers
    ):
        raise HTTPException(400, "That UserID not connected.")

    ClientManager = request.app.ClientManagers[UserID]

    if not ClientManager.getVC(GuildID):
        raise HTTPException(400, "That GuildID not connected.")

    if not ClientManager.getVC(GuildID).id != VoiceClientID:
        raise HTTPException(403, "That VoiceClientID doesn't match.")

    return ClientManager.getVC(GuildID)