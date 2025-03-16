from pydantic import BaseModel
import typing as t
from datetime import datetime
from app.schema.minio import MinioParts
from app.schema.base import Id,Now


class Conversation(BaseModel):
    role: t.Literal['user','developer','assistent']='user'
    content: str | list[str]
    voice: t.Optional[MinioParts]=None
    
        
    
    
    
    def has_voice(self):
        return self.voice is not None
    

    
    @classmethod
    def get_projected_fields(cls):
        
        fields={k:1 for k in cls.model_fields.keys()}
        fields['_id']={"$toString": "$_id"}
        return fields

class CreateConversation(Conversation):
    created_at : datetime=Now

class UpdateConversation(BaseModel):
    role: t.Optional[t.Literal['user','developer','assistent']]=None
    content: t.Optional[str | list[str]]=None
    voice: t.Optional[MinioParts]=None
    updated_at: datetime=Now 


  
class ConversationWithId(CreateConversation,Id):
    pass