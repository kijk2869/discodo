import threading

class Player(threading.Thread):
    def __init__(self, voice_client):
        threading.Thread(self)
        self.daemon = True

        self.client = voice_client
    
    