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
        self.user_buffers = {}
        self.user_names = {}

        self.ultimo_momento_fala_global = 0
        self.vc = None
        self.ocupado_processando = False

        
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
            data_np = np.frombuffer(audio_data, dtype=np.int32)

            # RECOGNIZER DO GOOGLE
            scipy.io.wavfile.write(arq_memoria, 48000, data_np)
            arq_memoria.seek(0)

            rec = sr.Recognizer()

            with sr.AudioFile(arq_memoria) as source:
                audio = rec.record(source)
            texto = rec.recognize_google(audio, language="pt-BR")

            # VOSK
            # data_np = data_np.astype(np.int16)

            # data_16k = data_np[::3]
            # rec = KaldiRecognizer(self.vosk_model, 16000)
            # rec.AcceptWaveform(data_16k.tobytes())
            # result_json = json.loads(rec.FinalResult())
            # texto = result_json.get("text", "")

            print(f"terminou em {time.time()-inicio:.2f}")
            return (uid, texto)

        except Exception as e:
            print(f"Erro ao transcrever: {e}")

    async def processar_voz(self):
        print(f"processando voz...")
        if self.vc:
            if self.vc.is_connected():
                self.vc.stop_listening()
                
                
        inicio = time.time()
        try:
            buffers_copia = self.user_buffers.copy()
            self.user_buffers.clear()

            loop = asyncio.get_running_loop()
            tasks_transcrever = []
            print("começou a transcrever")
            for uid, audio_data in buffers_copia.items():
                tasks_transcrever.append(
                    loop.run_in_executor(None, self.transcrever, uid, audio_data)
                )
            result = await asyncio.gather(*tasks_transcrever)
            valid_result = [r for r in result if r is not None]
            msg = ""
            if valid_result: 
                for i in valid_result:

                    nome = self.user_names.get(i[0], f"user [{i[0]}]")
                    msg += f"{nome} disse: {i[1]}\n"

                    print(f"\n{nome} disse: {i[1]}")
            else:
                print("só erro")
                self.vc.listen(voice_recv.BasicSink(self.callback))
                return

            resposta = await self.bot.char_ai.enviar_mensagem(msg)

            print(f"\nAmy disse: {resposta}")
            
            audio_bytes = await self.bot.char_ai.gerar_voz(os.getenv("CHAR_VOZID"))
            if not audio_bytes:
                time.sleep(1)
                audio_bytes = await self.bot.char_ai.gerar_voz(os.getenv("CHAR_VOZID"))
                
            caminho_resp = "./data/temp/resposta_ia.mp3"
            os.makedirs(os.path.dirname(caminho_resp), exist_ok=True)

            with open(caminho_resp, "wb") as f:
                f.write(audio_bytes)

            if self.vc.is_playing():
                self.vc.stop()
            self.vc.play(
                discord.FFmpegPCMAudio(caminho_resp),
            )
            
            
            print(f"Terminou de processar em {time.time()-inicio:.2f}")
            self.vc.listen(voice_recv.BasicSink(self.callback))


        except Exception as e:
            print(f"Erro ao processar: {e}")

    def limpar_texto_para_tts(self, texto):
        if not texto:
            return ""

        texto = re.sub(r"\bvc\b", "você", texto, flags=re.IGNORECASE)

        texto = re.sub(r"[\U00010000-\U0010ffff]", "", texto)

        texto = re.sub(r"\s+", " ", texto).strip()

        return texto

    @tasks.loop(seconds=1.0)
    async def fiscal_de_silencio(self):

        if not self.user_buffers:
            return
        if self.ocupado_processando:
            return

        agora = time.time()

        tempo_silencio = agora - self.ultimo_momento_fala_global
        if tempo_silencio > 0.8:
            total_bytes = 0
            for user_id in self.user_buffers:
                total_bytes += len(self.user_buffers[user_id])

            if total_bytes > 200000:
                self.ocupado_processando = True

                await self.processar_voz()

                self.ocupado_processando = False

    @commands.command(name="call")
    async def conectar_voice(self, ctx):
        try:
            if self.vc:
                self.desconectar_voice(ctx)
            else:
                self.bot.disponivel = False
                if ctx.author.voice:

                    self.vc = await ctx.author.voice.channel.connect(
                        cls=voice_recv.VoiceRecvClient, reconnect=True
                    )
                    self.vc.listen(voice_recv.BasicSink(self.callback))

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
                self.vc = None
                self.bot.disponivel = True
                await ctx.send("saindu")
            else:
                await ctx.send("m-mas eu nem to ai!")

        except Exception as e:
            print(f"erro na desconexão(???): {e}")

    def callback(self, user, data: voice_recv.VoiceData):
        try:
            if user is None or user.id == self.bot.user.id:
                return

            if self.bot.voice_clients and any(
                self.vc.is_playing() for vc in self.bot.voice_clients
            ):
                return

            if self.ocupado_processando:
                return

            if user.id not in self.user_buffers:
                self.user_buffers[user.id] = b""
                self.user_names[user.id] = user.display_name

            self.user_buffers[user.id] += data.pcm
            
            self.ultimo_momento_fala_global = time.time()

        except Exception as e:
            print(f"errin: {e}")


async def setup(bot):
    await bot.add_cog(VoiceCog(bot))
