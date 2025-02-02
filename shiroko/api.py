from fastapi import APIRouter,HTTPException,Query
from fastapi.responses import StreamingResponse
from shiroko.service import ChatGPTService
from shiroko.database import databaseDependency,get_collection
from shiroko.logger import *
from shiroko.schema import *
import pymongo

router=APIRouter(prefix='/api')


@router.post('/prompt')
async def send_prompt_to_llm(prompt: UserPrompt):
    try:

        chatgpt=ChatGPTService()

        
        response=chatgpt.prompt(prompt.text)
        return StreamingResponse(response,media_type='application/json')
    except Exception as e:
        error('Failed to prompt AI')
        error(e)
        return HTTPException(500,detail={"message": "Failed to prompt AI"})
    
    
    
@router.post('/conversations')
async def create_new_conversation(conversation : UpdateConversation, db : databaseDependency):
    try:
        conversations=get_collection(db,'conversations')
        result=conversations.insert_one(conversation.model_dump())
        inserted_id=result.inserted_id
        
        inserted_document=conversations.find_one({"_id": inserted_id})
        if inserted_document is None:
            return HTTPException(400)
        return ConversationWithId(**inserted_document).model_dump(by_alias=True)
    except Exception as e:
        error(e)
        error('Failed to create new conversation')
        return HTTPException(500,detail={'message': 'fail'})
    
@router.get('/conversations',response_model=Pagination[ConversationWithId])
async def list_all_conversations(db : databaseDependency,page : int=Query(1,ge=1),limit : int=Query(10,ge=1)):
    try:
        conversations=get_collection(db,'conversations')
        offset=(page-1)*limit
        fields=Conversation.get_projected_fields()
        pipeline=[
            {"$project":fields},
            {"$sort": {"created_at":-1}},
            {"$skip": offset},
            {"$limit": limit}
            ]
        data=conversations.aggregate(pipeline).to_list()

        remaining_items=conversations.count_documents(skip=offset+limit,filter={})
        results={
            "total_documents": conversations.count_documents(filter={}),
            "count_remaining_items": remaining_items,
            "data": data,
            "remaining_pages":int(remaining_items/limit)
        }
        error(data)
        return Pagination[ConversationWithId](**results).model_dump()
        
    except Exception as e:
        error(e)
        return HTTPException(500)
    
@router.get('/conversations/{id}',response_model=ConversationWithId)
async def retrieve_conversation_by_id(db : databaseDependency,id : str):
    try:
        fields=Conversation.get_projected_fields()
        pipeline=[{"$match":{"_id": ObjectId(id)}},{"$project": fields}]
        conversation=get_collection(db,'conversations').aggregate(pipeline).next()
        if conversation is None:
            return HTTPException(400,detail={'message': 'Conversation was not found'})
        return ConversationWithId(**conversation).model_dump(by_alias=True)
        
    except Exception as e:
        error(e)
        return HTTPException(500)     

    
    


