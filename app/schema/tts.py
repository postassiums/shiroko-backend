from pydantic import BaseModel
import typing as t
from app.schema.conversation import ConversationWithId

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
    
    
class SplitTTSBody(BaseModel):
    index: int
    content: str
    id: str
    total_parts: int
    
class RVCBody(BaseModel):
    index : int
    total_parts: int
    id: str