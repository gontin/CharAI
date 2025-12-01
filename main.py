import discord
import json
from discord.ext import commands, voice_recv
from dotenv import load_dotenv
import os
import scipy
import numpy as np

from PyCharacterAI import get_client
from PyCharacterAI.exceptions import SessionClosedError

from CharacterManager import CharacterManager

load_dotenv()

# configs globais
CHAR_TOKEN = os.getenv('CHAR_TOKEN')
DISCORD_TOKEN = os.getenv('DISCORD_TOKEN')
CHAR_ID = 'hPIEsrcL-qyxS6bNjEQIsTDcT-DQA7vouIs7t9ccqJ0' # character ai id

intents = discord.Intents.default()
intents.message_content = True
intents.voice_states = True
discord.opus._load_default()

# char_id = 'f_0wvFomHhJJJRYrwgtyeCLt-ny8SbDQrDk0kPkAtms'
historico = "data/histchar.json"

        
class Disc_Bot(discord.Client):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.client = None
        self.chat = None

        self.char_ai = CharacterManager(CHAR_TOKEN, CHAR_ID)

        self.historico_conversa = self.ler_historico()

        self.user_buffers = {}
        self.voice_client = None

    async def on_ready(self):
        self.char_ai.iniciar()


    def callback(self, user, data: voice_recv.VoiceData):
        try:
            if user == None:
                return
            
            if user.id not in self.user_buffers:
                self.user_buffers[user.id] = b''
            self.voice_client.is_listening()
            
            self.user_buffers[user.id] += data.pcm

            audio_call = 


        except Exception as e:
            print(f"errin: {e}")


    async def conectar_voice(self, mensagem):
        try:
            if mensagem.author.voice:
                        
                self.voice_client = await mensagem.author.voice.channel.connect(cls=voice_recv.VoiceRecvClient, reconnect = True)
                self.voice_client.listen(voice_recv.BasicSink(self.callback))
                
                await mensagem.channel.send("entrei na call dog")
            else:
                await mensagem.channel.send("q call vei, seu bobo")

        except Exception as e:
            print(f"erro na conexão de voz: {e}")
            await self.desconectar_voice(mensagem)
            
    async def desconectar_voice(self, mensagem):
        try:
            if self.voice_client.is_connected():
                await self.voice_client.disconnect()
                await mensagem.channel.send("tabein")
            else:
                await mensagem.channel.send("nem em call eu to dog")
            
        except Exception as e:
            print(f"erro na desconexão: {e}")


    def ler_historico(self):
        try:
            with open(historico, 'r', encoding='utf-8') as e:
                return json.load(e)
        except (FileNotFoundError, json.JSONDecodeError):
            return []

    def salvar_historico(self):
        with open(historico, 'w', encoding='utf-8') as f:
            json.dump(self.historico_conversa, f, ensure_ascii=False, indent=4)
    
    async def on_message(self, mensagem):
        if mensagem.author == self.user:
            return

        if mensagem.content.startswith("entrai"):
            await self.conectar_voice(mensagem)
            
        elif mensagem.content.startswith("sai"):
            await self.desconectar_voice(mensagem)
            
        elif mensagem.channel.name in ("geral"):
            await self.char_ai_msg(
                mensagem.content,
                mensagem.author,
                mensagem.channel
            )

    async def char_ai_msg(self, texto, autor, canal):
        try:
        
            resposta = await self.char_ai.enviar_mensagem(texto, autor.name)
            
            self.historico_conversa.append({
                "role": autor.name,
                "content": texto
            })
            
            self.historico_conversa.append({
                "role": self.user.name,
                "content": resposta
            })
            
            self.salvar_historico()
            await canal.send(resposta)
            return resposta
        except Exception as e:
            print(f"erro no character.ai: {e}")
            return None
        


client = Disc_Bot(intents=intents)
client.run(DISCORD_TOKEN)