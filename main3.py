
import discord
from discord.ext import commands
from pinecone import Pinecone
from openai import OpenAI
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Discord setup
intents = discord.Intents.default()
intents.message_content = True
bot = commands.Bot(command_prefix='!', intents=intents)

# Pinecone setup
pinecone = Pinecone(api_key=os.getenv('PINECONE_API_KEY'))
index = pinecone.Index(os.getenv('PINECONE_INDEX_NAME'))

# OpenAI setup
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
    print(message.author)
    print(bot.user)
    if message.author == bot.user:
        return
    if message.content.endswith('?'):
         await answer_question(message.channel, message.content, str(message.guild.id))
    await bot.process_commands(message)

@bot.command(name='s')
async def store_message(ctx, *, content):
    # Process the message
    author = str(ctx.author)
    channel = str(ctx.channel)
    timestamp = str(ctx.message.created_at)
    server_id = str(ctx.guild.id)

    # Create a combined string for embedding
    combined_text = f"{author} in {channel} at {timestamp}: {content}"

    # Generate embedding using OpenAI
    embedding = get_embedding(combined_text)

    # Store in Pinecone with server-specific namespace
    index.upsert(
        vectors=[(str(ctx.message.id), embedding, {"content": content, "author": author, "channel": channel, "timestamp": timestamp})],
        namespace=server_id
    )

    print(f"Stored message from {channel} in server {server_id}: {content}")
    await ctx.send("Message stored successfully!")

@bot.command(name='search')
async def search_messages(ctx, *, query: str):
    server_id = str(ctx.guild.id)
    
    # Generate embedding for the query
    query_embedding = get_embedding(query)

    # Search Pinecone using server-specific namespace
    results = index.query(
        vector=query_embedding,
        top_k=5,
        include_metadata=True,
        namespace=server_id
    )

    # Send results back to Discord
    if results['matches']:
        for match in results['matches']:
            metadata = match['metadata']
            await ctx.send(f"Match (score: {match['score']:.2f}):\n"
                           f"{metadata['author']} in {metadata['channel']} at {metadata['timestamp']}:\n"
                           f"{metadata['content']}")
    else:
        await ctx.send("No matching messages found.")

async def answer_question(channel, question, server_id):
    # Generate embedding for the question
    question_embedding = get_embedding(question)

    # Search Pinecone for relevant messages using server-specific namespace
    results = index.query(
        vector=question_embedding,
        top_k=5,
        include_metadata=True,
        namespace=server_id
    ) 

    # Prepare context from relevant messages
    context = "\n".join([f"{match['metadata']['author']} in {match['metadata']['channel']}: {match['metadata']['content']}" for match in results['matches']])

    # Use OpenAI to generate an answer
    response = openai.chat.completions.create(
        model="gpt-4o",
        messages=[
            {"role": "system", "content": "You are Senku, acting as the brain for this specific Discord server.  Use your vast knowledge and analytical skills to answer questions based on the context provided from this server only. If you can't find the answer in the context, say I don't have enough information to answer that question based on this server's context.Do not use any information that is not provided in the context."},
            {"role": "user", "content": f"Based on the following context, answer the question: '{question}'\n\nContext:\n{context}"}
        ]
    )

    # Send the answer back to Discord
    answer = response.choices[0].message.content
    await channel.send(f"Here's what I found based on discussions in this server:\n{answer}")

bot.run(os.getenv('DISCORD_TOKEN'))
