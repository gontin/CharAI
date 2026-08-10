# Character.AI Discord Voice Bot (Amy)
feito por gontin :3

Um bot completo para Discord que integra as respostas e vozes do **Character.AI** diretamente no seu servidor. Ele não apenas conversa por texto de forma contextualizada, mas também é capaz de entrar em canais de voz, ouvir múltiplos usuários, transcrever o áudio em tempo real e responder com a voz gerada pela IA.

---

## Funcionalidades

- **Integração com Character.AI:** Utiliza a biblioteca `PyCharacterAI` para manter contexto, histórico e a personalidade do bot.
- **Reconhecimento de Voz (STT):** Intercepta áudio no canal de voz do Discord, cria buffers individuais por usuário e utiliza o Google Speech Recognition para transcrever a fala em texto.
- **Síntese de Voz (TTS):** Gera áudio com a voz específica do Character.AI escolhido e reproduz nativamente no canal de voz do Discord.
- **Isolamento de Canal:** Responde automaticamente a mensagens de texto apenas no canal designado (ex: `#amy`), mantendo os outros canais limpos.
- **Gerenciamento de Fila de Áudio:** Processa as falas de múltiplos usuários sem sobreposição, aguardando o momento certo de silêncio para enviar a mensagem unificada para a IA.

---

## Tecnologias Utilizadas

- **[Python 3.x](https://www.python.org/)**
- **[Discord.py](https://discordpy.readthedocs.io/)** (Framework base do bot)
- **[discord-ext-voice-recv](https://github.com/imayhaveborkedit/discord-ext-voice-recv)** (Para recebimento de áudio em canais de voz)
- **[PyCharacterAI](https://github.com/Xtr4F/PyCharacterAI)** (Comunicação com a API do Character.AI)
- **[SpeechRecognition](https://pypi.org/project/SpeechRecognition/)** (Transcrição de áudio)
- **[SciPy](https://scipy.org/) & [NumPy](https://numpy.org/)** (Processamento de arrays de áudio na memória)

---
