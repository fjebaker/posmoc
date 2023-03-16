import asyncio
import posm

speaker = posm.Speaker()

loop = asyncio.get_event_loop()
try:
    # loop.run_until_complete(speaker.response_to_prompt("Introduce a speaker called Jacqueline for Pint of Science 2023 in Bristol, for a talk on the theme of machine learning and AI. Try to make it funny."))
    loop.run_until_complete(speaker.converse_loop())
finally:
    loop.run_until_complete(loop.shutdown_asyncgens())
    loop.close()

# from TTS.api import TTS


# tts_model = "tts_models/en/ljspeech/speedy-speech"
# for i in (TTS.list_models()):
#     print(i)
# exit(0)
# tts = TTS(tts_model, progress_bar = False)
# print(tts.speakers)

# import pydub
# import pydub.playback

# tts.tts_to_file(text="Hello World, this is the only way to do the thing you need to do today.", file_path="output.wav")
# song = pydub.AudioSegment.from_wav("output.wav")
# pydub.playback.play(song)