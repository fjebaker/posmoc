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
        self.action = self._noaction
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

    def _noaction(self):
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

    def _rolleyes(self):
        ...

    def _eyes(self):
        ...

    def _sleep(self):
        ...

    def _speaktext(self):
        ...

    async def execute(self, speaker):
        self.speaker = speaker
        self.action()
        self.speaktext()


def parse_script(text):
    # get rid of empty lines
    text = [i.strip() for i in text if i.strip()]

    actions = []
    for line in text:
        if line[0] == "[" and line[1] == "[":
            # parse command
            args = line[2:-2].split()
            actions.append(Action.command(*args))
        else:
            # text to speak
            actions.append(Action.speech(line))

    return actions

async def runactions(actions: list[Action]):
    speaker = posmoc.Speaker()
    for action in actions:
        await action.execute(speaker)

if __name__ == "__main__":
    inp = sys.stdin.readlines()
    actions = parse_script(inp)

    print("Parsed script:")
    for action in actions:
        print(action)

    loop = asyncio.get_event_loop()
    try:
        loop.run_until_complete(runactions(actions))
    finally:
        loop.run_until_complete(loop.shutdown_asyncgens())
        loop.close()
