FROM python:3.10.14 as backend



WORKDIR /app

COPY requirements.txt .
COPY . .

RUN pip3 install torch==2.1.1+cu118 torchaudio==2.1.1+cu118 --index-url https://download.pytorch.org/whl/cu118

RUN pip3 install -r requirements.txt 

ENTRYPOINT pip3 install -r requirements.txt && python3 -Xfrozen_modules=off .




