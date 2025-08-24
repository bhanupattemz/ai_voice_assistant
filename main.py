
import asyncio
from src.core.assistant import VoiceAssistant
from src.config.settings import settings
import logging

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

async def main():
    """Main entry point for the voice assistant."""
    assistant = VoiceAssistant()
    
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

if __name__ == "__main__":
    asyncio.run(main())