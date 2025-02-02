import pymongo
import os

import pymongo.database
import pymongo.errors
import typing as t
from fastapi import Depends,HTTPException
from shiroko.logger import *

    
    
def get_db():
    host=os.getenv('DB_HOST') or 'localhost'
    port=os.getenv('DB_PORT') or 27017
    uri=f"mongodb://{host}:{port}/"
    username=os.getenv('DB_USER')
    password=os.getenv('DB_PASSWORD')
    db=pymongo.MongoClient(uri,username=username,password=password)
    try:
        debug('Connected to the database succesufully')
        shiroko=db.get_database('shiroko')
        yield shiroko
    except Exception as e:
        critical(f'Could not connect to the database with the fallowing credentials:\n\n URI: {uri} \n Username: {username} \n Password: {password}')
        critical(e)
        raise HTTPException(500,detail={"message": "Failed to connect to the database"})
    finally:
        debug('Closing database connection')
        db.close()



colection_names=t.Literal['conversations']

def get_collection(db : pymongo.database.Database,name : colection_names):
    return db.get_collection(name)
        

databaseDependency=t.Annotated[pymongo.database.Database,Depends(get_db)]