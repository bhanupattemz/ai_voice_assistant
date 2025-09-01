import asyncio
from src.core.assistant import VoiceAssistant
from src.config.settings import settings
import logging
import speech_recognition as sr
from gtts import gTTS
from io import BytesIO
import pygame

logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)

async def main():
    """Main entry point for the voice assistant."""
    assistant = VoiceAssistant()
    await assistant.initialize()
    print(f"Welcome to {settings.assistant_name}!")
    print("Type 'exit' or 'quit' to end the conversation.")

    while True:
        try:
            user_input = await asyncio.to_thread(input, "\nYou: ")
            user_input = user_input.strip()

            if user_input.lower() in ["exit", "quit", "bye"]:
                print("Goodbye!")
                break

            if not user_input:
                continue

            response = await assistant.chat(user_input)
            print(f"\n{settings.assistant_name}: {response}")

        except KeyboardInterrupt:
            print("\nGoodbye!")
            break
        except Exception as e:
            logging.error(f"Error processing request: {e}")
            print("Sorry, I encountered an error. Please try again.")


# async def main():
#     """Voice assistant: waits for wake word 'Hey Nova' before starting command loop."""
#     assistant = VoiceAssistant()
#     r = sr.Recognizer()
#     pygame.mixer.init()

#     print(f"Welcome to {settings.assistant_name}!")
#     print("Say 'Hey Nova' to start talking. Type Ctrl+C to exit.")

#     while True:
#         try:
#             with sr.Microphone() as source:
#                 r.adjust_for_ambient_noise(source)
#                 print("Listening for wake word...")
#                 audio = r.listen(source)

#             try:
#                 text = r.recognize_google(audio).lower()
#                 print(f"You said: {text}")

#                 if "nova" in text.lower():
#                     print("Wake word detected! Starting command mode...")

#                     n = 0
#                     while n < 5:
#                         with sr.Microphone() as source:
#                             r.adjust_for_ambient_noise(source)
#                             print("Listening for your command...")
#                             audio = r.listen(source)
#                         try:
#                             command = r.recognize_google(audio)
#                             print(f"You: {command}")

#                             if command.lower() in ["exit", "quit", "bye"]:
#                                 print(
#                                     "Exiting command mode. Say 'Hey Nova' to trigger again."
#                                 )
#                                 break

#                             response = await assistant.chat(command)
#                             n = 0
#                             print(f"{settings.assistant_name}: {response}")

#                             tts = gTTS(text=response, lang="en", slow=False)
#                             fp = BytesIO()
#                             tts.write_to_fp(fp)
#                             fp.seek(0)
#                             pygame.mixer.music.load(fp)
#                             pygame.mixer.music.play()
#                             while pygame.mixer.music.get_busy():
#                                 pygame.time.Clock().tick(10)

#                         except sr.UnknownValueError:
#                             n += 1
#                             print("Sorry, could not understand the audio.")
#                         except sr.RequestError:
#                             n += 1
#                             print(
#                                 "Could not request results; check your internet connection."
#                             )

#             except sr.UnknownValueError:
#                 continue  
#             except sr.RequestError:
#                 print("Could not request results; check your internet connection.")

#         except KeyboardInterrupt:
#             print("\nGoodbye!")
#             break
#         except Exception as e:
#             logging.error(f"Error: {e}")
#             print("Encountered an error, please try again.")


if __name__ == "__main__":
    asyncio.run(main())
