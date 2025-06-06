from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
import os
from dotenv import load_dotenv
from assistantModelCode import ChatbotAssistant  # Import the chatbot model

# Load .env from the project root directory
env_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), ".env")
load_dotenv(env_path)

# Ensure OpenAI API key is set
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
if not OPENAI_API_KEY:
    raise ValueError("ERROR: OPENAI_API_KEY is missing. Set it in your .env file.")

# Initialize FastAPI app
app = FastAPI()

# Add CORS Middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  
    allow_credentials=True,
    allow_methods=["*"],  
    allow_headers=["*"],  
)

# Initialize ChatbotAssistant
assistant = ChatbotAssistant()  

@app.get("/")
def root():
    """
    Root endpoint to verify that the API is running.
    """
    return {"message": "Welcome to the SipNSavor API! Use /chat to interact with the assistant."}

@app.post("/chat")
async def chat(request: Request):
    """
    Handle user queries and provide responses using ChatbotAssistant.
    """
    data = await request.json()
    user_query = data.get("query", "").strip()
    user_id = data.get("user_id", "").strip()  # ✅ Get user_id from request

    if not user_query:
        return {"error": "Query cannot be empty."}

    if not user_id:
        return {"error": "User ID is required to fetch preferences."}

    try:
        # ✅ Call `query_assistant` with user_id
        bot_response = assistant.query_assistant(user_id, user_query)

        # Debugging log
        print(f"🟢 User ({user_id}): {user_query}")
        print(f"🟢 Bot Response: {bot_response}")

        return {"response": bot_response}
    
    except Exception as e:
        print(f"🔴 Unexpected error: {str(e)}")
        return {"error": f"An unexpected error occurred: {str(e)}"}
