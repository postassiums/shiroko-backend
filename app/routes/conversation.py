from fastapi import APIRouter,HTTPException,Query
from fastapi.responses import StreamingResponse,JSONResponse
from app.services.conversation import ConversationServiceDependency
from app.services.queue import QueueServiceDependency
from app.services.llm import LLMService
from app.database import databaseDependency,get_collection
from app.schema.llm import UserPrompt
from app.schema.tts import OpenAITTSBody
from app.schema.minio import MinioItemPart
from app.schema.conversation import CreateConversation,ConversationWithId,UpdateConversation
from app.services.storage import StorageServiceDependency
from app.services.tts import OpenAITTSService
from app.logger import LOGGER
from app.params import PaginationDependency
import io
from app.debug import *

router=APIRouter(prefix='/conversations',tags=['Conversations'],redirect_slashes=False)


@router.post('/shiroko',description='Send prompt to LLM and create new conversation')
async def send_prompt_to_llm(prompt: UserPrompt):
    try:

        llm=LLMService()
        
        stream=llm.prompt(prompt.text)
        
        return StreamingResponse(stream,media_type='text/event-stream; charset=utf-8')
    except Exception as e:
        LOGGER.error('Failed to prompt AI')
        LOGGER.error(e)
        return HTTPException(500,detail={"message": "Failed to prompt AI"})
    
    
    
@router.post('',description='Create new conversation')
async def create_new_conversation(conversation_service : ConversationServiceDependency,
  conversation : CreateConversation, queue : QueueServiceDependency):
    try:
        result=conversation_service.create(conversation)
        if result==False:
            return HTTPException(404)
        queue.dispatch_tts_splitter_job(result)
        return result.model_dump(by_alias=True)
    except Exception as e:
        LOGGER.error(e)
        LOGGER.error('Failed to create new conversation')
        return HTTPException(500,detail={'message': 'fail'})




@router.get('',description='List all Conversations')
async def list_all_conversations(conversation_service : ConversationServiceDependency,pagination : PaginationDependency ):
    try:
        page,limit=pagination
        return conversation_service.list_paginated(page,limit)
        
    except Exception as e:
        LOGGER.error(e)
        return HTTPException(500)




@router.post('/{id}',response_model=ConversationWithId)
async def update_existing_conversation_by_id(conversation_service : ConversationServiceDependency,id : str,new_data : CreateConversation):
    conversation_service.update(id,new_data)

    found_conversation=conversation_service.get_specific_conversation(id)
    return found_conversation.model_dump(by_alias=True)



    
@router.get('/{id}',response_model=ConversationWithId)
async def retrieve_conversation_by_id(conversation_service : ConversationServiceDependency,id : str):
    try:
        conversation=conversation_service.get_specific_conversation(id)
       
        if conversation==False:
            return HTTPException(400,detail={'message': 'Conversation was not found'})
        return conversation.model_dump(by_alias=True)
        
    except Exception as e:
        LOGGER.error(e)
        return HTTPException(500)    
    

@router.delete('/{id}/audio',response_model=None)
async def delete_only_voice_associated_with_conversation(conversation_service : ConversationServiceDependency,storage_service : StorageServiceDependency,id : str):
    current_conversation=conversation_service.get_specific_conversation(id)
    if current_conversation==False:
        return JSONResponse(status_code=404,content={'detail': 'Conversation was not found'})
    if not(ConversationWithId(**current_conversation).has_voice()):
        return JSONResponse(status_code=404,content={'detail': 'There is not voice associated with this conversation'})
    storage_service.deleteVoice(id)
    conversation_service.delete_voice(id)
    
    
    return JSONResponse(status_code=204,content={'detail': 'Voice was deleted'})
    

    
@router.delete('/{id}')
async def delete_conversation(conversation_service : ConversationServiceDependency,storage_service : StorageServiceDependency,id : str):
    result=conversation_service.delete(id)
    if result.deleted_count==0:
        raise HTTPException(500,detail={'message': 'Failed to delete conversation'})
    return JSONResponse(status_code=404,content={'detail': 'Conversation deleted'})


@router.post('/{id}/voice')
async def dispatch_tts_job(conversation_service : ConversationServiceDependency,queue_service : QueueServiceDependency,id : str):
    result=conversation_service.get_specific_conversation(id)
    if result==False:
        raise HTTPException(404,detail={'message': 'Conversation was not found'})   
    queue_service.dispatch_tts_splitter_job(result)   
    return {'message': 'Conversation job dispatched'}

    


    


    

