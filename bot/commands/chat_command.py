from discord.ext import commands
from services.openai_service import OpenAIService
from services.message_store import MessageStore
from services.rag_service import RAGService
import os

class ChatCommands(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.openai_service = OpenAIService()
        self.message_store = MessageStore(os.getenv("DATABASE_URL"))
        self.rag_service = RAGService()

    @commands.command()
    async def chat(self, ctx, *, message: str):
        # Retrieve recent messages for context
        recent_messages = await self.message_store.get_recent_messages(
            str(ctx.guild.id), str(ctx.channel.id)
        )
        context = "\n".join([f"{msg.user_id}: {msg.content}" for msg in recent_messages])

        # Generate response using OpenAI
        response = await self.openai_service.generate_response(message, context)

        # Store the new message and response
        await self.message_store.store_message(
            str(ctx.guild.id), str(ctx.channel.id), str(ctx.author.id), message, ctx.message.created_at
        )
        await self.message_store.store_message(
            str(ctx.guild.id), str(ctx.channel.id), str(self.bot.user.id), response, ctx.message.created_at
        )

        # Update RAG knowledge
        await self.rag_service.update_knowledge(f"{message}\n{response}")

        await ctx.send(response)

    @commands.command()
    async def rag_query(self, ctx, *, question: str):
        response = await self.rag_service.query(question)
        await ctx.send(response)

def setup(bot):
    bot.add_cog(ChatCommands(bot))