from fastapi import APIRouter,HTTPException,Query
from fastapi.responses import StreamingResponse,JSONResponse
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
async def include_audio_into_conversation(conversation_service : ConversationServiceDependency,
    storage_service : StorageServiceDependency,rvc_service : RVCDependency,id : str):
    found_conversation=conversation_service.get_specific_conversation(id)
    if found_conversation==False:
        return HTTPException(404,detail={'message': 'Conversation does not exist'})
    found_conversation=ConversationWithId(**found_conversation)
    if found_conversation.has_voice() and found_conversation.voice.rvc_expired():
        new_rvc=MinioItem(url=storage_service.getRVCVoiceURL(id),expires_at=storage_service.getNewExpirationDate())
        found_conversation.voice.update_rvc(new_rvc)
        
    if found_conversation.has_voice():
        return found_conversation.model_dump()
    tts=OpenAITTSService(OpenAITTSBody(content=found_conversation.content))
    storage_service.putNormalTTSVoice(tts,id)

    await rvc_service.load_model()
    await storage_service.putRVCTTSVoice(rvc_service,tts,id)
 
    normal_tts_download_url=storage_service.getNormalVoiceURL(id)
    rvc_tts_download_url=storage_service.getRVCVoiceURL(id)
    updated_conversation=UpdateConversation(**found_conversation.model_dump(exclude=['id','updated_at']))
    new_normal_tts=MinioItem(url=normal_tts_download_url,expires_at= StorageService.getNewExpirationDate())
    new_rvc_tts=MinioItem(url=rvc_tts_download_url,expires_at=StorageService.getNewExpirationDate())
    
    updated_conversation.update_voice(new_normal_tts,new_rvc_tts)

    
    result=conversation_service.update(id,updated_conversation)
    await rvc_service.close()
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
    

@router.delete('/{id}/audio')
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


     

    

    


    

