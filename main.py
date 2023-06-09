import logging

import asyncio
import posmoc

from posmoc.script import runscript

def script(speaker, file):
    loop = asyncio.get_event_loop()
    try:
        loop.run_until_complete(runscript(speaker, file))
    finally:
        loop.run_until_complete(loop.shutdown_asyncgens())
        loop.close()



if __name__ == "__main__":
    speaker = posmoc.Speaker()
    print("SETUP COMPLETE\n\n")
    while True:
        print("1: introduction")
        print("2: nathan")
        print("3: robbie")
        print("4: safety")

        inp = input("select > ")

        try:
            inp = int(inp)
        except:
            print("Bad input")
        else:
            if inp == 1:
                script(speaker, "ai-ml/introduction.txt")
            elif inp == 2:
                script(speaker, "ai-ml/nathan.txt")
            elif inp == 3:
                script(speaker, "ai-ml/robbie.txt")
            elif inp == 4:
                script(speaker, "ai-ml/safety.txt")
