import os
import typing as t
from openai import OpenAI,Stream
from openai.types.chat.chat_completion_chunk import ChatCompletionChunk
import random
from app.database import *

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
from datetime import timedelta
from app.logger import LOGGER

AudioType=t.Literal['rvc','tts']
VoiceType=t.Literal['normal','rvc']

class AsyncRVCService():
    

   
    
    def __init__(self,logger: logging.Logger=LOGGER):
        HOST=os.getenv('RVC_HOST')
        PORT=os.getenv('RVC_PORT')
        self.URL=f'http://{HOST}:{PORT}'
        self.TIMEOUT=60*5
        self.client=httpx.AsyncClient(base_url=self.URL,timeout=self.TIMEOUT)
        self.logger=logger

    @staticmethod
    async def get_rvc_service():
        rvc= AsyncRVCService()
        try:
            yield rvc
        finally:
            await rvc.close()
            
    
    
    async def load_model(self,model_name : str='shiroko'):

        response=await self.client.post(f'/models/{model_name}')
        response.raise_for_status()
        return response.text
    
    async def convert_file(self ,audio : bytes):
        
        response=await self.client.post('/convert_file',files={'file': audio},timeout=60*5)
        mime_type=response.headers.get('content-type')
 
        return (response.content,mime_type)
    
    async def close(self):
        await self.client.aclose()

class SyncRVCService():
    def __init__(self,logger: logging.Logger=LOGGER):
        HOST=os.getenv('RVC_HOST')
        PORT=os.getenv('RVC_PORT')
        self.URL=f'http://{HOST}:{PORT}'
        self.TIMEOUT=60*5
        self.client=httpx.Client(base_url=self.URL,timeout=self.TIMEOUT)
        self.logger=logger
        
    def __enter__(self):
        self.load_model()
        return self
    
    def __exit__(self,type,value,traceback):
        self.close()
        
    def load_model(self,model_name : str='shiroko'):

        response=self.client.post(f'/models/{model_name}')
        response.raise_for_status()
        return response.text
    
    def convert_file(self ,audio : bytes):
        
        response=self.client.post('/convert_file',files={'file': audio})
        mime_type : str=response.headers.get('content-type')
        return (response.content,mime_type)
    
        
    def close(self):
        self.client.close()
        
        
AsyncRVCDependency=t.Annotated[AsyncRVCService,Depends(AsyncRVCService.get_rvc_service)]