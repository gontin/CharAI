import discord
from discord.ext import commands, tasks, voice_recv
import time
import asyncio
import scipy.io.wavfile
import numpy as np
import speech_recognition as sr
import os

class VoiceCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.user_buffers = {}
        
        self.ultimo_momento_fala_global = 0
        self.ocupado_processando = False
        
        self.amy_names = ["amy", "eime", "ami", "aime", "emmy", "emi"]
        
        self.fiscal_de_silencio.start()
    
    def cog_unload(self):
        self.fiscal_de_silencio.stop()
        
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
                meus_buffers_copia = self.user_buffers.copy()
                self.user_buffers.clear()

                print("eu falaria agora se pudesse mas sou burra")
                self.ocupado_processando = False
    
  
    @commands.command(name="call")
    async def conectar_voice(self, ctx):
        try:
            if ctx.author.voice:

                vc = await ctx.author.voice.channel.connect(cls=voice_recv.VoiceRecvClient, reconnect=True)
                vc.listen(voice_recv.BasicSink(self.callback))

                await ctx.send("entrei na call dog")
            else:
                await ctx.send("q call vei, seu bobo")

        except Exception as e:
            print(f"erro na conexão de voz: {e}")
            await self.desconectar_voice(ctx)
    
    @commands.command(name="sai")
    async def desconectar_voice(self, ctx):
        
        try:
            if ctx.voice_client:
                await ctx.voice_client.disconnect()
                await ctx.send("tabein")
            else:
                await ctx.send("nem em call eu to dog")

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
    
    
    