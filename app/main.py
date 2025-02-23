from typing import Union

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.routes import main_router
from app.settings import *
from bson import ObjectId
import os
app = FastAPI(debug=True,redirect_slashes=False,title='Shiroko Backend')




app.add_middleware(CORSMiddleware,allow_origins=ORIGINS,allow_methods=METHODS,max_age=MAX_AGE,allow_headers=['*'])
app.include_router(main_router)




