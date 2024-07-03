import discord
from discord.ext import commands
from pinecone import Pinecone
from openai import OpenAI
import os
from dotenv import load_dotenv


load_dotenv()

intents = discord.Intents.default()
intents.message_content = True
bot = commands.Bot(command_prefix='!', intents=intents)



pinecone = Pinecone(api_key=os.getenv('PINECONE_API_KEY'))
index = pinecone.Index(os.getenv('PINECONE_INDEX_NAME'))



openai = OpenAI(api_key=os.getenv('OPENAI_API_KEY'))
def get_embedding(text):
    response = openai.embeddings.create(
        input=text,
        model="text-embedding-3-small"
    )
    return response.data[0].embedding

@bot.event
async def on_ready():
    print(f'{bot.user} has connected to Discord!')

@bot.event
async def on_message(message):
    if message.author == bot.user:
        return

   
    content = message.content
    author = str(message.author)
    channel = str(message.channel)
    timestamp = str(message.created_at)

   
    combined_text = f"{author} in {channel} at {timestamp}: {content}"

   
    embedding = get_embedding(combined_text)

    
    index.upsert(vectors=[(str(message.id), embedding, {"content": content, "author": author, "channel": channel, "timestamp": timestamp})])

    print(f"Stored message from {channel}: {content}")

    
    if message.content.endswith('?'):
        await answer_question(message)

    await bot.process_commands(message)

async def answer_question(message):

    question_embedding = get_embedding(message.content)

    results = index.query(vector=question_embedding, top_k=5, include_metadata=True)

 
    context = "\n".join([f"{match['metadata']['author']} in {match['metadata']['channel']}: {match['metadata']['content']}" for match in results['matches']])

   
    response = openai.chat.completions.create(
        model="gpt-3.5-turbo",
        messages=[
            {"role": "system", "content": "You are a helpful assistant answering questions based on Discord chat history from various channels."},
            {"role": "user", "content": f"Based on the following context, answer the question: '{message.content}'\n\nContext:\n{context}"}
        ]
    )

 
    answer = response.choices[0].message.content
    await message.channel.send(f"Here's what I found based on discussions across all channels:\n{answer}")

@bot.command(name='search')
async def search_messages(ctx, query: str):
   
    query_embedding = get_embedding(query)


    results = index.query(vector=query_embedding, top_k=5, include_metadata=True)

   
    for match in results['matches']:
        metadata = match['metadata']
        await ctx.send(f"Match (score: {match['score']:.2f}):\n"
                       f"{metadata['author']} in {metadata['channel']} at {metadata['timestamp']}:\n"
                       f"{metadata['content']}")

bot.run(os.getenv('DISCORD_TOKEN'))