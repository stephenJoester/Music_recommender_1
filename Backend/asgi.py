import uvicorn 
import sys
import signal

def signal_handler(sig, frame):
    print('Exiting application...')
    sys.exit(0)

if __name__ == "__main__" : 
    signal.signal(signal.SIGINT, signal_handler)
    uvicorn.run("main:app", port=8000, workers=4)