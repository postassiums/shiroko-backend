from fastapi import APIRouter,HTTPException,Query
from fastapi.responses import StreamingResponse
from app.service import *
from app.database import databaseDependency,get_collection
from app.logger import *
from app.schema import *



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
async def create_new_conversation(conversation_service : ConversationServiceDependency,conversation : ConversationBody):
    try:
        result=conversation_service.create(conversation)
        if result==False:
            return HTTPException(404)
        return result
    except Exception as e:
        error(e)
        error('Failed to create new conversation')
        return HTTPException(500,detail={'message': 'fail'})
    
@router.get('',response_model=Pagination[ConversationWithId],description='List all Conversations')
async def list_all_conversations(conversation_service : ConversationServiceDependency,page : int=Query(1,ge=1),limit : int=Query(10,ge=1)):
    try:
        return conversation_service.list_paginated(page,limit)
        
    except Exception as e:
        error(e)
        return HTTPException(500)
    
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

    


