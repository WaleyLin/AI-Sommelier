import openai
import os
import json
import firebase_admin
from firebase_admin import db, credentials

class ChatbotAssistant:
    def __init__(self):
        self.api_key = os.getenv("OPENAI_API_KEY")
        if not self.api_key:
            raise ValueError("API key is missing. Please provide a valid OpenAI API key.")
        openai.api_key = self.api_key

        firebase_creds_path = os.getenv("FIREBASE_CREDENTIALS_PATH", "/etc/secrets/firebase-key.json")
        if not os.path.exists(firebase_creds_path):
            raise FileNotFoundError(f"Firebase credentials file not found at: {firebase_creds_path}")

        with open(firebase_creds_path, "r") as f:
            creds_content = f.read().strip()

        if not creds_content:
            raise ValueError(f"Firebase credentials file at {firebase_creds_path} is empty!")

        firebase_creds_dict = json.loads(creds_content)

        if not firebase_admin._apps:
            cred = credentials.Certificate(firebase_creds_dict)
            firebase_admin.initialize_app(cred, {
                "databaseURL": "https://sip-and-savor-c9393-default-rtdb.firebaseio.com"
            })

    def get_user_preferences(self, user_id):
        user_ref = db.reference(f"users/{user_id}/chatbot_preferences")
        preferences = user_ref.get()

        print(f"🔍 Retrieved preferences for {user_id}: {preferences}")
        return preferences if preferences else {
            "favorite_wine": "",
            "favorite_beer": "",
            "favorite_cocktail": "",
            "favorite_spirit": "",
            "alcohol_preference": "",
            "sweet_or_dry": "",
            "red_or_white_wine": "",
            "light_or_strong": "",
            "vegan_friendly": False,
            "gluten_free": False
        }

    def store_user_preferences(self, user_id, preferences):
        user_pref_ref = db.reference(f"users/{user_id}/chatbot_preferences")
        user_pref_ref.set(preferences)
        print(f"✅ Updated preferences for {user_id}: {preferences}")

    def list_available_preferences(self):
        return (
            "Here are the preferences you can set:\n"
            "🍇 Favorite Wine\n"
            "🍺 Favorite Beer\n"
            "🍹 Favorite Cocktail\n"
            "🥃 Favorite Spirit\n"
            "🎯 Alcohol Preference (e.g., wine, beer, spirits)\n"
            "🍬 Sweet or Dry\n"
            "🔴 Red or White Wine\n"
            "💪 Light or Strong Drinks\n"
            "🌱 Vegan-Friendly\n"
            "🍾 Gluten-Free\n\n"
            "You can update your preferences by telling me something like 'My favorite wine is Merlot.' 😊"
        )

    def format_preferences(self, preferences):
        pref_list = []
        for key, value in preferences.items():
            if isinstance(value, bool):
                value = "Yes" if value else "No"
            if value:
                pref_list.append(f"➡ {key.replace('_', ' ').title()}: {value}")

        return (
            "Here are your current preferences:\n" + "\n".join(pref_list)
            if pref_list
            else "You haven't set any preferences yet! Want to set one now? 😊"
        )

    def ask_gpt_for_preference_update(self, user_query, preferences):
        try:
            keys = list(preferences.keys())
            examples = "\n".join([f"- favorite_wine: Merlot", f"- vegan_friendly: true"])

            prompt = (
                "You are a helpful assistant. Based on the user's input below, determine if they are updating a preference.\n"
                f"Here are current preferences: {json.dumps(preferences)}\n"
                "User message: '" + user_query + "'\n"
                "If it contains a preference update, reply ONLY in JSON like this:\n"
                "{\"favorite_wine\": \"Merlot\"}\n"
                "If it doesn't update any preference, reply ONLY with an empty JSON: {}"
            )

            client = openai.OpenAI()
            result = client.chat.completions.create(
                model="gpt-4",
                messages=[
                    {"role": "system", "content": prompt},
                    {"role": "user", "content": user_query}
                ],
            )

            raw_json = result.choices[0].message.content.strip()
            updates = json.loads(raw_json)

            if updates:
                for key, val in updates.items():
                    preferences[key] = val
                updated_keys = ', '.join(updates.keys())
                return True, f"✅ I’ve updated your preferences: {updated_keys.replace('_', ' ').title()}."


            return False, None
        except Exception as e:
            print("❌ GPT preference detection error:", e)
            return False, None

    def query_assistant(self, user_id, user_query):
        try:
            user_preferences = self.get_user_preferences(user_id)
            name = user_preferences.get("name", "there")

            updated, update_msg = self.ask_gpt_for_preference_update(user_query, user_preferences)
            if updated:
                self.store_user_preferences(user_id, user_preferences)
                return update_msg

            greetings = ["hi", "hello", "hey", "yo", "what's up", "howdy"]
            if any(greet in user_query.lower() for greet in greetings):
                return (
                    f"Hello, {name}! 👋 I'm your sommelier assistant. "
                    f"I can help you pick the perfect wine, beer, or cocktail — just ask! 🍇"
                )

            if "what preferences can i set" in user_query.lower():
                return self.list_available_preferences()

            if "my preferences" in user_query.lower() or "what are my preferences" in user_query.lower():
                return f"Hello, {name}! 👋\n\n{self.format_preferences(user_preferences)}"

            relevance_prompt = (
                f"Does the following message relate to beverages, alcoholic drinks, or food pairings?\n"
                f"Message: '{user_query}'\n"
                "Reply only 'yes' or 'no'."
            )
            client = openai.OpenAI()
            relevance = client.chat.completions.create(
                model="gpt-4",
                messages=[
                    {"role": "system", "content": relevance_prompt},
                    {"role": "user", "content": relevance_prompt}
                ],
            ).choices[0].message.content.strip().lower()

            if "yes" not in relevance:
                return (
                    "🍇 I'm your sommelier assistant, so I specialize in wine, beer, cocktails, spirits, "
                    "and food pairings. Let me know if you have a question in that area! 😊"
                )

            preference_text = self.format_preferences(user_preferences)
            prompt = (
                f"You are a sommelier assistant. Here are the user's preferences:\n"
                f"{preference_text}\n\nUser query: {user_query}"
            )

            response = client.chat.completions.create(
                model="gpt-4",
                messages=[
                    {"role": "system", "content": prompt},
                    {"role": "user", "content": user_query},
                ],
            )

            return response.choices[0].message.content

        except openai.OpenAIError as e:
            print(f"❌ OpenAI API error: {type(e).__name__}: {e}")
            return f"Sorry, OpenAI encountered an error: {e}"

        except Exception as e:
            print(f"❌ Unexpected error: {e}")
            return "An unexpected error occurred while processing your request."


if __name__ == "__main__":
    assistant = ChatbotAssistant()
    test_user_id = "user_12345"

    print(assistant.query_assistant(test_user_id, "Hello"))
    print(assistant.query_assistant(test_user_id, "What are my preferences?"))
    print(assistant.query_assistant(test_user_id, "What preferences can I set?"))
    print(assistant.query_assistant(test_user_id, "I think I prefer Merlot for my wine."))
    print(assistant.query_assistant(test_user_id, "I'm vegan and I like sweet drinks."))
