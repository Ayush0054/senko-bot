import os
from dotenv import load_dotenv
import pinecone
from langchain_community.embeddings import OpenAIEmbeddings
from langchain_community.vectorstores import Pinecone
from langchain_community.llms import OpenAI
from langchain.chains import RetrievalQA

load_dotenv()

class RAGService:
    def __init__(self):
        self.embeddings = OpenAIEmbeddings()
        self.index_name = "discord-bot-index"
        self.llm = OpenAI(temperature=0)

    async def init_pinecone(self):
        pinecone.init(
            api_key=os.getenv("PINECONE_API_KEY"),
            environment=os.getenv("PINECONE_ENVIRONMENT")
        )
        if self.index_name not in pinecone.list_indexes():
            pinecone.create_index(self.index_name, dimension=1536)
        self.vectorstore = Pinecone.from_existing_index(self.index_name, self.embeddings)

    async def update_knowledge(self, text: str):
        self.vectorstore.add_texts([text])

    async def query(self, question: str):
        qa = RetrievalQA.from_chain_type(llm=self.llm, chain_type="stuff", retriever=self.vectorstore.as_retriever())
        return qa.run(question)