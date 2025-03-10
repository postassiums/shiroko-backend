
from app.services.consumer import *
from dotenv import load_dotenv
import sys
import os
from datetime import datetime
import logging




def setup_logging(name : str=__name__):
    log_directory='static/logs'
    if not(os.path.exists(log_directory)):
        os.makedirs(log_directory)
    current_date=datetime.now().strftime('%d-%m-%Y')
    file_name=f'consumer-{current_date}.log'
    output_path=os.path.join(log_directory,file_name)
    logging.basicConfig(
    level=logging.INFO,  # Set the logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',  # Define the log format
    handlers=[
        logging.FileHandler(output_path),  # Log to a file
        logging.StreamHandler()  # Also log to the console (optional)
    ])
    
    return logging.getLogger(name)
    



def main():
    load_dotenv('.env')
    
    arguments = sys.argv
    if arguments.__len__() > 2:
        raise RuntimeError('You must provide only one argument')
    argument = arguments[1]
    
    if argument == 'tts':
        with TTSConsumer() as consumer:
            consumer.logger.info('Starting Consuming TTS Queue')
            consumer.consume()
    elif argument == 'tts_splitter':
        with TTSSplitConsumer() as consumer:
            consumer.logger.info('Starting Consuming TTS Split Queue')
            consumer.consume()
    elif argument=='rvc':
        with RVCConsumer() as consumer:
            consumer.logger.info('Starting consuming RVC Queue')
            consumer.consume()
    else:
        raise RuntimeError('Invalid argument')
 


if __name__=='__main__':
    logger=setup_logging()
    try:
        main()
    except KeyboardInterrupt:
        logger.info('Exiting Consumer Program')

        sys.exit(0)


