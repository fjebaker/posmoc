import random
import logging
import asyncio

import TTS.api

import pyaudio
import wave

import numpy as np

logger = logging.getLogger(__name__)


class AudioProcessor:
    def __init__(self, control):
        self.i = 0
        self.control = control

    def setup(self, all_chunks):
        chunks = [np.array(np.frombuffer(i, np.int16), np.float64) for i in all_chunks]

        def _measure(chunk):
            return np.sqrt(np.mean(np.square(chunk)))

        means = [_measure(i) for i in chunks]

        self.max = np.max(means)
        self.means = means

    def callback(self, i):
        if i % 4 == 0:
            mean = self.means[i]
            jaw = int(190 * (mean / self.max))
            self.control.write(jaw=jaw)


class Audio:
    def __init__(self):
        # first speaker is always the same
        self.tts = TTS.api.TTS(TTS.api.TTS.list_models()[0])
        self.speaker = 2
        self.language = "en"
        self.outfile = "latest.wav"

    async def speak(self, message: str, control):
        loop = asyncio.get_running_loop()
        file = await loop.run_in_executor(None, self._make_tts_file, message)

        proc = AudioProcessor(control)
        control.speaking = True
        await loop.run_in_executor(
            None, self._speak_from_file, file, proc.setup, proc.callback
        )
        control.speaking = False

    def random_speaker(self):
        self.speaker = random.randint(0, len(self.tts.speakers) - 1)
        logger.debug("Switched speaker to id = %s", self.speaker)

    def _make_tts_file(self, message: str) -> str:
        self.tts.tts_to_file(
            text=message,
            speaker=self.tts.speakers[self.speaker],
            language=self.language,
            file_path=self.outfile,
        )
        return self.outfile

    def _speak_from_file(self, file: str, setup_callback, callback, chunk: int = 512):
        audio = pyaudio.PyAudio()

        all_chunks = []
        with wave.open(file, "rb") as f:
            channels = f.getnchannels()
            rate = f.getframerate()
            samplewidth = f.getsampwidth()
            data = f.readframes(chunk)

            while data:
                all_chunks.append(data)
                data = f.readframes(chunk)

        stream = audio.open(
            format=audio.get_format_from_width(samplewidth),
            channels=channels,
            rate=rate,
            output=True,
        )

        if setup_callback:
            setup_callback(all_chunks)

        for i, data in enumerate(all_chunks):
            stream.write(data)
            if callback:
                callback(i)

        stream.stop_stream()
        stream.close()
