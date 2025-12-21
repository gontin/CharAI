import discord
import json
from discord.ext import commands, voice_recv, tasks
from dotenv import load_dotenv
import os
import scipy
import numpy as np
import time
import asyncio

from PyCharacterAI import get_client
from PyCharacterAI.exceptions import SessionClosedError

from services.CharacterManager import CharacterManager

load_dotenv()

# configs globais
CHAR_TOKEN = os.getenv('CHAR_TOKEN')
DISCORD_TOKEN = os.getenv('DISCORD_TOKEN')
CHAR_ID = 'hPIEsrcL-qyxS6bNjEQIsTDcT-DQA7vouIs7t9ccqJ0'  # character ai id

discord.opus._load_default()

# char_id = 'f_0wvFomHhJJJRYrwgtyeCLt-ny8SbDQrDk0kPkAtms'
historico = "data/histchar.json"


class Disc_Bot(commands.Bot):
    def __init__(self):

        intents = discord.Intents.default()
        intents.message_content = True
        intents.voice_states = True
        super().__init__(command_prefix="!", intents=intents, help_command=None)

        self.char_ai = CharacterManager(CHAR_TOKEN, CHAR_ID)

        self.historico_conversa = self.ler_historico()
        self.active_tasks = set()
        self.disponivel = True
        async def reboot_wrapper(ctx):
            await self.reboot(ctx)
        self.add_command(commands.Command(reboot_wrapper, name="reboot"))

    async def setup_hook(self):
        print("carregando cogs")
        try:
            await self.load_extension("cogs.voice_cog")
        except Exception as e:
            print(f"Errin ao carregar cog de voz: {e}")
        return await super().setup_hook()

    async def on_ready(self):
        try:

            await self.char_ai.iniciar()
            print("oiii, estou funcionando")
        except Exception as e:
            print(f"Erro: {e}")

    def ler_historico(self):
        try:
            with open(historico, 'r', encoding='utf-8') as e:
                return json.load(e)
        except (FileNotFoundError, json.JSONDecodeError):
            return []

    def salvar_historico(self):
        with open(historico, 'w', encoding='utf-8') as f:
            json.dump(self.historico_conversa, f, ensure_ascii=False, indent=4)

    async def on_message(self, message):
        if message.author == self.user:
            return

        await self.process_commands(message)

        if message.channel.name == "amy" and not message.content.startswith(self.command_prefix):
            if self.disponivel:
                task = asyncio.create_task(self.char_ai_msg(message.content, message.author, message.channel))
                self.active_tasks.add(task)
                task.add_done_callback(self.active_tasks.discard)
        
    async def reboot(self, ctx):
        print("rebootando...")
        await ctx.send("AAAaAaAAaAaAaAaAaaAAAAAAAAAA")
        await self.char_ai.reboot()
        
    async def char_ai_msg(self, texto, autor, canal):
        try:

            self.disponivel = False
            async with canal.typing():
                resposta = await self.char_ai.enviar_mensagem(f"{autor.display_name} disse: {texto}")
            self.historico_conversa.append({
                "role": autor.display_name,
                "content": texto
            })

            self.historico_conversa.append({
                "role": self.user.name,
                "content": resposta
            })

            self.salvar_historico()
            await canal.send(resposta)
            self.disponivel = True
            return resposta
        except Exception as e:
            print(f"erro no character.ai: {e}")
            return None


if __name__ == "__main__":
    bot = Disc_Bot()
    bot.run(DISCORD_TOKEN)
