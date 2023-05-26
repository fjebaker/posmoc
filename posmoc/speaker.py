import typing
import logging
import sys
import asyncio

from posmoc.ai import OpenAI, GPT4All
from posmoc.audio import Audio
from posmoc.listener import SpeechRecognition
from posmoc.serial import HeadControl

logger = logging.getLogger(__name__)


class Speaker:
    def __init__(self):
        #self.ai = GPT4All()
        self.ai = OpenAI()
        self.audio = Audio()
        self.listener = SpeechRecognition()
        self.head = HeadControl(sys.argv[1])
        self.idling = False

    async def respond_to_prompt(self, prompt: str):
        loop = asyncio.get_event_loop()
        # set thinking animation going
        task = loop.create_task(self.head.set_thinking())

        response = await self.ai.fetch_response(prompt)
        # cancel thinking
        task.cancel()

        await self.audio.speak(
            response.message,
            self.head,
        )

    async def converse(self):
        self.head.write(lefteye=0b010, righteye=0b010)
        prompt = await self.listener.listen(
            lambda: self.head.write(lefteye=0b100, righteye=0b100)
        )

        if prompt:
            await self.respond_to_prompt(prompt)
        else:
            await self.audio.speak("Please speak again.", self.head)
        self.audio.random_speaker()

    async def startidle(self):
        if not self.idling:
            logger.info("Starting idling")
            loop = asyncio.get_event_loop()
            loop.create_task(self.head.start_idle())
            self.idling = True

    async def converse_loop(self):
        await self.startidle()
        await self.audio.speak("I am now ready to talk.", self.head)
        while True:
            await self.converse()
