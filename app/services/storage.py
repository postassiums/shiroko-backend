import os
import typing as t
from openai import OpenAI,Stream
from openai.types.chat.chat_completion_chunk import ChatCompletionChunk
from app.database import *
from math import ceil
from enum import Enum
from fastapi import Query
from dotenv import load_dotenv
from minio import Minio
import io

from app.services.rvc import *
from app.services.tts import OpenAITTSService,EdgeTTSService
from app.schema.minio import MinioItemPart
from datetime import *
from app.logger import LOGGER

        



        

class StorageService():
    class Buckets(Enum):
        
        VIDEOS='videos'
        AUDIOS='audios'
        TTS='tts'
        
        @classmethod
        def getTTSBucketPath(cls,id : str,voice_type : VoiceType,filename : str | int):
            return f'{id}/{voice_type}/{filename}'
    
    @staticmethod
    def get_storage():
        return StorageService() 
        
    def __init__(self,logger : logging.Logger=LOGGER):
        try:
            HOST=f"{os.getenv('MINIO_HOST')}:9000"
            ACCESS_KEY=os.getenv('MINIO_ACCESS_KEY')
            SECRET_KEY=os.getenv('MINIO_SECRET_KEY')
            self._client=Minio(HOST,ACCESS_KEY,SECRET_KEY,secure=False)
            self._createBucketsIfNeeded()
            self.logger=logger
            
        
        except Exception as e:
            
            self.logger.critical(e)
            raise HTTPException(500,detail='Failed to connect to Minio')
    
    def _createBucketsIfNeeded(self):   

        for bucket in self.Buckets:
            if not(self._client.bucket_exists(bucket.value)):
                self._client.make_bucket(bucket.value) 
    def getClient(self):
        return self._client
    
    def _putTTSVoice(self,id : str,new_audio : bytes, mime_type : str,voice_type : VoiceType,index : int):
        dest=self.Buckets.getTTSBucketPath(id,voice_type,index)
        buffered_audio=io.BytesIO()
        buffered_audio.write(new_audio)
        length=buffered_audio.getbuffer().nbytes
        buffered_audio.seek(0)
        result=self._client.put_object(f'{self.Buckets.TTS.value}',dest,buffered_audio,length=length,content_type=mime_type)
        buffered_audio.close()
        return result
    
    def putTTSVoicePart(self,audio : bytes,mime_type : str,id : str,part : int):
        return self._putTTSVoice(id,audio,mime_type,'normal',part)
    
    def getVoice(self,id: str,index: int,voice_type : VoiceType='normal'):
        response=None
        try:
            response=self._client.get_object(self.Buckets.TTS.value,self.Buckets.getTTSBucketPath(id,voice_type,index))
            return response.data
        except Exception as e:
            self.logger.critical(e)
            
        finally:
            if response is None:
                return
            response.close()
            
            response.release_conn()
    
    def deleteVoice(self, id : str):
        for voice in t.get_args(VoiceType):
            self._client.remove_object(self.Buckets.TTS.value,f'{id}/{voice}')
            
    
    def putRVCTTSVoice(self, rvc_audio: bytes,mime_type : str,id : str,index : int):
        return self._putTTSVoice(id,rvc_audio,mime_type,'rvc',index)
            

        
    def renovateVoice(self, id : str,item : MinioItemPart,type : VoiceType):
        item.renovateExpiresAt()
        if type=='normal':
            item.url=self.getNormalVoiceURL(id)
            return item
  
        item.url=self.getRVCVoiceURL(id)
        
        return item
    
    
    
    def _getVoiceURL(self, id: str,voice_type : VoiceType):
        dest=f'{id}/{voice_type}'
        return self._client.presigned_get_object(self.Buckets.TTS.value,dest,expires=self.EXPIRE_IN)
    
    def getNormalVoiceURL(self, id : str):
        return self._getVoiceURL(id,'normal')
    
    def getRVCVoiceURL(self, id: str):
        return self._getVoiceURL(id,'rvc')
    
    
    

        
        
StorageServiceDependency=t.Annotated[StorageService,Depends(StorageService.get_storage)]