
import typing as t
from app.database import *
from app.schema.conversation import *
from app.schema.base import *
from math import ceil

from fastapi import Query
from bson import ObjectId

class ConversationService():
    def __init__(self,db : databaseDependency):
        self.db=db
        self.conversations=get_collection(self.db,'conversations')
    
    def create(self,new_conversation : CreateConversation):
        
        result=self.conversations.insert_one(new_conversation.model_dump())
        inserted_id=result.inserted_id
        
        inserted_document=self.conversations.find_one({"_id": inserted_id})
        if inserted_document is None:
            return False
        return ConversationWithId(**inserted_document)
    
    def update(self,id : str,data : UpdateConversation):
        target_id=ObjectId(id)
        return self.conversations.update_one({"_id": target_id },{'$set': data.model_dump()})

    def delete_voice(self,id :str):
        return self.conversations.update_one({'_id': ObjectId(id)},{'$set': {'voice': None}})  

    def delete(self, id : str):
        return self.conversations.delete_one({'_id': ObjectId(id)})
    
    def delete_all(self):
        return self.conversations.delete_many({},{})
    
    # def renovate_voice(self,storage_service : StorageService):
    #     new_tts=MinioItem(url=storage_service.getNormalVoiceURL(id),expires_at=storage_service.getNewExpirationDate())
    #     found_conversation.voice.update_normal_tts(new_tts)
    
    def get_specific_conversation(self, id : str):
        fields=Conversation.get_projected_fields()
        pipeline=[{"$match":{"_id": ObjectId(id)}},{"$project": fields}]
        conversation=self.conversations.aggregate(pipeline).next()
        if conversation is None:
            return False
        return ConversationWithId(**conversation)
    
    def list_paginated(self,page : t.Annotated[int,Query(1,ge=1)], limit : t.Annotated[int,Query(10,ge=1)]):

        offset=(page-1)*limit
        fields=Conversation.get_projected_fields()
        pipeline=[
            {"$project":fields},
            {"$sort": {"created_at":-1}},
            {"$skip": offset},
            {"$limit": limit}
            ]
        data=self.conversations.aggregate(pipeline).to_list()
        data.reverse()
        remaining_items=self.conversations.count_documents(skip=offset+limit,filter={})
        results={
            "total_documents": self.conversations.count_documents(filter={}),
            "count_remaining_items": remaining_items,
            "data":data,
            "remaining_pages":int(ceil(remaining_items/limit))
        }
        return Pagination[ConversationWithId](**results).model_dump(by_alias=True)

   
ConversationServiceDependency=t.Annotated[ConversationService,Depends(ConversationService)] 