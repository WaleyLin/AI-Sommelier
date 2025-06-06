import os
from dotenv import load_dotenv, find_dotenv
from assistantModelCode import ChatbotAssistant

# Load the .env file explicitly
env_path = find_dotenv()
if not env_path:
    raise ValueError("❌ ERROR: .env file not found. Make sure it exists in the root directory.")

load_dotenv(env_path)

# Verify API key is loaded
api_key = os.getenv("OPENAI_API_KEY")
if not api_key:
    raise ValueError("❌ ERROR: OPENAI_API_KEY is missing. Set it in your .env file.")

print("OpenAI API Key is set. Initializing assistant...")

# Initialize the assistant
assistant = ChatbotAssistant()

def setup_assistant():
    """
    Tests the assistant with a sample query.
    """
    sample_question = "What wine pairs well with steak?"
    print(f"🟢 Testing assistant with: {sample_question}")

    response = assistant.query_assistant(sample_question)
    print(f"🟢 Assistant Response: {response}")

if __name__ == "__main__":
    setup_assistant()
