from openai import AsyncOpenAI
from dotenv import load_dotenv
import os

load_dotenv()

class OpenAIService:
    def __init__(self):
        self.client = AsyncOpenAI(api_key=os.getenv("OPENAI_API_KEY"))

    async def generate_response(self, prompt: str, context: str = ""):
        try:
            response = await self.client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=[
                    {"role": "system", "content": "You are a helpful assistant in a Discord server."},
                    {"role": "user", "content": f"Context: {context}\n\nUser query: {prompt}"}
                ]
            )
            return response.choices[0].message.content.strip()
        except Exception as e:
            print(f"Error in OpenAI API call: {e}")
            return "I'm sorry, I couldn't generate a response at the moment."