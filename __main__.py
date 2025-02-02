import uvicorn
from shiroko.main import app
from dotenv import load_dotenv
import os

if __name__=='__main__':
    load_dotenv()
    port=int(os.getenv('PORT'))
    uvicorn.run('shiroko.main:app',port=port,host='0.0.0.0',access_log=False,use_colors=True,reload=True,reload_dirs=['shiroko/'])