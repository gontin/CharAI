import discord
from discord.ext import commands, tasks
# A biblioteca mágica de recepção de áudio
from discord.ext import voice_recv 
import scipy.io.wavfile
import numpy as np
import speech_recognition as sr
import asyncio
import time
import os
from dotenv import load_dotenv

# --- CONFIGURAÇÕES ---
load_dotenv()
TOKEN = os.getenv('DISCORD_TOKEN')
LANGUAGE = "pt-BR" # Mude para "en-US" se quiser testar nomes em inglês
TEMP_FOLDER = "./dados_teste"

# Garante que a pasta existe
os.makedirs(TEMP_FOLDER, exist_ok=True)

# --- CLASSE DE ESTADO (Para separar os usuários) ---
class AudioBuffer:
    def __init__(self):
        self.data = b''
        self.last_packet_time = time.time()
        self.processing = False

# --- O BOT DE TESTE ---
class TesteBot(commands.Bot):
    def __init__(self):
        intents = discord.Intents.default()
        intents.message_content = True
        intents.voice_states = True # Necessário para voz
        super().__init__(command_prefix="!", intents=intents)
        
        self.user_buffers = {}
        self.recognizer = sr.Recognizer()

    async def on_ready(self):
        print(f'--- BOT DE TESTE ONLINE: {self.user} ---')
        print(f'Linguagem configurada: {LANGUAGE}')
        print('Comandos: !entrai, !sai')
        self.check_silence.start() # Inicia o cão de guarda

    @commands.command()
    async def entrai(self, ctx):
        if not ctx.author.voice:
            await ctx.send("Entra na call primeiro!")
            return

        # Conecta usando o receptor especial
        vc = await ctx.author.voice.channel.connect(cls=voice_recv.VoiceRecvClient)
        
        # Configura o callback
        vc.listen(voice_recv.BasicSink(self.callback))
        await ctx.send(f"Estou ouvindo! Fale algo (Idiom: {LANGUAGE})...")

    @commands.command()
    async def sai(self, ctx):
        if ctx.voice_client:
            await ctx.voice_client.disconnect()
            await ctx.send("Saindo...")

    # --- PARTE 1: O CALLBACK (Recebe pacotes brutos) ---
    def callback(self, user, data: voice_recv.VoiceData):
        if not user: return

        # Cria buffer se não existir
        if user.id not in self.user_buffers:
            self.user_buffers[user.id] = AudioBuffer()
        
        estado = self.user_buffers[user.id]
        
        # Atualiza o relógio e adiciona dados
        estado.last_packet_time = time.time()
        estado.data += data.pcm

    # --- PARTE 2: O CÃO DE GUARDA (Detecta silêncio) ---
    @tasks.loop(seconds=0.5)
    async def check_silence(self):
        current_time = time.time()
        # Listar chaves para evitar erro de modificação durante iteração
        user_ids = list(self.user_buffers.keys())

        for uid in user_ids:
            estado = self.user_buffers[uid]
            
            if estado.processing or len(estado.data) == 0:
                continue

            # Se passou 1.2s sem receber pacote, acabou a frase
            if current_time - estado.last_packet_time > 1.2:
                # Filtro de ruído (menos de 0.5s de áudio joga fora)
                if len(estado.data) < 50000:
                    estado.data = b''
                    continue
                
                print(f"[SILÊNCIO DETECTADO] Processando áudio do usuário ID {uid}...")
                
                # Bloqueia, copia e limpa
                estado.processing = True
                audio_to_process = estado.data
                estado.data = b''
                
                # Pega o objeto User para mostrar o nome bonito
                user = self.get_user(uid)
                user_name = user.display_name if user else f"ID {uid}"

                # Manda processar
                asyncio.create_task(self.process_audio(user_name, uid, audio_to_process))
                
                # Reseta
                estado.processing = False

    # --- PARTE 3: TRANSCRIÇÃO (Salva e reconhece) ---
    async def process_audio(self, user_name, uid, audio_bytes):
        filename = f"{TEMP_FOLDER}/user_{uid}.wav"
        
        # 1. Salvar WAV (Executa em thread separada para não travar)
        await self.loop.run_in_executor(None, self.save_wav, filename, audio_bytes)
        
        # 2. Transcrever
        texto = await self.loop.run_in_executor(None, self.transcribe_wav, filename)

        # 3. RESULTADO NO TERMINAL
        print("-" * 40)
        if texto:
            print(f"🗣️  {user_name} FALOU: '{texto}'")
            
            # Teste simples de reconhecimento de nome
            if "amy" in texto.lower() or "eime" in texto.lower():
                print(">>> 🤖 OPA! Reconheci meu nome (Amy)!")
        else:
            print(f"❌ {user_name} falou algo ininteligível.")
        print("-" * 40)

    def save_wav(self, filename, audio_bytes):
        # Converte bytes PCM (int16) para array numpy e salva
        data = np.frombuffer(audio_bytes, dtype=np.int16)
        scipy.io.wavfile.write(filename, 48000, data)

    def transcribe_wav(self, filename):
        try:
            with sr.AudioFile(filename) as source:
                # listen processa o arquivo wav limpo
                audio = self.recognizer.record(source)
            
            # Usa o Google Web Speech API
            return self.recognizer.recognize_google(audio, language=LANGUAGE)
        except sr.UnknownValueError:
            return None
        except Exception as e:
            print(f"Erro no recognizer: {e}")
            return None

# --- RODAR ---
if __name__ == "__main__":
    bot = TesteBot()
    bot.run(TOKEN)