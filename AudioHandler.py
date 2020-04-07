import pyaudio
import time

class AudioHandler:
    FORMAT = pyaudio.paInt16
    CHANNELS = 2
    RATE = 44100
    RECORD_SECONDS = 5
    BUFFER_SIZE = 1024

    def __init__(self):
        self.input_device = pyaudio.PyAudio()
        self.input_src = \
            self.input_device.open(format=AudioHandler.FORMAT,
                                    channels=AudioHandler.CHANNELS,
                                    rate=AudioHandler.RATE,
                                    input=True,
                                    frames_per_buffer=AudioHandler.BUFFER_SIZE)
        

        self.output_src = \
            self.input_device.open(format=AudioHandler.FORMAT,
                                    channels=AudioHandler.CHANNELS,
                                    rate=AudioHandler.RATE,
                                    output=True,
                                    frames_per_buffer=AudioHandler.BUFFER_SIZE)
    def get_audio(self):
        return self.input_src.read(AudioHandler.BUFFER_SIZE)
    
    def play_audio(self,data):
        self.output_src.write(data)
        
        

def test():

    h = AudioHandler() 
    print("Geting audio")

    while True:
        data = h.get_audio()
        h.play_audio(data)

if __name__ == "__main__":
    test()
