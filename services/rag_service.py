import os
from dotenv import load_dotenv
from pinecone import Pinecone, ServerlessSpec
from langchain_community.embeddings import OpenAIEmbeddings
from langchain_community.vectorstores import Pinecone as LangchainPinecone
from langchain_community.llms import OpenAI
from langchain.chains import RetrievalQA

load_dotenv()

class RAGService:
    def __init__(self):
        self.embeddings = OpenAIEmbeddings()
        self.index_name = "discord-bot-index"
        self.llm = OpenAI(temperature=0)
        self.pc = Pinecone(api_key=os.getenv("PINECONE_API_KEY"))
        self.vectorstore = None

    async def init_pinecone(self):
        try:
            if self.index_name not in self.pc.list_indexes().names():
                self.pc.create_index(
                    name=self.index_name,
                    dimension=1536,  # This should match your OpenAI embeddings dimension
                    metric='cosine',
                    spec=ServerlessSpec(
                        cloud="aws",
                        region="us-east-1"  # You can change this to your preferred region
                    )
                )
                print(f"Created new Pinecone index: {self.index_name}")
            else:
                print(f"Pinecone index {self.index_name} already exists")

            self.vectorstore = LangchainPinecone.from_existing_index(
                self.index_name, 
                self.embeddings
            )
        except Exception as e:
            print(f"Error initializing Pinecone: {e}")
            raise

    async def update_knowledge(self, text: str):
        if self.vectorstore is None:
            raise ValueError("Vectorstore is not initialized. Call init_pinecone() first.")
        try:
            self.vectorstore.add_texts([text])
        except Exception as e:
            print(f"Error updating knowledge: {e}")
            raise

    async def query(self, question: str):
        if self.vectorstore is None:
            raise ValueError("Vectorstore is not initialized. Call init_pinecone() first.")
        try:
            qa = RetrievalQA.from_chain_type(
                llm=self.llm, 
                chain_type="stuff", 
                retriever=self.vectorstore.as_retriever()
            )
            return qa.run(question)
        except Exception as e:
            print(f"Error querying: {e}")
            raise
