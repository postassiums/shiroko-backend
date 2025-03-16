from pydantic import BaseModel,Field
import typing as t
from datetime import datetime,timedelta,timezone








class MinioItem(BaseModel):
    url: str
    expires_at : datetime=Field(default_factory=lambda : MinioItem.getNewExpirationDate())
    def has_expired(self):
        return self.expires_at>=datetime.now()
    
    def renovateExpiresAt(self):
        self.expires_at=MinioItem.getNewExpirationDate()
        
    @classmethod 
    def getNewExpirationDate(cls):
        return datetime.now(tz=timezone.utc)+timedelta(days=7)
            
    

    
    def update(self,new_url : str,new_expiration : datetime=None):
        self.url=new_url
        self.expires_at= new_expiration if new_expiration is not None else self.getNewExpirationDate()
        return self
    
    
class MinioParts(BaseModel):
    parts: t.List[MinioItem]=[]
    total_parts: int
    
    def has_parts(self):
        return self.parts>0