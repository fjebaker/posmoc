import asyncio 
import posmoc
from posmoc.script import runscript
import sys

if __name__ == "__main__":
    speaker = posmoc.Speaker()
    loop = asyncio.get_event_loop()
    try:
        loop.run_until_complete(runscript(speaker, sys.argv[2]))
    finally:
        loop.run_until_complete(loop.shutdown_asyncgens())
        loop.close()
