import logging
import asyncio

import speech_recognition

logger = logging.getLogger(__name__)


class SpeechRecognition:
    def __init__(self):
        self.speech = speech_recognition.Recognizer()
        self.microphone = speech_recognition.Microphone()
        with self.microphone as src:
            self.speech.adjust_for_ambient_noise(src)

    async def listen(self, on_done=None) -> None | str:
        loop = asyncio.get_running_loop()
        return await loop.run_in_executor(None, self._listen, on_done)

    def _listen(self, on_done):
        
        phrases = []
        def callback(r, audio):
            logger.info("Translating...")
            try:
                text = r.recognize_google(audio)
            except speech_recognition.exceptions.UnknownValueError:
                logger.error("UnknownValueError")
            else: 
                logger.info("Heard: '%s'", text)
                phrases.append(text)
        
        logger.info("Talk:")
        audio = self.speech.listen_in_background(self.microphone, callback)

        input("Hit ENTER to stop listening")
        logger.info("Stopped listening.")

        if on_done:
            on_done()

        # stop listening
        audio(wait_for_stop=True)
        
        text = (" ".join(phrases)).strip()
        if not text:
            return None
        return text
