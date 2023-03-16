import os
import dataclasses
import typing
import logging

import TTS.api
import openai

import pyaudio
import wave

import nltk

import speech_recognition

logger = logging.getLogger(__name__)
openai.api_key = os.environ.get("OPEN_AI_API_KEY")


@dataclasses.dataclass
class MessageChunk:
    _id: str
    content: typing.Union[str, None]
    finish_reason: typing.Union[str, None]


class Speaker:
    def __init__(self):
        self.tts = TTS.api.TTS(TTS.api.TTS.list_models()[0])
        self.outfile = "output.wav"
        self.speaker = 2
        self.language = "en"
        self.speech = speech_recognition.Recognizer()
        self.audio = pyaudio.PyAudio()
        self.history = [
            {
                "role": "system",
                "content": "Keep your replies short and try to sound like Max Headroom.",
            }
        ]

    def make_tts_file(self, message: str) -> str:
        self.tts.tts_to_file(
            text=message,
            speaker=self.tts.speakers[self.speaker],
            language=self.language,
            file_path=self.outfile,
        )
        return self.outfile

    def speak_from_file(self, file: str, chunk: int = 1024):
        with wave.open(file, "rb") as f:
            stream = self.audio.open(
                format=self.audio.get_format_from_width(f.getsampwidth()),
                channels=f.getnchannels(),
                rate=f.getframerate(),
                output=True,
            )
            data = f.readframes(chunk)

            while data:
                stream.write(data)
                data = f.readframes(chunk)
            stream.stop_stream()
            stream.close()

    async def speak(self, message: str):
        file = self.make_tts_file(message)
        self.speak_from_file(file)

    async def respond_to_prompt(self, prompt: str):
        response = await self.assemble_response(prompt)
        await self.speak(response)

    async def assemble_response(self, prompt: str) -> str:
        # add new prompt
        new_message = {
            "role": "user",
            "content": prompt,
        }
        self.history.append(new_message)
        response = await self.fetch_response(self.history)
        response_trimmed = self.ensure_grammar(response)
        self.history.append({"role": "assistant", "content": response_trimmed})

        logger.info("AI: %s", response_trimmed)
        return response_trimmed

    def ensure_grammar(self, response: str) -> str:
        logger.debug("Full response: %s", response)
        tokens = nltk.tokenize.sent_tokenize(response)
        if (len(tokens) > 1) and (tokens[-1][-1] not in [".", "!", "?"]):
            tokens = tokens[:-1]
        return " ".join(tokens)

    async def fetch_response(self, messages) -> str:
        message = []
        try:
            async for chunk in self.stream_response(messages):
                if chunk.content:
                    message.append(chunk.content)
        except openai.error.ServiceUnavailableError:
            return "I am not currently available to talk."
        return "".join(message)

    async def _stream_response(self, messages, max_tokens=40):
        response = await openai.ChatCompletion.acreate(
            model="gpt-3.5-turbo",
            messages=messages,
            n=1,
            max_tokens=max_tokens,
            temperature=0.0,
            stream=True,
        )
        return response

    async def stream_response(self, messages, **kwargs):
        async for chunk in await self._stream_response(messages, **kwargs):
            _id = chunk["id"]
            choice = chunk["choices"][0]
            if "role" in choice["delta"]:
                continue
            finish = choice["finish_reason"]
            if finish:
                content = None
            else:
                content = choice["delta"]["content"]
            yield MessageChunk(_id, content, finish)

    async def listen(self) -> typing.Union[None, str]:
        with speech_recognition.Microphone() as src:
            logger.info("Talk:")
            audio = self.speech.listen(src, phrase_time_limit=15)
            logger.info("Translating...")
        try:
            text = self.speech.recognize_google(audio)
        except speech_recognition.exceptions.UnknownValueError:
            return None
        logger.info("Heard: " + text)
        return text

    async def converse(self):
        prompt = await self.listen()
        if prompt:
            await self.respond_to_prompt(prompt)
        else:
            await self.speak("Please speak again.")

    async def converse_loop(self):
        await self.speak("I am now ready to talk.")

        while True:
            await self.converse()
