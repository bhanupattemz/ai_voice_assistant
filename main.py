# import asyncio
# from src.core.assistant import VoiceAssistant
# from src.config.settings import settings
# import logging
# from gtts import gTTS
# from io import BytesIO
# import pygame
# import keyboard
# import sounddevice as sd
# import numpy as np
# from scipy.io.wavfile import write
# from pynput import keyboard
# import speech_recognition as sr

# logging.basicConfig(
#     level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
# )


# async def main():
#     """Main entry point for the voice assistant."""
#     assistant = VoiceAssistant()
#     await assistant.initialize()
#     print(f"Welcome to {settings.assistant_name}!")
#     print("Type 'exit' or 'quit' to end the conversation.")

#     while True:
#         try:
#             user_input = await asyncio.to_thread(input, "\nYou: ")
#             user_input = user_input.strip()

#             if user_input.lower() in ["exit", "quit", "bye"]:
#                 print("Goodbye!")
#                 break

#             if not user_input:
#                 continue

#             response = await assistant.chat(user_input)
#             print(f"\n{settings.assistant_name}: {response}")

#         except KeyboardInterrupt:
#             print("\nGoodbye!")
#             break
#         except Exception as e:
#             logging.error(f"Error processing request: {e}")
#             print("Sorry, I encountered an error. Please try again.")





# LONG_PRESS_THRESHOLD = 1.0
# TRIGGER_COOLDOWN = 0.5


# async def wait_for_trigger():
#     """Wait for Control key long press."""
#     while True:
#         if keyboard.is_pressed("ctrl"):
#             loop = asyncio.get_running_loop()
#             start = loop.time()
#             while keyboard.is_pressed("ctrl"):
#                 await asyncio.sleep(0.1)
#             if loop.time() - start >= LONG_PRESS_THRESHOLD:
#                 await asyncio.sleep(TRIGGER_COOLDOWN)
#                 return "ctrl"
#         await asyncio.sleep(0.1)


# async def play_sound(sound):
#     """Play a preloaded sound."""
#     sound.play()
#     await asyncio.sleep(sound.get_length())


# async def speak(text):
#     """Convert text to speech and play."""
#     try:
#         tts = gTTS(text=text, lang="en", slow=False)
#         fp = BytesIO()
#         tts.write_to_fp(fp)
#         fp.seek(0)
#         pygame.mixer.music.load(fp)
#         pygame.mixer.music.play()
#         while pygame.mixer.music.get_busy():
#             await asyncio.sleep(0.1)
#     except Exception as e:
#         logging.error(f"TTS playback failed: {e}")
#         print("Could not play audio response.")



# async def main():
#     """Voice assistant triggered by long press of Control key."""
#     assistant = VoiceAssistant()
#     await assistant.initialize()
#     r = sr.Recognizer()
#     pygame.mixer.init()

#     wakeup_sound = pygame.mixer.Sound("wakeup.mp3")
#     sleep_sound = pygame.mixer.Sound("sleep.mp3")

#     with sr.Microphone() as source:
#         r.adjust_for_ambient_noise(source, duration=1)

#     print(f"Welcome to {settings.assistant_name}!")
#     print("Long-press the Control key to start talking. Ctrl+C to exit.")

#     while True:
#         try:
#             trigger = await wait_for_trigger()
#             print(f"{trigger.capitalize()} long-press detected! Starting command mode...")
        
#             n = 0
#             while n < 5:
#                 await play_sound(wakeup_sound)
#                 with sr.Microphone() as source:
#                     r.pause_threshold = 1.5
#                     print("Listening for your command...")
#                     audio = r.listen(source, timeout=5, phrase_time_limit=10)                
#                 try:
#                     command = r.recognize_google(audio)
#                     print(f"You: {command}")

#                     if command.lower() in ["exit", "quit", "bye"]:
#                         await play_sound(sleep_sound)
#                         print(
#                             "Exiting command mode. Long-press Control key to trigger again."
#                         )
#                         break

#                     response = await assistant.chat(command)
#                     n = 0
#                     print(f"{settings.assistant_name}: {response}")

#                     await speak(response)

#                 except sr.UnknownValueError:
#                     n += 1
#                     print("Sorry, could not understand the audio.")
#                 except sr.RequestError:
#                     n += 1
#                     print("Could not request results; check your internet connection.")
#                 finally:
#                     pygame.mixer.quit()
#             if n == 5:
#                 await play_sound(sleep_sound)

#         except KeyboardInterrupt:
#             print("\nGoodbye!")
#             break
#         except Exception as e:
#             logging.error(f"Error: {e}")
#             print("Encountered an error, please try again.")














import asyncio
import logging
from gtts import gTTS
from io import BytesIO
import pygame
import sounddevice as sd
import numpy as np
from scipy.io.wavfile import write
from pynput import keyboard as pynput_keyboard
import speech_recognition as sr

from src.core.assistant import VoiceAssistant
from src.config.settings import settings

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)

pygame.mixer.init()

async def speak(text):
    try:
        tts = gTTS(text=text, lang="en", slow=False)
        fp = BytesIO()
        tts.write_to_fp(fp)
        fp.seek(0)
        pygame.mixer.music.load(fp)
        pygame.mixer.music.play()
        while pygame.mixer.music.get_busy():
            await asyncio.sleep(0.1)
    except Exception as e:
        logging.error(f"TTS playback failed: {e}")

async def main():
    fs = 44100
    recording = []
    stream = None
    recording_on = False

    assistant = VoiceAssistant()
    await assistant.initialize()

    loop = asyncio.get_running_loop()

    def callback(indata, frames, time, status):
        recording.append(indata.copy())

    def on_press(key):
        nonlocal stream, recording_on, recording
        if key in (pynput_keyboard.Key.ctrl_l, pynput_keyboard.Key.ctrl_r) and not recording_on:
            recording = []
            stream = sd.InputStream(
                samplerate=fs,
                channels=1,
                dtype="float32",
                callback=callback
            )
            stream.start()
            recording_on = True
            

    def on_release(key):
        nonlocal stream, recording_on
        if key in (pynput_keyboard.Key.ctrl_l, pynput_keyboard.Key.ctrl_r) and recording_on:
            stream.stop()
            stream.close()
            recording_on = False
           
            audio = np.concatenate(recording, axis=0)
            audio = np.int16(audio * 32767)
            write("output.wav", fs, audio)

            loop.call_soon_threadsafe(
                lambda: asyncio.create_task(process_audio())
            )

    async def process_audio():
        r = sr.Recognizer()
        try:
            with sr.AudioFile("output.wav") as source:
                r.adjust_for_ambient_noise(source, duration=0.2)
                audio_data = r.record(source)

            command = r.recognize_google(audio_data)
            print("You:", command)

            response = await assistant.chat(command)
            print(f"{settings.assistant_name}: {response}")

            await speak(response)

        except sr.UnknownValueError:
            print("Could not understand audio")

        except sr.RequestError as e:
            print("Speech service error:", e)

    listener = pynput_keyboard.Listener(on_press=on_press, on_release=on_release)
    listener.start()

    while True:
        await asyncio.sleep(0.1)

if __name__ == "__main__":
    try:
        asyncio.run(main())
    finally:
        pygame.mixer.quit()
