from fastapi import APIRouter,Depends,UploadFile, File
from core.models.Message import Message
from externals.DB.message.create import addMessage
from externals.auth.auth import get_current_user
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer


oauth2_scheme = HTTPBearer()

router = APIRouter()

@router.post("/message/update/{indent}")
async def addNewMessage(
    chat_id: str,
    message: Message,
    token: HTTPAuthorizationCredentials = Depends(oauth2_scheme)

):
 