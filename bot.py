import boto3
import os
import sys
import openai
from langchain.chains import ConversationalRetrievalChain, RetrievalQA
from langchain.chat_models import ChatOpenAI
from langchain.document_loaders import DirectoryLoader, TextLoader
from langchain.embeddings import OpenAIEmbeddings
from langchain.indexes import VectorstoreIndexCreator
from langchain.indexes.vectorstore import VectorStoreIndexWrapper
from langchain.llms import OpenAI
from langchain.vectorstores import Chroma
import constants

os.environ["OPENAI_API_KEY"] = constants.APIKEY

# Enable to save to disk & reuse the model (for repeated queries on the same data)
PERSIST = False

query = None

# Configure AWS S3 client
s3 = boto3.client('s3', aws_access_key_id=constants.ACCESS_KEY,
                  aws_secret_access_key=constants.SECRET_ACCESS_KEY)

if PERSIST and os.path.exists("persist"):
    print("Reusing index...\n")
    vectorstore = Chroma(persist_directory="persist", embedding_function=OpenAIEmbeddings())
    index = VectorStoreIndexWrapper(vectorstore=vectorstore)
else:
    loader = DirectoryLoader("data/", glob='**/*.txt')
    if PERSIST:
        index = VectorstoreIndexCreator(vectorstore_kwargs={"persist_directory": "persist"}).from_loaders([loader])
    else:
        index = VectorstoreIndexCreator().from_loaders([loader])

chain = ConversationalRetrievalChain.from_llm(
    llm=ChatOpenAI(model="gpt-3.5-turbo"),
    retriever=index.vectorstore.as_retriever(search_kwargs={"k": 1}),
)

chat_history = []

def get_chatbot_response(prompt):
    result = chain({"question": prompt, "chat_history": chat_history})
    return result['answer']

def save_chat_history_to_s3():
    bucket_name = 'mybothistory'
    file_name = 'chat_history.txt'

    # Generate chat history text
    chat_text = "\n".join([f"User: {query}\nChatbot: {response}\n" for query, response in chat_history])

    # Save chat history to S3
    s3.put_object(Body=chat_text, Bucket=bucket_name, Key=file_name)
