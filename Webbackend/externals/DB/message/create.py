from externals.DB.db_init import db
from fastapi import APIRouter, HTTPException
from core.models.Message import Message
from datetime import datetime
from bson import ObjectId
import httpx
from dotenv import load_dotenv
import os
load_dotenv()
ragHost = os.getenv('RAGBASEURL')


async def addMessage(chat_id: str, message: Message):
    chat_entity = db.Chat
    chat_object_id = ObjectId(chat_id)
    # Find the chat by chat_id
    chat = chat_entity.find_one({"_id": chat_object_id})
    
    if not chat:
        raise HTTPException(status_code=404, detail="Chat not found")
    
    print("Chat found:", chat)  # Debug the found chat

    # Add the new message to the chat's message list
    update_result = chat_entity.update_one(
        {"_id": chat_object_id},
        {"$push": {"messages": message.dict()}}
    )

    print("Message added to chat, update_result:", update_result.modified_count)

    # Ensure the keys 'chunks' and 'numofresults' exist in the chat document
    chunks = chat.get('chunks', 500)  # Default value of 500 if 'chunks' is not found
    numofresults = chat.get('numofresults', 1) 
    filenames=chat.get('fileName',"")
    modelname=chat.get('modelname',"llama3")
    messages = chat.get('messages', [])
    history = messages[-5:] if len(messages) >= 5 else messages  # Retrieve last 5 messages or all if less than 5
        # Create a new history with only 'content' and 'message_type'
    filtered_history = [{'content': msg['content'], 'message_type': msg['message_type']} for msg in history]
    
    # Prepare the payload for the external API request

    external_payload = {
        'filenames':filenames,
        'chunks': chunks,
        'numofresults': numofresults,
        'question': message.content,
        'modelname':modelname,
        'history':filtered_history
    }

    print("External payload:", external_payload)

    # Send the request to the other backend
    async with httpx.AsyncClient(timeout=60.0) as client:
        try:
            response = await client.post(
                ragHost+"api/query/",
                json=external_payload
            )
            response.raise_for_status()  # Raises an error for 4xx/5xx responses



            response_data = response.json()  # Ensure this works without errors

            responseMessage = Message(
                content=response_data.get('message', 'No message content'),
                message_time=datetime.now(),
                message_type="response"
            )
            

            
            update_result = chat_entity.update_one(
                {"_id": chat_object_id},
                {"$push": {"messages": responseMessage.dict()}}
            )

        except httpx.HTTPStatusError as e:
            print("HTTPStatusError:", e)
            raise HTTPException(status_code=e.response.status_code, detail="Failed to notify external service")
        except Exception as e:
            print("General Exception:", repr(e))  # Use repr to capture the full exception details
            raise HTTPException(status_code=500, detail=f"An error occurred: {str(e)}")

    return responseMessage
