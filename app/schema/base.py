from pydantic import BaseModel,Field,field_serializer,ConfigDict,BeforeValidator
import typing as t
from datetime import datetime,timezone



PydanticObjectId=t.Annotated[str,BeforeValidator(str)]     
Now=Field(default_factory=lambda  :datetime.now(tz=timezone.utc))
class Id(BaseModel):
    model_config=ConfigDict(populate_by_name=True)
    id: PydanticObjectId=Field(alias='_id')  
    
    
    
class OptionalTimestamps():
    updated_at : t.Optional[datetime]=None
    created_at: t.Optional[datetime]=None
    
    
T=t.TypeVar('T')


class Pagination(BaseModel,t.Generic[T]):
    total_documents: int
    remaining_pages: int
    count_remaining_items: int
    data: t.List[T]    
    