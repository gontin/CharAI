import discord
import json
import asyncio
import scipy
from characterai import aiocai
from discord.ext import commands, voice_recv
import numpy as np
from scipy.signal import resample
import subprocess
import wave
import speech_recognition as sr
import pyttsx3
import io
from dotenv import load_dotenv
import os

load_dotenv()

CHAR_TOKEN = os.getenv('CHAR_TOKEN')
DISCORD_TOKEN = os.getenv('DISCORD_TOKEN')

intents = discord.Intents.default()
intents.message_content = True
intents.voice_states = True
discord.opus._load_default()
history_audio = b''

engine = pyttsx3.init()

# configs globais
# model = vosk.Model(model_path="C:\wosk-model-small-pt-0.3")
# char_id = 'f_0wvFomHhJJJRYrwgtyeCLt-ny8SbDQrDk0kPkAtms'
char_id = 'Jdw61ZYHdRXCsuXQgTN7pnA4Hl9dnVcdJjwK_Bc8Yok' # character ai id
historico = "data/histchar.json"

def transcrever_audio_speechrecognition(audio_path):
    recognizer = sr.Recognizer()
    with sr.AudioFile(audio_path) as source:
        audio = recognizer.record(source)  
    texto = recognizer.recognize_google(audio, language="pt-BR")
    return texto
        
class Quantiu(discord.Client):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.ca_client = aiocai.Client(CHAR_TOKEN)
        self.chat_id = None
        self.historico_conversa = self.ler_historico()
        self.voice_client = None

    def ler_historico(self):
        try:
            with open(historico, 'r', encoding='utf-8') as e:
                return json.load(e)
        except (FileNotFoundError, json.JSONDecodeError):
            return []

    def salvar_historico(self):
        with open(historico, 'w', encoding='utf-8') as f:
            json.dump(self.historico_conversa, f, ensure_ascii=False, indent=4)

    async def on_ready(self):
        me = await self.ca_client.get_me()
        async with await self.ca_client.connect() as chat:
            new, answer = await chat.new_chat(char_id, me.id)
            self.chat_id = new.chat_id
            print(f'{answer.name}: {answer.text}')
            print(f'{self.user} esta onfire')
    
    async def on_message(self, mensagem):
        if mensagem.author == self.user:
            return

        if mensagem.content.startswith("entrai"):
            await self.conectar_voice(mensagem)
            
        elif mensagem.content.startswith("sai"):
            await self.desconectar_voice(mensagem)
            
        elif mensagem.channel.name in ("geral"):
            await self.processar_mensagem(
                mensagem.content,
                mensagem.channel,
                mensagem.author
            )

    async def processar_mensagem(self, texto, canal, autor):
        try:
            async with await self.ca_client.connect() as chat:
                resposta = await chat.send_message(char_id, self.chat_id, f'{autor.display_name} disse: {texto}')
                
                self.historico_conversa.append({
                    "role": autor.name,
                    "content": texto
                })
                
                self.historico_conversa.append({
                    "role": self.user.name,
                    "content": resposta.text
                })
                
                self.salvar_historico()
                await canal.send(resposta.text)
                return resposta.text
                
        except Exception as e:
            print(f"erro no character.ai: {e}")
            return None
        
    async def processar_mensagem_voz(self, texto, autor):
        try:
            async with await self.ca_client.connect() as chat:
                resposta = await chat.send_message(char_id, self.chat_id, texto)
                
                self.historico_conversa.append({
                    "role": autor,
                    "content": texto
                })
                
                self.historico_conversa.append({
                    "role": self.user.name,
                    "content": resposta.text
                })
                
                self.salvar_historico()
                return resposta.text
                
        except Exception as e:
            print(f"erro no character.ai voz: {e}")
            return None
    async def msgmandar(self, msg, canal):
        await canal.send(msg)
    async def conectar_voice(self, mensagem):
        try:
            if mensagem.author.voice:
                def callback(user, data: voice_recv.VoiceData):
                    try:
                        global history_audio
                        audio = data.pcm
                        history_audio += audio
                        
                        if len(history_audio) > 1000000:
                            tmp_audio = history_audio
                            history_audio = b''
                            
                            audio_data = np.frombuffer(tmp_audio, dtype=np.int32, offset=0)
                            sample_rate = 48000

                            scipy.io.wavfile.write(f'./voice_data/recoding.wav', sample_rate, audio_data)

                            # audio para texto
                            txt = transcrever_audio_speechrecognition('./voice_data/recoding.wav')
                    
                            print(txt)

                            # passando pela llm
                            resposta = asyncio.run(self.processar_mensagem_voz(txt, "call"))

                            print(resposta)
                            
                            # texto para audio
                            engine.save_to_file(resposta, './voice_data/output.mp3')
                            engine.runAndWait()
            
                            if self.voice_client and self.voice_client.is_connected():
                                # tocando
                                fonte = discord.FFmpegPCMAudio("./voice_data/output.mp3")
                                self.voice_client.play(fonte)
                            else:
                                print("O bot não está conectado a um canal de voz.")
                    except Exception as e:
                        print(f"errin: {e}")
                        
                self.voice_client = await mensagem.author.voice.channel.connect(cls=voice_recv.VoiceRecvClient, reconnect = True)
                self.voice_client.listen(voice_recv.BasicSink(callback))
                        
                await mensagem.channel.send("entrei na call dog")
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

client = Quantiu(intents=intents)
client.run(DISCORD_TOKEN)