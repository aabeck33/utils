################################################################
##   Script: mp4tomp3.py
##   Autor: Alvaro Beck
##   Descrição: Converte arquivos MP4 para MP3, transcreve áudio para texto,
##              traduz texto e converte texto para fala.
##   Data: 2024-06-10
#
# text_to_speach(text, output_audio_path, language="pt-BR")
# substitute_audio_in_video(video_path, audio_path, output_video_path)
# convert_mp4_to_mp3(video_path, audio_path)
# transcribe_audio(audio_path, text_path, language="pt-BR")
# transcribe_with_whisper(audio_path, model_size="base", input_language="pt")
# translate_text(text, input_language="pt", output_language="en")
# ------------------------------------------------------------------------------------------------
# Dependência do SpeachRecognition -> FFmpeg: https://ffmpeg.org/download.html
# pip install git+https://github.com/openai/whisper.git
# pip install moviepy speechrecognition librosa soundfile googletrans==4.0.0-rc1 gtts pydub requests
# https://breakfastquay.com/rubberband/
################################################################

from moviepy import VideoFileClip, AudioFileClip
import speech_recognition as sr
import librosa
import soundfile as sf
import whisper
import pyrubberband as rb
from googletrans import Translator
from gtts import gTTS
from pydub import AudioSegment
import requests
from audiotsm import phasevocoder
from audiotsm.io.wav import WavReader, WavWriter


# Variáveis e constantes
audio_path = "audio.mp3"
text_path = "transcript.txt"
video_path = "video.mp4"
output_video_path = "video_with_new_audio.mp4"
output_audio_path = "output_audio.mp3"
output_text_path = "translated_text.txt"
text = "Olá, este é um exemplo de conversão de texto para fala usando Python criado por Alvaro Beck."
language = "pt-BR"                    # pt-BR | zh-CN | en-US
input_language = "pt"                 # pt | zh | en
output_language = "zh-CN"             # en-US | zh-CN | pt-BR
END_VIDEO_START_SILENCE_MS = 2000          # Milissegundos de silêncio no início do vídeo final


def text_to_speech(text, output_audio_path, language="pt-BR"):
    if text.strip() == "":
        print("Texto vazio. Nada para converter para fala.")
        return

    if text.endswith(".txt"):
        with open(text, "r", encoding="utf-8") as f:
            text = f.read()
    tts = gTTS(text=text, lang=language)
    tts.save(output_audio_path)
    print(f"Áudio gerado com sucesso! Arquivo salvo em: {output_audio_path}")


def mix_multiple_audios(voice_path, audio_path) -> str:
    voice = AudioSegment.from_file(voice_path)
    music = AudioSegment.from_file(audio_path)

    music = music - 10  # reduz volume da música (em dB)
    final_audio = music.overlay(voice)

    audio_path = "tempmix.wav"
    final_audio.export(audio_path, format="wav")
    return audio_path


def audio_stretch(audio_path, target_duration_ms) -> str:
    y, sr = librosa.load(audio_path)

    # Calcular fator correto
    current_duration = len(y) / sr
    target_duration = target_duration_ms / 1000
    rate = current_duration / target_duration  # inverso do fator

    output_audio_path = "tempvdajst.wav"
    print(f"Ajustando velocidade: rate={rate:.3f}")
    #y_stretched = librosa.effects.time_stretch(y, rate=rate)
    #y_stretched = rb.time_stretch(y, sr, rate)
    with WavReader(audio_path) as reader:
        with WavWriter(output_audio_path, reader.channels, reader.samplerate) as writer:
            tsm = phasevocoder(reader.channels, speed=rate)
            tsm.run(reader, writer)

    audio_path = output_audio_path
    #sf.write(audio_path, y_stretched, sr)

    return audio_path


def audio_adjustment(audio_path, target_duration_ms, start_ms=0) -> str:
    audio = AudioSegment.from_file(audio_path)
    # Adiciona silêncio no início, se necessário
    if start_ms > 0:
        print("Adicionando silêncio no início do áudio...")
        silence_start = AudioSegment.silent(duration=start_ms)
        audio = silence_start + audio
    if len(audio) > target_duration_ms and target_duration_ms > 0:
        print("Cortando áudio para combinar com o vídeo...")
        audio = audio[:target_duration_ms]
    elif target_duration_ms == 0:
        print("Mantendo duração original do áudio...")
        target_duration_ms = len(audio)
    if len(audio) < target_duration_ms:
        print("Adicionando silêncio no final do áudio...")
        # Adiciona silêncio no final, se necessário
        if len(audio) < target_duration_ms:
            silence = AudioSegment.silent(duration=target_duration_ms - len(audio))
            audio = audio + silence
    # Exporta áudio ajustado
    audio_path = "tempvdaj.wav"
    audio.export(audio_path, format="wav")
    return audio_path


def substitute_audio_in_video(video_path, audio_path, output_video_path) -> None:
    video = VideoFileClip(video_path)
    audio = AudioFileClip(audio_path)

    if audio_path.endswith(".mp3"):
        convert_mp3_to_wav(audio_path, "tempvd.wav", quality="stereo")
        audio_path = "tempvd.wav"
    audio_path = audio_adjustment(audio_path, target_duration_ms=((audio.duration+2) * 1000), start_ms = END_VIDEO_START_SILENCE_MS)
    audio_path = audio_stretch(audio_path, target_duration_ms=int(video.duration * 1000))
    new_audio = AudioFileClip(audio_path)
    audio.close()

    # Ajustar duração do áudio para combinar com o vídeo
    new_audio = new_audio.with_duration(video.duration)
    #new_audio = new_audio.subclipped(0, video.duration)

    video_with_new_audio = video.with_audio(new_audio)
    video_with_new_audio.write_videofile(output_video_path, codec="libx264", audio_codec="aac")
    print(f"Áudio substituído com sucesso! Arquivo salvo em: {output_video_path}")


def convert_mp4_to_mp3(video_path, audio_path):
    print("Convertendo MP4 para MP3...")
    video_path = "video.mp4"
    audio_path = "audio.mp3"
    video = VideoFileClip(video_path)
    video.audio.write_audiofile(audio_path)
    print("Conversão concluída! Áudio salvo em:", audio_path)


def convert_mp3_to_wav(mp3_path, wav_path, quality= "mono"):
    print("Convertendo MP3 para WAV...")
    audio = AudioSegment.from_mp3(mp3_path)
    if quality == "mono":
        audio = audio.set_channels(1).set_frame_rate(16000) # Mono e 16kHz
    else:
        audio = audio.set_channels(2).set_frame_rate(44100) # Stereo e 44.1kHz
    audio.export(wav_path, format="wav")
    print(f"Arquivo WAV salvo em: {wav_path}")


def transcribe_audio(audio_path, text_path, language="pt-BR") -> str:
    # Inicializa o reconhecedor
    r = sr.Recognizer()

    # Converter MP3 para WAV (para melhor compatibilidade)
    if audio_path.endswith(".mp3"):
        convert_mp3_to_wav(audio_path, "temp.wav")
        audio_path = "temp.wav"

    # Carrega o arquivo de áudio
    with sr.AudioFile(audio_path) as source:
        audio_data = r.record(source)
        texto = r.recognize_google(audio_data, language=language)
        print("Texto transcrito:")
        print(texto)

    # Salva o texto transcrito em um arquivo
    with open(text_path, "w", encoding="utf-8") as f:
        f.write(texto)
    print(f"Transcrição salva em: {text_path}")
    return texto


def transcribe_with_whisper(audio_path, model_size="base", input_language="pt") -> str:
    model = whisper.load_model(model_size)
    result = model.transcribe(audio_path, language=input_language)
    texto = result["text"]
    print("Transcrição com Whisper:")
    print(texto)

    with open(text_path, "w", encoding="utf-8") as f:
        f.write(texto)
    print(f"Transcrição salva em: {text_path}")

    return texto


def translate_text(text, output_text_path, input_language="pt", output_language="en") -> str:
    translated_text = ""

    if text.strip() == "":
        print("Texto vazio. Nada para traduzir.")
        return ""
    
    if text.endswith(".txt"):
        with open(text, "r", encoding="utf-8") as f:
            text = f.read()
    translator = Translator()
    translated_text = translator.translate(text, src=input_language, dest=output_language).text

    print(f"Texto traduzido para {output_language}:")
    print(translated_text)
    if output_text_path.endswith(".txt"):
        with open(output_text_path, "w", encoding="utf-8") as f:
            f.write(translated_text)
        print(f"Tradução salva em: {output_text_path}")

    return translated_text



if __name__ == "__main__":
    # text_to_speech(output_text_path, output_audio_path, language=output_language)
    substitute_audio_in_video(video_path, output_audio_path, output_video_path)
    # convert_mp4_to_mp3(video_path, audio_path)
    # transcribe_audio(audio_path, text_path, language=language)
    # transcribe_with_whisper(audio_path, model_size="base", input_language=input_language)
    # translate_text(text_path, output_text_path, input_language=input_language, output_language=output_language)

# Fim do arquivo mp4tomp3.py