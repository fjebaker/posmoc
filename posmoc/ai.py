import os
import logging
import dataclasses
import asyncio

import nltk
import openai

import gpt4all

logger = logging.getLogger(__name__)
openai.api_key = os.environ.get("OPENAI_API_KEY")


@dataclasses.dataclass
class MessageChunk:
    _id: str
    content: str | None
    finish_reason: str | None


@dataclasses.dataclass
class Response:
    message: str
    action: int
    code: int


class _AI:
    def __init__(self):
        self.history = []

    async def fetch_response(self, prompt: str) -> Response:
        response = await self._assemble_response(prompt)
        return response

    async def _assemble_response(self, prompt: str) -> str:
        # add new prompt
        new_message = {
            "role": "user",
            "content": prompt,
        }
        # store prompt in conversation history
        self.history.append(new_message)

        response = await self._fetch_response(self.history)
        # trim the action
        response = response.strip()
        if len(response) > 3 and response[0] == "(" and response[2] == ")":
            try:
                action = int(response[1])
            except:
                logger.warning("Could not convert action: %s", response[1])
                action = 3
            response = response[3:]
        else:
            logger.warning("No action included. Defaulting to normal")
            action = 3

        response_trimmed = self._ensure_grammar(response)

        if response_trimmed:
            # store the response in the conversation history
            self.history.append({"role": "assistant", "content": response_trimmed})
        else:
            logger.debug("no response generated")
            action = 4
            response_trimmed = "Sorry, I didn't understand that."

        logger.info("AI: [[%d]] %s", action, response_trimmed)
        return Response(response_trimmed, action, 1)

    def _ensure_grammar(self, response: str) -> str:
        logger.debug("Full response: %s", response)
        tokens = nltk.tokenize.sent_tokenize(response)
        if (len(tokens) > 1) and (tokens[-1][-1] not in [".", "!", "?"]):
            tokens = tokens[:-1]
        return " ".join(tokens)


class GPT4All(_AI):
    def __init__(self):
        super().__init__()
        self.model = gpt4all.GPT4All("ggml-gpt4all-j-v1.3-groovy.bin")

    def _generate_from_messages(self, messages):
        response = self.model.chat_completion(messages, verbose=False, streaming=False)
        return response

    async def _fetch_response(self, messages) -> str:
        loop = asyncio.get_running_loop()
        response = await loop.run_in_executor(
            None, self._generate_from_messages, messages
        )
        logger.debug("gpt4all: %s", response)
        return response["choices"][0]["message"]["content"]


class OpenAI(_AI):
    def __init__(self):
        super().__init__()
        self.history.append(
            {
                "role": "system",
                # "content": "Keep your replies short. You are the master of ceremonies, who is eloquent, funny, and charasmatic. Begin each response with one of the following: 1. happy, 2. angry, 3. normal, 4. shake head, 5. roll eyes. Put the number is brackets before each response.",
                "content": "You are Al Capone. Respond in character, using phrases relevant to the 1920s."
            }
        )

    async def _fetch_response(self, messages) -> str:
        message = []
        try:
            async for chunk in self._stream_chunks(messages):
                if chunk.content:
                    message.append(chunk.content)
        except openai.error.ServiceUnavailableError:
            logger.error("openai api is unavailable")
            return "(4) I am not currently available to talk."
        return "".join(message)

    async def _stream_response(self, messages, max_tokens=100):
        response = await openai.ChatCompletion.acreate(
            model="gpt-3.5-turbo",
            messages=messages,
            n=1,
            max_tokens=max_tokens,
            temperature=0.0,
            stream=True,
        )
        return response

    async def _stream_chunks(self, messages, **kwargs):
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
