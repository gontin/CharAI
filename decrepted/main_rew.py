import asyncio
from dotenv import load_dotenv
import os
from PyCharacterAI import get_client
from PyCharacterAI.exceptions import SessionClosedError

load_dotenv()


token = os.getenv('CHAR_TOKEN')
character_id = 'Jdw61ZYHdRXCsuXQgTN7pnA4Hl9dnVcdJjwK_Bc8Yok'


async def main():
    client = await get_client(token=token)
    
    me = await client.account.fetch_me()
    print(f"Logado em @{me.username}")

    chat, greeting_message = await client.chat.create_chat(character_id)

    print(f"{greeting_message.author_name}: {greeting_message.get_primary_candidate().text}")

    try:
        while True:
            # NOTE: input() is blocking function!
            message = input(f"[{me.name}]: ")

            answer = await client.chat.send_message(character_id, chat.chat_id, message)
            print(f"[{answer.author_name}]: {answer.get_primary_candidate().text}")

    except SessionClosedError:
        print("session closed. Bye!")

    finally:
        # Don't forget to explicitly close the session
        await client.close_session()

asyncio.run(main())