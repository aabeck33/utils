# Dependência -> FFmpeg: https://ffmpeg.org/download.html

from moviepy import VideoFileClip
import speech_recognition as sr
from pydub import AudioSegment


# Variáveis
audio_path = "audio.mp3"
text_path = "transcript.txt"
video_path = "video.mp4"
language = "pt-BR"                      # pt-BR | zh-CN


def convert_mp4_to_mp3(video_path, audio_path):
    print("Convertendo MP4 para MP3...")
    video_path = "video.mp4"
    audio_path = "audio.mp3"
    video = VideoFileClip(video_path)
    video.audio.write_audiofile(audio_path)
    print("Conversão concluída! Áudio salvo em:", audio_path)


def transcribe_audio(audio_path, text_path, language="pt-BR"):
    # Inicializa o reconhecedor
    r = sr.Recognizer()

    # Converter MP3 para WAV (para melhor compatibilidade)
    if audio_path.endswith(".mp3"):
        print("Convertendo MP3 para WAV...")
        audio_mp3 = audio_path
        audio_wav = "temp.wav"
        sound = AudioSegment.from_mp3(audio_mp3)
        sound = sound.set_channels(1).set_frame_rate(16000) # Mono e 16kHz
        sound.export(audio_wav, format="wav")
        audio_path = audio_wav

    # Carrega o arquivo de áudio
    with sr.AudioFile(audio_path) as source:
        audio_data = r.record(source)
        texto = r.recognize_google(audio_data, language=language)
        print("Texto transcrito:")
        print(texto)

    # Salva o texto transcrito em um arquivo
    with open(text_path, "w", encoding="utf-8") as f:
        f.write(texto)


if __name__ == "__main__":
    #convert_mp4_to_mp3(video_path, audio_path)
    transcribe_audio(audio_path, text_path, language)

# Fim do arquivo mp4tomp3.py