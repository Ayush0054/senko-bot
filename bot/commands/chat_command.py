from discord.ext import commands
from services.openai_service import OpenAIService
from services.message_store import MessageStore
from services.rag_service import RAGService
import os
import logging
import datetime

class ChatCommands(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.openai_service = OpenAIService()
        self.message_store = MessageStore(os.getenv("DATABASE_URL"))
        self.rag_service = RAGService()

    async def cog_load(self):
        await self.rag_service.init_pinecone()

    @commands.command()
    async def chat(self, ctx, *, message: str):
        logging.info("Received !chat command")
        
        if self.rag_service.vectorstore is None:
            await ctx.send("The RAG service is still initializing. Please try again in a moment.")
            return

        # Retrieve recent messages for context
        recent_messages = await self.message_store.get_recent_messages(
            str(ctx.guild.id), str(ctx.channel.id)
        )
        context = "\n".join([f"{msg.user_id}: {msg.content}" for msg in recent_messages])

        # Generate response using OpenAI
        response = await self.openai_service.generate_response(message, context)

        # Get current time as naive datetime
        current_time = datetime.datetime.now(datetime.timezone.utc).replace(tzinfo=None)

        # Store the new message and response
        await self.message_store.store_message(
            str(ctx.guild.id), str(ctx.channel.id), str(ctx.author.id), message, current_time
        )
        await self.message_store.store_message(
            str(ctx.guild.id), str(ctx.channel.id), str(self.bot.user.id), response, current_time
        )

        # Update RAG knowledge
        await self.rag_service.update_knowledge(f"{message}\n{response}")

        await ctx.send(response)

    @commands.command()
    async def rag_query(self, ctx, *, question: str):
        logging.info("Received !rag_query command")
        
        if self.rag_service.vectorstore is None:
            await ctx.send("The RAG service is still initializing. Please try again in a moment.")
            return

        response = await self.rag_service.query(question)
        await ctx.send(response)

async def setup(bot):
    logging.info("Setting up ChatCommands cog")
    await bot.add_cog(ChatCommands(bot))
    logging.info("ChatCommands cog loaded")