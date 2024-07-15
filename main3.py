import discord
from discord.ext import commands
from pinecone import Pinecone
from openai import OpenAI
import os
import random
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Discord setup
intents = discord.Intents.default()
intents.message_content = True
intents.members = True
intents.reactions = True
bot = commands.Bot(command_prefix='!', intents=intents)

# Pinecone setup
pinecone = Pinecone(api_key=os.getenv('PINECONE_API_KEY'))
index = pinecone.Index(os.getenv('PINECONE_INDEX_NAME'))

# OpenAI setup
openai = OpenAI(api_key=os.getenv('OPENAI_API_KEY'))

# Define emoji categories
EMOTION_EMOJIS = {
    'happy': ['😄', '😊', '🎉', '👍', '🥳'],
    'sad': ['😢', '😔', '💔', '🤧', '😿'],
    'angry': ['😠', '😡', '🤬', '💢', '👿'],
    'surprise': ['😲', '😮', '🤯', '😱', '🙀'],
    'neutral': ['🤔', '😐', '🧐', '🤨', '😶'],
    'science': ['🧪', '🔬', '💡', '🤖', '🧠']
}

def get_embedding(text):
    response = openai.embeddings.create(
        input=text,
        model="text-embedding-3-small"
    )
    return response.data[0].embedding

async def analyze_sentiment(text):
    response = openai.chat.completions.create(
        model="gpt-4o",
        messages=[
            {"role": "system", "content": "You are a sentiment analysis expert. Categorize the following text as 'happy', 'sad', 'angry', 'surprise', or 'neutral'. Respond with only the category name."},
            {"role": "user", "content": text}
        ]
    )
    return response.choices[0].message.content.lower().strip()

async def choose_reaction(message):
    content = message.content.lower()
    
    # Check for science-related keywords
    science_keywords = ['science', 'experiment', 'research', 'lab', 'discovery', 'innovation', 'technology']
    if any(keyword in content for keyword in science_keywords):
        return random.choice(EMOTION_EMOJIS['science'])

    # Analyze sentiment using OpenAI
    sentiment = await analyze_sentiment(content)
    return random.choice(EMOTION_EMOJIS.get(sentiment, EMOTION_EMOJIS['neutral']))

@bot.event
async def on_ready():
    print(f'{bot.user} has connected to Discord!')
    await bot.change_presence(activity=discord.Game(name="Science!"))
    
# @bot.command(name="l")
# async def members(ctx):
#     for guild in bot.guilds:
#         for member in guild.members:
#             print(member)    
@bot.event
async def on_guild_join(guild):
    general = discord.utils.find(lambda x: x.name == 'general', guild.text_channels)
    if general and general.permissions_for(guild.me).send_messages:
        commands_list = [
            "- !s [message] - Store a context/memory in the database\n",
            "- you can ask message ending with '?' to get response with your context/memory\n",
            "- !search [query] - Search for stored context/memory\n",
            "- You can  mention me  to get a response\n",
            
        ]
        
        welcome_message = (
            f"Greetings, fellow scientists! I am Senku, your brilliant AI assistant.\n"
            f"Here are the commands you can use:\n\n" + "\n".join(commands_list)
        )
        
        await general.send(welcome_message)
@bot.event
async def on_message(message):
    if message.author == bot.user:
        return
    if random.random() < 0.5: 
        try:
            reaction = await choose_reaction(message)
            await message.add_reaction(reaction)
        except discord.errors.HTTPException:
            pass


    if bot.user.mentioned_in(message):
        async with message.channel.typing():
            await answer_question(message, str(message.guild.id), with_context=False, is_mention=True)
    
  
    elif message.content.endswith('?'):
        async with message.channel.typing():
            await answer_question(message, str(message.guild.id), with_context=True, is_mention=False)

    await bot.process_commands(message)

@bot.command(name='s')
async def store_message(ctx, *, content):
    async with ctx.typing():
        author = str(ctx.author)
        channel = str(ctx.channel)
        timestamp = str(ctx.message.created_at)
        server_id = str(ctx.guild.id)

        combined_text = f"{author} in {channel} at {timestamp}: {content}"
        embedding = get_embedding(combined_text)

        index.upsert(
            vectors=[(str(ctx.message.id), embedding, {"content": content, "author": author, "channel": channel, "timestamp": timestamp})],
            namespace=server_id
        )

        print(f"Stored message from {channel} in server {server_id}: {content}")
        await ctx.reply("Message stored successfully! 🧠💾")

@bot.command(name='search')
async def search_messages(ctx, *, query: str):
    async with ctx.typing():
        server_id = str(ctx.guild.id)
        query_embedding = get_embedding(query)

        results = index.query(
            vector=query_embedding,
            top_k=5,
            include_metadata=True,
            namespace=server_id
        )

        if results['matches']:
            response = "Here are the matches I found:\n\n"
            for match in results['matches']:
                metadata = match['metadata']
                response += f"Match (score: {match['score']:.2f}):\n"
                response += f"{metadata['author']} in {metadata['channel']} at {metadata['timestamp']}:\n"
                response += f"{metadata['content']}\n\n"
            await ctx.reply(response)
        else:
            await ctx.reply("No matching messages found. 🕵️‍♂️")

async def answer_question(message, server_id, with_context=False, is_mention=False):
    question = message.content
    
    if is_mention:
        # Remove the bot mention from the question
        question = question.replace(f'<@!{bot.user.id}>', '').replace(f'<@{bot.user.id}>', '').strip()
    
    system_message = "You are Senku , You're confident, logical, and occasionally sarcastic. You have vast scientific knowledge and approach problems analytically."

    if with_context and not is_mention:
        question_embedding = get_embedding(question)
        results = index.query(
            vector=question_embedding,
            top_k=5,
            include_metadata=True,
            namespace=server_id
        ) 
        context = "\n".join([f"{match['metadata']['author']} in {match['metadata']['channel']}: {match['metadata']['content']}" for match in results['matches']])
        system_message += " Use the provided context to inform your answer if relevant."
        user_content = f"Based on the following context, respond to this message: '{question}'\n\nContext:\n{context}"
    else:
        user_content = question

    response = openai.chat.completions.create(
        model="gpt-4o",
        messages=[
            {"role": "system", "content": system_message},
            {"role": "user", "content": user_content}
        ]
    )

    answer = response.choices[0].message.content
    await message.reply(answer)

bot.run(os.getenv('DISCORD_TOKEN'))