from fastapi import APIRouter,HTTPException,Query,WebSocket
from fastapi.responses import StreamingResponse,JSONResponse
from app.services.conversation import ConversationServiceDependency
from app.services.queue import QueueServiceDependency
from app.services.llm import LLMService
from app.database import databaseDependency,get_collection
from app.schema.llm import UserPrompt
from app.schema.tts import OpenAITTSBody
from app.schema.conversation import *
from app.schema.base import *
from app.services.storage import StorageServiceDependency
from app.services.tts import OpenAITTSService
from app.logger import LOGGER
from app.params import PaginationDependency
import io
from app.debug import *
from minio.deleteobjects import DeletedObject
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
        if result.role=='assistent':
            queue.dispatch_tts_splitter_job(result)
        return result.model_dump(by_alias=True)
    except Exception as e:
        LOGGER.error(e)
        LOGGER.error('Failed to create new conversation')
        return HTTPException(500,detail={'message': 'fail'})




@router.get('',description='List all Conversations',response_model=Pagination[ConversationWithId])
async def list_all_conversations(conversation_service : ConversationServiceDependency,pagination : PaginationDependency ):
    try:
        page,limit=pagination
        return conversation_service.list_paginated(page,limit)
        
    except Exception as e:
        LOGGER.error(e)
        return HTTPException(500)


@router.post('/{id}/voice/renovate',response_model=None)
async def renovate_expired_voice_of_conversation(conversation_service : ConversationServiceDependency,
    storage_service : StorageServiceDependency, id : str):
    found=conversation_service.get_specific_conversation(id)
    if found==False:
        return HTTPException(404,detail={'message': 'No conversation found'})
    for index,part in enumerate(found.voice.parts):
        if part.has_expired():
            new_url=storage_service.sign_rvc_voice_url(id,index)
            part.renovate_expired_at()   
            part.url=new_url
    update_data=UpdateConversation(**found.model_dump(include=['id','voice'],by_alias=True))
    conversation_service.update(id,update_data)
    return found.model_dump(by_alias=True)


@router.put('/{id}',response_model=ConversationWithId)
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
    storage_service.delete_voice(id)
    conversation_service.delete_voice(id)
    
    
    return JSONResponse(status_code=204,content={'detail': 'Voice was deleted'})
    
@router.delete('/all')
async def delete_all_conversations_and_voices(conversation_service: ConversationServiceDependency,storage_service : StorageServiceDependency):
    error=storage_service.delete_all_tts_objects()
    if error is not None:
        raise HTTPException(500,detail={'message': f'Failed to delete storage Objects: {error.message} '})
    conversation_service.delete_all()

    return JSONResponse(status_code=202,content={'message': 'Deleted everything'})
    
@router.delete('/{id}')
async def delete_conversation(conversation_service : ConversationServiceDependency,storage_service : StorageServiceDependency,id : str):
    result=conversation_service.delete(id)
    if result.deleted_count==0:
        raise HTTPException(500,detail={'message': 'Failed to delete conversation'})
    return JSONResponse(status_code=404,content={'detail': 'Conversation deleted'})

@router.delete('/all')
async def delete_all_conversations(conversation_service : ConversationServiceDependency,storage_service : StorageServiceDependency):
    
    result=conversation_service.delete_all()
    storage_result=storage_service.deleteAllVoices()
    if isinstance(storage_result,DeletedObject):
        return JSONResponse(status_code=500,content={'detail': f'{storage_result.code} : {storage_result.message}'})
    
    return JSONResponse(status_code=202,content={'detail': f'Deleted {result.deleted_count} conversations and {storage_result} voices'})

@router.websocket('/{id}/voice/ws')
async def retrieve_audio_from_conversation(web_socket : WebSocket,conversation_service : ConversationServiceDependency,id : str):
    await web_socket.accept()
    retrieve_audio=True
    while retrieve_audio:
        result=conversation_service.get_specific_conversation(id)
        
        if result.has_voice() and result.voice.has_parts():
            continue
        voice=result.voice
        i=0
        total_parts=result.voice.total_parts
        while i<total_parts:
            web_socket.send_json(voice.parts[i])
            
            i+=1
        retrieve_audio=False
    web_socket.close()
            

            
            
    

    


    


    

