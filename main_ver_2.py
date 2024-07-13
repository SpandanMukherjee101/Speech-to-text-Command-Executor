import queue
import sys

import pyautogui as pag

import pyttsx3

from google.api_core.client_options import ClientOptions
from google.cloud import speech

from pydub import AudioSegment
from pydub.playback import play

import pyaudio

RATE = 16000
CHUNK = int(RATE / 10)

class MicrophoneStream:

    def __init__(self: object, rate: int = RATE, chunk: int = CHUNK) -> None:
        self._rate = rate
        self._chunk = chunk
        self._buff = queue.Queue()
        self.closed = True

    def __enter__(self: object) -> object:
        self._audio_interface = pyaudio.PyAudio()
        self._audio_stream = self._audio_interface.open(
            format=pyaudio.paInt16,
            channels=1,
            rate=self._rate,
            input=True,
            frames_per_buffer=self._chunk,
            stream_callback=self._fill_buffer,
        )

        self.closed = False

        return self

    def __exit__(
        self: object,
        type: object,
        value: object,
        traceback: object,
    ) -> None:

        self._audio_stream.stop_stream()
        self._audio_stream.close()
        self.closed = True
        self._buff.put(None)
        self._audio_interface.terminate()

    def _fill_buffer(
        self: object,
        in_data: object,
        frame_count: int,
        time_info: object,
        status_flags: object,
    ) -> object:
        self._buff.put(in_data)
        return None, pyaudio.paContinue

    def generator(self: object) -> object:
        while not self.closed:
            chunk = self._buff.get()
            if chunk is None:
                return
            data = [chunk]

            while True:
                try:
                    chunk = self._buff.get(block=False)
                    if chunk is None:
                        return
                    data.append(chunk)
                except queue.Empty:
                    break

            yield b"".join(data)


def listen_print_loop(responses: object) -> str:
    play(AudioSegment.from_mp3("1.mp3"))

    b= 1
    b2= 0

    num_chars_printed = 0
    for response in responses:
        if not response.results:
            continue

        result = response.results[0]
        if not result.alternatives:
            continue

        transcript = result.alternatives[0].transcript

        overwrite_chars = " " * (num_chars_printed - len(transcript))

        if not result.is_final:
            sys.stdout.write(transcript + overwrite_chars + "\r")
            sys.stdout.flush()

            num_chars_printed = len(transcript)

        else:
            print(transcript + overwrite_chars)

            if b == 1:

                if transcript.strip()== "exit":
                    sys.exit()
                
                if transcript.strip()== "single click":
                    pag.click()

                elif transcript.strip()== "double click":
                    pag.doubleClick()
                
                elif transcript.strip()== "right click":
                    pag.click(button= "right")

                elif transcript[:9].strip()== "scroll up":
                    pag.scroll( int(transcript[10:].replace(",", "")))
                
                elif transcript[:11].strip()== "scroll down":
                    pag.scroll( -int(transcript[12:].replace(",", "")))

                elif transcript[:7].strip()== "move up":
                    pag.move( 0, -int(transcript.replace(" ", "").replace(",", "")), 0.5, pag.easeOutQuad)

                elif transcript[:9].strip()== "move down":
                    pag.move( 0, int(transcript.replace(" ", "").replace(",", "")), 0.5, pag.easeOutQuad)

                elif transcript[:10].strip()== "move right":
                    pag.move( int(transcript.replace(" ", "").replace(",", "")), 0, 0.5, pag.easeOutQuad)
                
                elif transcript[:9].strip()== "move left":
                    pag.move( -int(transcript.replace(" ", "").replace(",", "")), 0, 0.5, pag.easeOutQuad)

                elif transcript[:4].strip()== "type":
                    pag.write(transcript[5:].strip())

                elif transcript.strip()== "enter":
                    pag.press("enter")

                elif transcript.strip()== "escape":
                    pag.press("escape")

                elif transcript.strip()== "backspace" or transcript.strip()== "back space":
                    pag.press("backspace")

                elif transcript.strip()== "pause":
                    b= 0
                        
                elif transcript[:8].strip()== "up arrow":
                    i= int( transcript[9:].replace(" ", " "))
                    while(i):
                        pag.press("up")
                        i-=1
                    
                elif transcript[:10].strip()== "down arrow":
                    i= int( transcript[11:].replace(" ", " "))
                    while(i):
                        pag.press("down")
                        i-=1

                elif transcript[:11].strip()=="right arrow":
                    i= int( transcript.replace(" ", " "))        
                    while(i):
                        pag.press("right")
                        i-=1
                
                elif transcript[:10].strip()== "left arrow":
                    i= int( transcript.replace(" ", " "))
                    while(i):
                        pag.press("left")
                        i-=1

            elif b == 0:
                if transcript== "continue":
                    b2= 1

            if b2 == 1:
                b2= 0
                if transcript== "yes continue":
                    b= 1
            
            num_chars_printed = 0

    return transcript


def main() -> None:

    language_code = "en-US"

    client = speech.SpeechClient.from_service_account_file('Key.json')
    config = speech.RecognitionConfig(
        encoding=speech.RecognitionConfig.AudioEncoding.LINEAR16,
        sample_rate_hertz=RATE,
        language_code=language_code,
    )

    streaming_config = speech.StreamingRecognitionConfig(
        config=config, interim_results=True
    )

    with MicrophoneStream(RATE, CHUNK) as stream:
        audio_generator = stream.generator()
        requests = (
            speech.StreamingRecognizeRequest(audio_content=content)
            for content in audio_generator
        )

        responses = client.streaming_recognize(streaming_config, requests)

if __name__ == "__main__":
    main()