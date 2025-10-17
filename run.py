import google.generativeai as genai
import os

genai.configure(api_key="AIzaSyADlBTWfleg_PLTvOZ23l-6mVu4mmHNrNE")

model = genai.GenerativeModel("gemini-2.5-flash")

def chat():
    print("💬 Gemini Chat (type 'exit' to quit)\n")
    history = []

    while True:
        user_input = input("You: ")
        if user_input.lower() in {"exit", "quit"}:
            print("👋 Goodbye!")
            break

        history.append({"role": "user", "parts": [user_input]})

        response = model.generate_content(history)

        reply = response.text
        print(f"Gemini: {reply}\n")

        # Add assistant reply to history
        history.append({"role": "model", "parts": [reply]})

if __name__ == "__main__":
    chat()