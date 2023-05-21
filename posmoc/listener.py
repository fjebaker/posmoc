import logging
import asyncio

import speech_recognition

logger = logging.getLogger(__name__)


class SpeechRecognition:
    def __init__(self):
        self.speech = speech_recognition.Recognizer()

    async def listen(self, on_done=None) -> None | str:
        loop = asyncio.get_running_loop()
        return await loop.run_in_executor(None, self._listen, on_done)

    def _listen(self, on_done):
        with speech_recognition.Microphone() as src:
            logger.info("Talk:")
            audio = self.speech.listen(src, phrase_time_limit=15)
        if on_done:
            on_done()
        logger.info("Translating...")
        try:
            text = self.speech.recognize_google(audio)
        except speech_recognition.exceptions.UnknownValueError:
            return None
        logger.info("Heard: " + text)
        return text
