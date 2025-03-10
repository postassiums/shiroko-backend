import typing as t
from enum import Enum
import os
import pika
from pika.channel import Channel
from fastapi import Depends
from pika.channel import Channel
from app.schema.conversation import *
from app.services.tts import *
from app.services.storage import *
from app.schema.tts import *
from app.schema.llm import *
import json
from app.logger import LOGGER





class QueueService():
    class QueueNames(Enum):
        RVC = 'rvc'
        TTS = 'tts'
        TRANSCRIPTIONS = 'transcriptions'
        TTS_SPLITTER = 'tts_splitter'
        
        @classmethod
        def get_rvc(cls):
            return cls.RVC.value
        
        @classmethod 
        def get_tts(cls):
            return cls.TTS.value
        
        @classmethod
        def get_tts_splitter(cls):
            return cls.TTS_SPLITTER.value
    
    
    def __init__(self,logger : logging.Logger=LOGGER):
        host=os.getenv('RABBITMQ_HOST')
        port=int(os.getenv('RABBITMQ_PORT'))
        password=os.getenv('RABBITMQ_PASSWORD')
        user=os.getenv('RABBITMQ_USER')
        self.logger=logger
        parameters=pika.URLParameters(f'amqp://{user}:{password}@{host}:{port}')
        parameters.socket_timeout=60
        parameters.connection_attempts=3
        print(f'amqp://{user}:{password}@{host}:{port}')
        self.con=pika.BlockingConnection(parameters)
        self.channel=self.con.channel()
        self._create_queues()
        

    def _create_queues(self):
        for queue in self.QueueNames:
            self.channel.queue_declare(queue.value,durable=True)
            
    @staticmethod
    def get_queue():
        queue=QueueService()
        try:
            yield queue
        finally:
            queue.close()
            
            
    def close(self):
        self.channel.close()
    
    def dispatch_tts_job(self,data : SplitTTSBody):
        self.channel.basic_publish('',self.QueueNames.get_tts(),data.model_dump_json(by_alias=True))   
        self.logger.info('Dispatched job to TTS queue')
        
    def dispatch_rvc_job(self, data: RVCBody):
        queue_name=self.QueueNames.get_rvc()
        self.channel.basic_publish('',queue_name,data.model_dump_json(by_alias=True))
        self.logger.info('Dispatched job to RVC queue')
    
    def dispatch_tts_splitter_job(self,conversation : ConversationWithId):
        queue_name=self.QueueNames.get_tts_splitter()
        self.channel.basic_publish('',queue_name,conversation.model_dump_json(by_alias=True))
        self.logger.info('Dispatched job to TTS Splitter queue')
    




QueueServiceDependency=t.Annotated[QueueService,Depends(QueueService.get_queue)]