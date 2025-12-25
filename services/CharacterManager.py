from PyCharacterAI import get_client
from PyCharacterAI.exceptions import SessionClosedError


class CharacterManager:
    def __init__(self, token, char_id):
        self.token = token
        self.char_id = char_id
        self.client = None
        self.chat = None
        self.me = None

        self.last_turn_id = None
        self.last_candidate_id = None

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

    async def reboot(self):
        self.chat, greeting = await self.client.chat.create_chat(self.char_id)

    def _atualizar_ids(self, turn_obj):
        print("atualizando ids")
        try:
            candidato = turn_obj.get_primary_candidate()
            c_id = getattr(candidato, "candidate_id", None)

            t_id = None
            if hasattr(turn_obj, "turn_id"):
                t_id = turn_obj.turn_id
                    
            if t_id and str(t_id) != "None":
                self.last_turn_id = str(t_id)

            if c_id and str(c_id) != "None":
                self.last_candidate_id = str(c_id)

            print(
                f"IDs capturados -> Turn: {self.last_turn_id} | Candidate: {self.last_candidate_id}"
            )

        except Exception as e:
            print(f"Erro ao extrair IDs: {e}")

    async def enviar_mensagem(self, texto):
        if not self.client or not self.chat:
            raise Exception("SEU ANSIOSO CALMA KRL")
        msg_formatada = f"{texto}"

        resposta = await self.client.chat.send_message(
            self.char_id, self.chat.chat_id, msg_formatada
        )

        self._atualizar_ids(resposta)

        return resposta.get_primary_candidate().text

    async def gerar_voz(self, voice_id=22):
        try:
            if not self.client:
                raise Exception("CharacterManager não iniciado")

            audio_bytes = await self.client.utils.generate_speech(
                chat_id=str(self.chat.chat_id),
                turn_id=str(self.last_turn_id),
                candidate_id=str(self.last_candidate_id),
                voice_id=str(voice_id),
            )
            return audio_bytes
        except Exception as e:
            print(f"Erro ao gerar voz: {e}")
