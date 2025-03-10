from app.services.queue import QueueService

from pika.channel import Channel
from pika.channel import Channel
from app.schema.conversation import *
from app.services.tts import *
from app.services.storage import *
from app.schema.tts import *
from app.schema.llm import *
import json
import abc
from app.debug import *
import re
from bson import ObjectId
class ConsumerBase(QueueService):
    
    def __init__(self):
        super().__init__()
        
    def __enter__(self):
        return self
    
    def register_consume(self, queue_name : QueueService.QueueNames,callback):
        self.channel.basic_consume(queue_name.value,callback,auto_ack=False)
        
    @staticmethod
    def body_to_json(body: bytes):
        return json.loads(body.decode())
        
    
    def consume(self):
        self.channel.start_consuming()
    
    def __exit__(self,type, value, traceback):
        self.channel.stop_consuming()
        self.close()
        return True
        

class TTSConsumer(ConsumerBase):
    def __init__(self):
        super().__init__()
        self.logger=logging.getLogger('tts')
        self._register_task()
        
    def _register_task(self):
        def send_message_part_to_tts_service(ch: Channel,method,properties,body : bytes):
            try:
                self.logger.info('Initiating TTS Task')
                data : SplitTTSBody=SplitTTSBody(**json.loads(body.decode()))
                self.logger.info(f'TTS Body data: {data.model_dump_json(by_alias=True)} ')
                tts_service=OpenAITTSService(OpenAITTSBody(content=data.content),logger=self.logger)
                storage_service=StorageService(self.logger)
                audio=tts_service.tts_stream_all_bytes()
                self.logger.info('TTS Audio is ready')
                mime_type=tts_service.get_mime_type()
                storage_service.putTTSVoicePart(audio,mime_type,data.id,data.index)
                self.logger.info('Audio was stored on Minio')
                self.dispatch_rvc_job(RVCBody(index=data.index,id=data.id,total_parts=data.total_parts))
                self.logger.info('TTS Task completed')
                
                ch.basic_ack(delivery_tag=method.delivery_tag)
            except Exception as e:
                self.logger.critical('Failed to complete TTS task')
                self.logger.critical(e)
                ch.basic_ack(delivery_tag=method.delivery_tag)
        self.register_consume(self.QueueNames.TTS,send_message_part_to_tts_service)
        self.logger.info('Registered TTS consumer')
        
    
    
        
class TTSSplitConsumer(ConsumerBase):
    
    
    def __init__(self):
        super().__init__()
        self.logger=logging.getLogger('tts.splitter')
        self._register_task()
    
    def _register_task(self):
        def split_messages_to_tts_queue(ch : Channel,method ,properties,body : bytes):
            try:
                conversation=ConversationWithId(**json.loads(body.decode()))
                pattern=r'([^\.!?;]+[\.!?;]{1,50})'
                split_result=re.split(pattern,conversation.content)
                result=[x.strip() for x in list(filter(None,split_result))]
                total_parts=result.__len__()
                for index,message in enumerate(result):
                    new_data=SplitTTSBody(index=index,content=message,id=conversation.id,total_parts=total_parts)
                    self.dispatch_tts_job(new_data)
                    self.logger.info('Sending to TTS queue')
                with get_db_context_manager() as db:
                    conversations=db.get_collection('conversations')
                    conversation.voice=Voice(total_parts=result.__len__(),full=None)
                    conversations.update_one({'_id': ObjectId(conversation.id)},{'$set':conversation.model_dump_json(include='voice')})
                ch.basic_ack(delivery_tag=method.delivery_tag)
            except Exception as e:
                self.logger.critical(e)
                self.logger.critical('Failed to send to TTS queue')
                ch.basic_ack(delivery_tag=method.delivery_tag)
        self.register_consume(self.QueueNames.TTS_SPLITTER,split_messages_to_tts_queue)
        self.logger.info('Registered TTS Splitter consumer')
        
        
class RVCConsumer(ConsumerBase):
    
    def __init__(self):
        super().__init__()
        self._register_task()
        
    def _register_task(self):
        def convert_tts_voice_using_rvc(ch : Channel,method,properties,body : bytes):
            try:
                self.logger.info('Initizing RVC task')
                body_data=ConsumerBase.body_to_json(body)
                body_data=RVCBody(**body_data)
                storage_service=StorageService(self.logger)
                with SyncRVCService(self.logger) as rvc_service:
                    tts_bytes=storage_service.getVoice(body_data.id,body_data.index,'normal')
                    rvc_audio_bytes,rvc_audio_mime_type=rvc_service.convert_file(tts_bytes)
                    storage_service.putRVCTTSVoice(rvc_audio_bytes,rvc_audio_mime_type,body_data.id,body_data.index)
                ch.basic_ack(delivery_tag=method.delivery_tag)
                self.logger.info('Finished RVC Task')
                
            except Exception as e:
                self.logger.critical(e)
        self.register_consume(self.QueueNames.RVC,convert_tts_voice_using_rvc)
        
                
            
        
    
    
    
