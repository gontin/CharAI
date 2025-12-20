import discord
from discord.ext import commands, tasks, voice_recv
import time
import asyncio
import scipy.io.wavfile
import numpy as np
import speech_recognition as sr
import os
import io


class VoiceCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.user_buffers = {}

        self.ultimo_momento_fala_global = 0
        self.ocupado_processando = False

        self.amy_names = [" amy ", " eime ", " ami ", " aime ", " emmy ", " emi ", " m "]

        self.fiscal_de_silencio.start()

    def cog_unload(self):
        self.fiscal_de_silencio.stop()
        
    def transcrever (self, uid, audio_data):
        print("começou a transcrever")
        inicio = time.time()
        try:
            arq_memoria = io.BytesIO()
            data_np = np.frombuffer(audio_data, dtype=np.int32)
            scipy.io.wavfile.write(arq_memoria, 48000, data_np)
            arq_memoria.seek(0)
            
            rec = sr.Recognizer()
            
            with sr.AudioFile(arq_memoria) as source:
                audio = rec.record(source)  
            texto = rec.recognize_google(audio, language="pt-BR")
            print(f"terminou em {time.time()-inicio:.2f}")
            return (uid, texto)
        
        except Exception as e:
            print(f"Erro ao transcrever: {e}")
            
    @tasks.loop(seconds=1.0)
    async def fiscal_de_silencio(self):

        if not self.user_buffers:
            return
        if self.ocupado_processando:
            return

        agora = time.time()

        tempo_silencio = agora - self.ultimo_momento_fala_global

        if tempo_silencio > 2.5:
            total_bytes = 0
            for user_id in self.user_buffers:
                total_bytes += len(self.user_buffers[user_id])

            if total_bytes > 1000000:
                self.ocupado_processando = True
                
                buffers_copia = self.user_buffers.copy()
                self.user_buffers.clear()
                
                # temporario
                loop = asyncio.get_running_loop()
                tasks_transcrever = []
                for uid, audio_data in buffers_copia.items():
                    tasks_transcrever.append(
                        loop.run_in_executor(None, self.transcrever, uid, audio_data)
                    )
                result = await asyncio.gather(*tasks_transcrever)
                valid_result = [r for r in result if r is not None]
                for i in valid_result:
                    print(f"{i[0]} disse: {i[1]}")
                # 
                
                self.ocupado_processando = False

    @commands.command(name="call")
    async def conectar_voice(self, ctx):
        try:
            if ctx.author.voice:

                vc = await ctx.author.voice.channel.connect(cls=voice_recv.VoiceRecvClient, reconnect=True)
                vc.listen(voice_recv.BasicSink(self.callback))

                await ctx.send("entrandu")
            else:
                await ctx.send("não to vendo call nenhuma :<")

        except Exception as e:
            print(f"erro na conexão de voz: {e}")
            await self.desconectar_voice(ctx)

    @commands.command(name="sai")
    async def desconectar_voice(self, ctx):

        try:
            if ctx.voice_client:
                await ctx.voice_client.disconnect()
                await ctx.send("saindu")
            else:
                await ctx.send("m-mas eu nem to ai!")

        except Exception as e:
            print(f"erro na desconexão(???): {e}")

    def callback(self, user, data: voice_recv.VoiceData):
        try:
            if user is None or user.id == self.bot.user.id:
                return

            if self.bot.voice_clients and any(vc.is_playing() for vc in self.bot.voice_clients):
                return
            
            if user.id not in self.user_buffers:
                self.user_buffers[user.id] = b''

            self.user_buffers[user.id] += data.pcm

            self.ultimo_momento_fala_global = time.time()

        except Exception as e:
            print(f"errin: {e}")


async def setup(bot):
    await bot.add_cog(VoiceCog(bot))
