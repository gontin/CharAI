from PyCharacterAI import get_client
from PyCharacterAI.exceptions import SessionClosedError

class CharacterManager:
    def __init__(self, token, char_id):
        self.token = token
        self.char_id = char_id
        self.client = None
        self.chat = None
        self.me = None

    async def iniciar(self):
        try:
            print("conectando ao Character.ai...")
            self.client = await get_client(token=self.token)
            self.me = await self.client.account.fetch_me()
            
            # Cria ou recupera o chat
            self.chat, greeting = await self.client.chat.create_chat(self.char_id)
            print(f"conectado ao Character.ai :D")

            return greeting.get_primary_candidate().text
        except Exception as e:
            print(f"ERROR ao iniciar char_ai: {e}")

    async def enviar_mensagem(self, texto, nome_autor):
        if not self.client or not self.chat:
            raise Exception("SEU ANSIOSO CALMA KRL")

        msg_formatada = f"{nome_autor} disse: {texto}"
        
        resposta = await self.client.chat.send_message(
            self.char_id, 
            self.chat.chat_id, 
            msg_formatada
        )
        
        return resposta.get_primary_candidate().text

    async def gerar_voz(self, texto, voice_id=22):
        if not self.client:
            raise Exception("CharacterManager não foi iniciado!")
            
        audio_bytes = await self.client.voice.generate(texto, voice_id)
        return audio_bytes