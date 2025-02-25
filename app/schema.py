from pydantic import BaseModel,Field,field_serializer,ConfigDict,BeforeValidator
import typing as t
from datetime import datetime,timezone
from bson.objectid import ObjectId

class UserPrompt(BaseModel):
    text: str

PydanticObjectId=t.Annotated[str,BeforeValidator(str)]     

class Id(BaseModel):
    model_config=ConfigDict(populate_by_name=True)
    id: PydanticObjectId=Field(alias='_id')  


Now=Field(default_factory=lambda  :datetime.now(tz=timezone.utc))

class MinioItem(BaseModel):
    url: str
    expires_at : datetime
    
    def has_expired(self):
        return self.expires_at>=datetime.now()
    
    def update(self,new_url : str,new_expiration : datetime):
        self.url=new_url
        self.expires_at=new_expiration
    


class Voice(BaseModel):
    normal_tts: MinioItem
    rvc_tts: MinioItem
    
    def rvc_expired(self):
        return self.rvc_tts.has_expired()
    
    def update_normal_tts(self, new_tts: MinioItem):
        self.normal_tts=new_tts
    
    def update_rvc(self,new_rvc : MinioItem):
        self.rvc_tts=new_rvc

class OptionalTimestamps():
    updated_at : t.Optional[datetime]=None
    created_at: t.Optional[datetime]=None
    
    
class Conversation(BaseModel):
    role: t.Literal['user','developer','assistent']='user'
    content: str | list[str]
    voice: t.Optional[Voice]=None
    
    def update_voice(self,normal_tts: MinioItem,rvc_tts: MinioItem):
        self.voice=Voice(normal_tts=normal_tts,rvc_tts=rvc_tts)
    
    
    def has_voice(self):
        return self.voice is not None
    

    
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

    

    
    
    
    
    
T=t.TypeVar('T')


class Pagination(BaseModel,t.Generic[T]):
    total_documents: int
    remaining_pages: int
    count_remaining_items: int
    data: t.List[T]    
    

OpenAIModels=t.Literal['gpt-3.5-turbo-0125']
OpenAITTSModels=t.Literal['tts-1','tts-1-hd']   
OpenAITTSVoices=t.Literal['alloy', 'ash', 'coral', 'echo', 'fable', 'onyx', 'nova', 'sage', 'shimmer']
AudioFormat=t.Literal['mp3', 'opus', 'aac', 'wav']
 
class OpenAITTSBody(BaseModel):
    content :str
    voice: OpenAITTSVoices='nova'
    model : OpenAITTSModels='tts-1'
    STREAM_CHUNK: t.Optional[int]=1024
    speed : t.Optional[int]=1
    format: t.Optional[AudioFormat]='mp3'
    
class EdgeTTSBody(BaseModel):
    content : str
    voice : str
    STREAM_CHUNK: t.Optional[int]=1024
    


        
    