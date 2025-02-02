
import os
import typing as t
from openai import OpenAI,Stream
from openai.types.chat.chat_completion_chunk import ChatCompletionChunk
import random
from app.database import *
from app.schema import *
from app.service import *
from math import ceil


class ConversationService():
    def __init__(self,db : databaseDependency):
        self.db=db
    
    def create(self,new_conversation : ConversationBody):
        conversations=get_collection(self.db,'conversations')
        result=conversations.insert_one(new_conversation.model_dump())
        inserted_id=result.inserted_id
        
        inserted_document=conversations.find_one({"_id": inserted_id})
        if inserted_document is None:
            return False
        return ConversationWithId(**inserted_document).model_dump(by_alias=True)
    

    
    def get_specific_conversation(self, id : str):
        fields=Conversation.get_projected_fields()
        pipeline=[{"$match":{"_id": ObjectId(id)}},{"$project": fields}]
        conversation=get_collection(self.db,'conversations').aggregate(pipeline).next()
        if conversation is None:
            return False
        return ConversationWithId(**conversation).model_dump(by_alias=True)
    
    def list_paginated(self,page : int, limit : int):
        conversations=get_collection(self.db,'conversations')
        offset=(page-1)*limit
        fields=Conversation.get_projected_fields()
        pipeline=[
            {"$project":fields},
            {"$sort": {"created_at":-1}},
            {"$skip": offset},
            {"$limit": limit}
            ]
        data=conversations.aggregate(pipeline).to_list()
        data.reverse()
        remaining_items=conversations.count_documents(skip=offset+limit,filter={})
        results={
            "total_documents": conversations.count_documents(filter={}),
            "count_remaining_items": remaining_items,
            "data":data,
            "remaining_pages":int(ceil(remaining_items/limit))
        }
        return Pagination[ConversationWithId](**results).model_dump(by_alias=True)

   
ConversationServiceDependency=t.Annotated[ConversationService,Depends(ConversationService)]     

class LLMService():
    
    __instance__=None
    
    def __new__(cls) :
        if cls.__instance__ is None:
            cls.__instance__=super().__new__(cls)
            cls.__instance__._initialize()
            
        
        
        return cls.__instance__
    
    
    def _initialize(self):
        self.API_KEY=os.getenv('OPENAI_API_KEY')
        self.model='gpt-3.5-turbo-0125'
        self.client=OpenAI(api_key=self.API_KEY)
        with open('static/shiroko_prompt.md','r') as f:
            self.system_prompt=f.read()
    
    
    def __repr__(self):
        return f'Model: {self.model} \n API_KEY: {self.API_KEY}'
    
    async def prompt(self,user_prompt : str):
        chunks= self.client.chat.completions.create(model=self.model,stream=True,messages=[
            {"role": "developer","content":"You are Sunnaokami Shiroko from the game Blue Archieve"},
            {"role": "user","content": user_prompt}
        ])
        for chunk in chunks:
            choices=chunk.choices
            #TODO: Escolher aleatoriamente
            chosen_message=choices[0].delta.content
            if chosen_message is not None:
                yield chosen_message

        

        
        

        
