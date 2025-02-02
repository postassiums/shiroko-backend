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
    
class Conversation(BaseModel):
    role: t.Literal['user','developer','assistent']
    content: str | list[str]
    created_at: datetime=Field(default_factory=lambda : datetime.now(tz=timezone.utc))
    
    @classmethod
    def get_projected_fields(cls):
        fields={k:1 for k in cls.model_fields.keys()}
        fields['_id']={"$toString": "$_id"}
        return fields

class UpdateConversation(Conversation):
    created_at: t.Optional[datetime]=Field(default_factory=lambda : datetime.now(tz=timezone.utc))

  
class ConversationWithId(Conversation,Id):
    pass

    

    
    
    
    
    



class Pagination[T](BaseModel):
    total_documents: int
    remaining_pages: int
    count_remaining_items: int
    data: t.List[T]    
    