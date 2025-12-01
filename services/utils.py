import speech_recognition as sr

def transcrever_audio_speechrecognition(audio_path):
    recognizer = sr.Recognizer()
    with sr.AudioFile(audio_path) as source:
        audio = recognizer.record(source)  
    texto = recognizer.recognize_google(audio, language="pt-BR")
    return texto