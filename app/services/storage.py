import os
import typing as t
from openai import OpenAI,Stream
from openai.types.chat.chat_completion_chunk import ChatCompletionChunk
from app.database import *
from math import ceil
from enum import Enum
from minio import Minio
from minio.deleteobjects import DeleteObject
import io
from datetime import timedelta
from app.services.rvc import *
from app.services.tts import OpenAITTSService,EdgeTTSService
from app.schema.minio import MinioItem
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
    def get_client(self):
        return self._client
    
    def _put_tts_voice(self,id : str,new_audio : bytes, mime_type : str,voice_type : VoiceType,index : int):
        dest=self.Buckets.getTTSBucketPath(id,voice_type,index)
        buffered_audio=io.BytesIO()
        buffered_audio.write(new_audio)
        length=buffered_audio.getbuffer().nbytes
        buffered_audio.seek(0)
        result=self._client.put_object(f'{self.Buckets.TTS.value}',dest,buffered_audio,length=length,content_type=mime_type)
        buffered_audio.close()
        return result
    
    def put_tts_voice_part(self,audio : bytes,mime_type : str,id : str,part : int):
        return self._put_tts_voice(id,audio,mime_type,'normal',part)
    
    def get_voice(self,id: str,index: int,voice_type : VoiceType='normal'):
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
    
    def delete_voice(self, id : str):
        for voice in t.get_args(VoiceType):
            self._client.remove_object(self.Buckets.TTS.value,f'{id}/{voice}')
            
    def delete_all_tts_objects(self):
        TTS_BUCKET=self.Buckets.TTS.value
        storage_objects= self._client.list_objects(TTS_BUCKET,recursive=True)
        objects_to_be_deleted=list(map(lambda item: DeleteObject(item.object_name),storage_objects))
        errors=self._client.remove_objects(TTS_BUCKET,objects_to_be_deleted)
        for error in errors:
            return error
            
    
    def put_rvc_voice(self, rvc_audio: bytes,mime_type : str,id : str,index : int):
        return self._put_tts_voice(id,rvc_audio,mime_type,'rvc',index)
            

        
    def renovate_voice(self, id : str,item : MinioItem,type : VoiceType):
        item.renovateExpiresAt()
        if type=='normal':
            item.url=self.getNormalVoiceURL(id)
            return item
  
        item.url=self.get_rvc_voice_url(id)
        
        return item
    
    def deleteAllVoices(self):
        bucket=self.Buckets.TTS.value
        objects=self._client.list_objects(bucket)
        delete_objects=list(map(lambda x: DeletedObject(x.object_name),objects))
        errors=self._client.remove_objects(bucket,delete_objects)
        for error in errors:
            return error
        
        return delete_objects.__len__()  
    
    
    def _get_voice_url(self, id: str,voice_type : VoiceType, part : int,expires_at):
        dest=f'{id}/{voice_type}/{part}'
        return self._client.presigned_get_object(self.Buckets.TTS.value,dest,expires=expires_at)
    
    def get_rvc_voice_url(self, id: str,part : int):
        expires_at=timedelta(hours=1)
        return self._get_voice_url(id,'rvc',part,expires_at)
    
    
    

        
        
StorageServiceDependency=t.Annotated[StorageService,Depends(StorageService.get_storage)]