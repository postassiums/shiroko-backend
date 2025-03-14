from pydantic import BaseModel
import typing as t
from datetime import datetime
from app.schema.minio import MinioItem
from app.schema.base import Id,Now

class Conversation(BaseModel):
    role: t.Literal['user','developer','assistent']='user'
    content: str | list[str]
    voice: t.List[MinioItem]=[]
    
        
    
    
    
    def is_voice_empty(self):
        return self.voice.__len__()>0
    

    
    @classmethod
    def get_projected_fields(cls):
        
        fields={k:1 for k in cls.model_fields.keys()}
        fields['_id']={"$toString": "$_id"}
        return fields

class CreateConversation(Conversation):
    created_at : datetime=Now

class UpdateConversation(Conversation):
    updated_at: datetime=Now 


  
class ConversationWithId(CreateConversation,Id):
    pass