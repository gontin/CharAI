import discord
from discord.ext import commands, tasks, voice_recv
import time
import asyncio
import scipy.io.wavfile
import numpy as np
import speech_recognition as sr
import os
import io
from vosk import Model, KaldiRecognizer
import json
import re


class VoiceCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        
        self.active_buffers = {}
        self.buffer_metadata = {}
        self.speech_queue = []
        
        self.user_names = {}

        self.ultimo_momento_fala_global = 0
        self.vc = None
        self.ocupado_processando = False
        
        self.PAUSA_INDIVIDUAL = 0.6
        self.SILENCIO_GLOBAL = 1.2
        
        self.fiscal_de_silencio.start()

        # self.vosk_model = Model("model")

    def cog_unload(self):
        self.fiscal_de_silencio.stop()

    def transcrever(self, uid, audio_data):
        inicio = time.time()
        if self.vc:
            if self.vc.is_connected():
                self.vc.stop_listening()
        try:
            arq_memoria = io.BytesIO()
            data_np = np.frombuffer(audio_data, dtype=np.int32).astype(np.int16)

            # RECOGNIZER DO GOOGLE
            scipy.io.wavfile.write(arq_memoria, 48000, data_np)
            arq_memoria.seek(0)

            rec = sr.Recognizer()

            with sr.AudioFile(arq_memoria) as source:
                audio = rec.record(source)
                
            try:
                
                texto = rec.recognize_google(audio, language="pt-BR")
                print(f"terminou em {time.time()-inicio:.2f}")
                return(uid, texto)
            except sr.UnknownValueError:
                print("n tendi...")
                return None
            except sr.RequestError:
                print("recog do google deu ruim")
                return None

        except Exception as e:
            print(f"Erro ao transcrever: {e}")

    async def processar_voz(self):
        if self.vc and self.vc.is_connected():
            self.vc.stop_listening()
            
        inicio = time.time()
        try:
            fila_para_processar = self.speech_queue.copy()
            self.speech_queue.clear()
            
            fila_para_processar.sort(key=lambda x: x['time'])
            
            loop = asyncio._get_running_loop()
            tasks_transcrever = []
            
            for item in fila_para_processar:
                tasks_transcrever.append(loop.run_in_executor(None, self.transcrever, item['uid'], item['audio']))
                
            results = await asyncio.gather(*tasks_transcrever)
            
            msg_final = ""
            
            for res in results:
                if res and res[1]:
                    uid, texto = res
                    nome = self.user_names.get(uid, f"User")
                    msg_final += f"{nome} disse: {texto}\n"
                    print(f"{nome}: {texto}")
                    
            if not msg_final.strip():
                print("tendi porra nenhuma")
                if self.vc and self.vc.is_connected():
                    self.vc.listen(voice_recv.BasicSink(self.callback))
                return
            
            print("mandando pra amyzinha...")
            resposta = await self.bot.char_ai.enviar_mensagem(msg_final)
            print(f"Amy: {resposta}")
            
            audio_bytes = None
            for _ in range(2):
                audio_bytes = await self.bot.char_ai.gerar_voz(os.getenv("CHAR_VOZID"))
                if audio_bytes: break
                await asyncio.sleep(1)
                
            if audio_bytes:
                caminho_resp = "./data/temp/resposta_ia.mp3"
                os.makedirs(os.path.dirname(caminho_resp), exist_ok=True)
                with open(caminho_resp, "wb") as f:
                    f.write(audio_bytes)
                
                if self.vc and self.vc.is_connected():
                    if self.vc.is_playing(): self.vc.stop()
                    
                    self.vc.play(discord.FFmpegPCMAudio(caminho_resp))
                    
                    while self.vc.is_playing():
                        await asyncio.sleep(0.5)
            print(f"\nprocessamento de audio feito em {time.time()-inicio:.2f}s")
            
        except Exception as e:
            print(f"Erro ao processar voz: {e}")
            
        finally:
            if self.vc and self.vc.is_connected() and not self.vc.is_listening():
                print("ouvindo dnv..")
                self.vc.listen(voice_recv.BasicSink(self.callback))
                

    @tasks.loop(seconds=0.2)
    async def fiscal_de_silencio(self):
        if self.ocupado_processando: return
        
        agora = time.time()
        
        for uid in list(self.active_buffers.keys()):
            meta = self.buffer_metadata[uid]
            
            if (agora - meta['last_packet']) > self.PAUSA_INDIVIDUAL:
            
                audio_content = self.active_buffers.pop(uid)
                start_time = meta['start_time']
                del self.buffer_metadata[uid]
                
                if len(audio_content) > 15000:
                    self.speech_queue.append({
                        'uid': uid,
                        'audio': audio_content,
                        'time': start_time
                    })
        
        tempo_silencio_global = agora - self.ultimo_momento_fala_global
        
        if self.speech_queue and tempo_silencio_global > self.SILENCIO_GLOBAL:
            if not self.active_buffers:
                self.ocupado_processando = True
                await self.processar_voz()
                self.ocupado_processando = False
                

    @commands.command(name="call")
    async def conectar_voice(self, ctx):
        if not ctx.author.voice:
            await ctx.send("mai c n ta em call >:0")
            return
        try:
            if self.vc: await self.desconectar_voice(ctx)
            self.vc = await ctx.author.voice.channel.connect(cls=voice_recv.VoiceRecvClient, reconnect=True)
            self.bot.disponivel = False
            self.vc.listen(voice_recv.BasicSink(self.callback))
            await ctx.send("oky")
        except Exception as e:
            print(f"Erro na call: {e}")

    @commands.command(name="sai")
    async def desconectar_voice(self, ctx):
        if ctx.voice_client:
            await ctx.voice_client.disconnect()
            self.vc = None
            self.bot.disponivel = True
            await ctx.send("saindu..")


    def callback(self, user, data: voice_recv.VoiceData):
        try:
            if not user or user.id == self.bot.user.id: return
            if self.vc and self.vc.is_playing(): return
            if self.ocupado_processando: return
            
            agora = time.time()
            uid = user.id
            
            if uid not in self.active_buffers:
                self.active_buffers[uid] = bytearray()
                self.buffer_metadata[uid] = {
                    'start_time' : agora,
                    'last_packet' : agora
                }
                self.user_names[uid] = user.display_name

            self.active_buffers[uid].extend(data.pcm)
            self.buffer_metadata[uid]['last_packet'] = agora
            self.ultimo_momento_fala_global = agora

        except Exception as e:
            print(f"errin: {e}")


async def setup(bot):
    await bot.add_cog(VoiceCog(bot))
