import pymongo
import os

import pymongo.database
import pymongo.errors
import typing as t
from fastapi import Depends,HTTPException
from app.logger import *
from contextlib import contextmanager
collection_names=t.Literal['conversations','audios']
 
def get_db():
    host=os.getenv('DB_HOST') or 'localhost'
    port=os.getenv('DB_PORT') or 27017
    uri=f"mongodb://{host}:{port}"
    username=os.getenv('DB_USER')
    password=os.getenv('DB_PASSWORD')
    db=pymongo.MongoClient(uri,username=username,password=password)
    try:
        LOGGER.debug('Connected to the database succesufully')
        
        shiroko=db.get_database('shiroko')
        yield shiroko
    finally:
        LOGGER.debug('Closing database connection')
        db.close()


@contextmanager
def get_db_context_manager():
    host=os.getenv('DB_HOST') or 'localhost'
    port=os.getenv('DB_PORT') or 27017
    uri=f"mongodb://{host}:{port}"
    username=os.getenv('DB_USER')
    password=os.getenv('DB_PASSWORD')
    db=pymongo.MongoClient(uri,username=username,password=password)
    try:
        LOGGER.debug('Connected to the database succesufully')
        
        shiroko=db.get_database('shiroko')
        yield shiroko
    finally:
        LOGGER.debug('Closing database connection')
        db.close()





def get_collection(db : pymongo.database.Database,name : collection_names):
    return db.get_collection(name)
        

databaseDependency=t.Annotated[pymongo.database.Database,Depends(get_db)]