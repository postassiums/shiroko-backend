from fastapi import APIRouter,HTTPException,Query
from fastapi.responses import StreamingResponse
from app.service import *
from app.database import databaseDependency,get_collection
from app.logger import *
from app.schema import *
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
        error('Failed to prompt AI')
        error(e)
        return HTTPException(500,detail={"message": "Failed to prompt AI"})
    
    
    
@router.post('',description='Create new conversation')
async def create_new_conversation(conversation_service : ConversationServiceDependency,conversation : CreateConversation):
    try:
        result=conversation_service.create(conversation)
        if result==False:
            return HTTPException(404)
        return result
    except Exception as e:
        error(e)
        error('Failed to create new conversation')
        return HTTPException(500,detail={'message': 'fail'})
    
@router.get('',description='List all Conversations')
async def list_all_conversations(conversation_service : ConversationServiceDependency,pagination : PaginationDependency ):
    try:
        page,limit=pagination
        return conversation_service.list_paginated(page,limit)
        
    except Exception as e:
        error(e)
        return HTTPException(500)




@router.post('/{id}',response_model=ConversationWithId)
async def update_existing_conversation_by_id(conversation_service : ConversationServiceDependency,id : str,new_data : CreateConversation):
    conversation_service.update(id,new_data)

    found_conversation=conversation_service.get_specific_conversation(id)
    return ConversationWithId(**found_conversation).model_dump()

@router.post('/{id}/audio')
async def include_audio_into_conversation(conversation_service : ConversationServiceDependency,storage_service : StorageServiceDependency,id : str):

    found_conversation=conversation_service.get_specific_conversation(id)
    if found_conversation==False:
        return HTTPException(404,detail={'message': 'Conversation does not exist'})
    found_conversation=ConversationWithId(**found_conversation)
    if found_conversation.has_voice() and found_conversation.voice.has_expired():
        found_conversation.voice.update(storage_service.getAudioUrl(id),storage_service.getNewExpirationDate())
        
    if found_conversation.has_voice():
        return found_conversation.model_dump()
    tts=OpenAITTSService(OpenAITTSBody(content=found_conversation.content))
    buffer=io.BytesIO()
    for chunk in tts.tts_stream():
        buffer.write(chunk)
   
    length=buffer.tell()
    buffer.seek(0)
    result=storage_service.putAudioObject(id,buffer,length,tts.get_mime_type())
    buffer.close()
    download_url=storage_service.getAudioUrl(id)
    updated_conversation=UpdateConversation(**found_conversation.model_dump(exclude=['id','updated_at']))
    updated_conversation.voice=Voice(url=download_url,expires_at= datetime.now(tz=timezone.utc)+StorageService.EXPIRE_IN)
    result=conversation_service.update(id,updated_conversation)
    if not result.acknowledged:
        return HTTPException(500,detail={'message': 'Failed to update'})

        
    return ConversationWithId(**updated_conversation.model_dump(),id=id).model_dump(by_alias=True)

    
@router.get('/{id}',response_model=ConversationWithId)
async def retrieve_conversation_by_id(conversation_service : ConversationServiceDependency,id : str):
    try:
        conversation=conversation_service.get_specific_conversation(id)
       
        if conversation==False:
            return HTTPException(400,detail={'message': 'Conversation was not found'})
        return conversation
        
    except Exception as e:
        error(e)
        return HTTPException(500)     

    
# @router.post('/{id}/audio')
# async def create_audio_from_conversatio_content(conversation_service : ConversationServiceDependency,id : str):
#     # target_conversation=conversation_service.get_specific_conversation(id)
#     # if target_conversation==False:
#     #     return HTTPException(404)
#     # content=target_conversation.get('content')
#     voice_service=VoiceService()
#     voice_service.tts('teste')
    


    

