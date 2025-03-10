
import os
import typing as t
from openai import OpenAI,Stream
from openai.types.chat.chat_completion_chunk import ChatCompletionChunk
from app.database import *
from app.schema.tts import EdgeTTSBody,OpenAITTSBody,OpenAITTSVoices
from app.schema.base import Pagination
from app.services.llm import ChatGPT
from math import ceil
from pathlib import Path
from enum import Enum
from fastapi import Query
import httpx
import edge_tts
from dotenv import load_dotenv
from minio import Minio
import tempfile
import abc
import io
from app.schema.base import Pagination

class TTSBase(abc.ABC):
    
    
    
    @abc.abstractmethod
    def get_mime_type() -> str:
        pass
    
    @abc.abstractmethod
    def get_audio_format() -> str:
        pass
    
    
class EdgeTTSService(TTSBase):
    
    def __init__(self,body : EdgeTTSBody):
        self.voice=body.voice
        
        if not(self._voice_exists()):
            raise RuntimeError(f'The specific voice {body.voice} does not exists')
            
        self.audio_format='mp3'
        self.STREAM_CHUNK=body.STREAM_CHUNK
        self.content=body.content
        

        
    def get_audio_format(self):
        return self.audio_format

    def get_mime_type(self):
        return 'audio/mp3'
  
    


    
    async def tts_stream(self):
        communication=edge_tts.Communicate(self.content,self.voice)
        response=await communication.stream()
        return response

        
    async def _voice_exists(self):
        voice_manager=await edge_tts.VoicesManager.create()
        found_voices=voice_manager.find(ShortName=self.voice)
        return type(found_voices)==list and found_voices.__len__()>0
          
            
    @staticmethod  
    async def list_edge_tts_voices(page: int,limit : int,filter : dict[str,str]):   
        voice_manager=await edge_tts.VoicesManager.create()
        voices=voice_manager.voices
        
        if filter is not None:
            voices=voice_manager.find(**filter)
        total=voices.__len__()
        remaining_items=total-(page*limit)
        remaining_items=remaining_items if remaining_items>0 else 0
        remaning_pages=int(ceil(remaining_items/limit))
        data=voices[page-1:limit]
        
         
        return Pagination[edge_tts.voices.Voice](total_documents=total,count_remaining_items=remaining_items,data=data,remaining_pages=remaning_pages)
         

class OpenAITTSService(ChatGPT,TTSBase):


        
  
    
    
    
    def __init__(self,body : OpenAITTSBody,logger =LOGGER):
        self.voice=body.voice
        if not(self._voice_exists()):
            raise RuntimeError(f'The specific voice {self.voice} does not exists')
        
        super().__init__(body.model)
        
            
        self.STREAM_CHUNK=body.STREAM_CHUNK
        self.speed=body.speed
        self.audio_format=body.format
        self.content=body.content
        self.logger=logger
        
    def get_mime_type(self):
        mime_type_dict={
            "mp3": 'mpeg',
            'opus': 'ogg'
        }
        return f'audio/{self.audio_format}' if self.audio_format not in mime_type_dict.keys() else f'audio/{mime_type_dict.get(self.audio_format)}'
        
    def get_audio_format(self):
        return self.audio_format

    def _voice_exists(self):
        return self.voice in t.get_args(OpenAITTSVoices)

   
    
    def tts_stream_all_bytes(self):
        all_chunks=bytes()
        for chunk in self.tts_stream():
            all_chunks+=chunk
        return all_chunks
            
    
    
 
    
    def tts_stream(self):
        response=self.client.audio.speech.create(model=self.model,voice=self.voice,input=self.content,speed=self.speed,response_format=self.audio_format)
        for chunk in response.iter_bytes(self.STREAM_CHUNK):
            yield chunk
    

OpenAITTSDependency=t.Annotated[OpenAITTSService,Depends(OpenAITTSService)]
EdgeTTSDependency=t.Annotated[EdgeTTSService,Depends(EdgeTTSService)]