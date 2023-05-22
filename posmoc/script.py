import asyncio

# import posmoc
import sys

"""
script format:

comamnds to be put in `[[ CMD ARGS... ]]`

[[shakehead | lefteye 0b010 | eyetilt left | eyetilt middle]]

Hello, this is some text that the head will speak and sync.
"""


class Action:
    def __init__(self):
        self.text = ""
        self.action = Action._noaction
        self.action_args = ()
        self.speaker = None

    def __str__(self):
        s = ""
        if self.text:
            s += (
                "Text: "
                + self.text[0 : min(35, len(self.text))]
                + ("[...]" if 35 < len(self.text) else "")
            )

        if self.action != self._noaction:
            s += f"Action: {self.action} {self.action_args}"

        return s

    async def _noaction(self):
        ...

    @staticmethod
    def speech(text) -> "Action":
        self = Action()
        self.text = text
        return self

    @staticmethod
    def command(command, *args) -> "Action":
        self = Action()

        self.action = getattr(Action, "_" + command)
        self.action_args = args

        return self

    async def _rolleyes(self):
        ...

    async def _eyes(self):
        ...

    async def _turnhead(self):
        direction = self.action_args[0]
        if direction == "left":
            angle = 0
        elif direction == "middle":
            angle = 50
        else:
            angle = 100
        self.speaker.head.write(head = angle)

    async def _waitforinput(self):
        input("Waiting to continue...")

    async def _sleep(self):
        await asyncio.sleep(int(self.action_args[0]))

    async def speaktext(self):
        await self.speaker.audio.speak(self.text, self.speaker.head)

    async def execute(self, speaker):
        self.speaker = speaker
        await self.action(self)
        if self.text:
            await self.speaktext()


def parse_script(text):
    # get rid of empty lines
    text = [i.strip() for i in text if i.strip()]

    actions = []
    for line in text:
        if line[0] == '#':
            continue 

        if line[0] == "[" and line[1] == "[":
            # parse command
            args = [i.strip() for i in line[2:-2].split() if i.strip()]
            actions.append(Action.command(*args))
        else:
            # text to speak
            actions.append(Action.speech(line))

    return actions

async def runactions(speaker, actions: list[Action]):
    for action in actions:
        await action.execute(speaker)

async def runscript(speaker, file):
    with open(file, "r") as f:
        text = f.readlines()

    actions = parse_script(text)
    for action in actions:
        print(action)
    
    input("Script ready: press Enter to start")
    await speaker.startidle()
    await runactions(speaker, actions)
