import asyncio
from bot import main as bot_main
from telethon_client import main as telethon_main

async def main():
    await asyncio.gather(
        bot_main(),
        telethon_main()
    )

if __name__ == "__main__":
    asyncio.run(main())
