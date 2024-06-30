# from random import choice, randint


# def get_response(user_input: str) -> str:
#     lowered: str = user_input.lower()

#     if lowered == '':
#         return 'Well, you\'re awfully silent...'
#     elif 'hello' in lowered:
#         return 'Hello there!'
#     elif 'how are you' in lowered:
#         return 'Good, thanks!'
#     elif 'bye' in lowered:
#         return 'See you!'
#     elif 'roll dice' in lowered:
#         return f'You rolled: {randint(1, 6)}'
#     else:
#         return choice(['I do not understand...',
#                        'What are you talking about?',
#                        'Do you mind rephrasing that?'])
        
        
from openai import OpenAI
from typing import List, Dict
import re
import random
import os
from dotenv import load_dotenv


load_dotenv()


api_key = os.getenv("OPENAI_API_KEY")

if not api_key:
    raise ValueError("No OpenAI API key found. Please set the OPENAI_API_KEY environment variable.")

client = OpenAI(api_key=api_key)

class ResponseGenerator:
    def __init__(self):
        self.conversation_history: List[Dict[str, str]] = []
        self.max_history = 5  # Adjust based on your needs and token limits

    def get_response(self, user_input: str) -> str:
        # Add user input to conversation history
        self.conversation_history.append({"role": "user", "content": user_input})
        
        # Trim conversation history if it's too long
        if len(self.conversation_history) > self.max_history:
            self.conversation_history = self.conversation_history[-self.max_history:]

        try:
            # Generate response using GPT
            response = client.chat.completions.create(
                model="gpt-3.5-turbo",  # or another appropriate model
                messages=[
                    {"role": "system", "content": "You are a helpful Discord bot assistant. Respond concisely and engagingly."},
                    *self.conversation_history
                ],
                max_tokens=150  # Adjust based on your needs
            )

            bot_response = response.choices[0].message.content.strip()

            # Add bot response to conversation history
            self.conversation_history.append({"role": "assistant", "content": bot_response})

            # Handle special cases
            if re.search(r'\broll\s+dice\b', user_input, re.IGNORECASE):
                dice_result = random.randint(1, 6)
                bot_response += f"\n\nOh, you want to roll a dice? You rolled: {dice_result}"

            return bot_response

        except Exception as e:
            print(f"Error in generating response: {e}")
            return random.choice([
                "I'm having trouble processing that right now. Could you try again?",
                "Oops, something went wrong on my end. Let's try a different topic!",
                "I didn't quite catch that. Could you rephrase your message?"
            ])

# Initialize the ResponseGenerator
response_gen = ResponseGenerator()

def get_response(user_input: str) -> str:
    return response_gen.get_response(user_input)

# Example usage
if __name__ == "__main__":
    print(get_response("Hello! How are you today?"))
    print(get_response("Tell me a joke about programming."))
    print(get_response("Can you roll a dice for me?"))