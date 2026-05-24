import os
from dotenv import find_dotenv, load_dotenv
from langchain_gigachat.chat_models import GigaChat
from database_worker import ReviewManager  # БД
from langchain.schema import Document
from langchain.text_splitter import RecursiveCharacterTextSplitter
from chromadb.config import Settings
from langchain_gigachat.embeddings.gigachat import GigaChatEmbeddings
from langchain_chroma import Chroma
from langchain.chains import RetrievalQA

load_dotenv(find_dotenv())
llm = GigaChat(verify_ssl_certs=False)

# question = "В чем смысл жизни?"
question = 'Подарок'
print(llm.invoke(question).content)

# 0. Инициализируем БД
rm = ReviewManager()

# 1. Загружаем отзывы из БД
reviews = rm.get_all_reviews()
rm.close_connection()

# 2. Преобразуем отзывы в документы LangChain
documents = [
    Document(
        page_content=review["text"],
        metadata={
            "id": review["id"],
            "sku": review["sku"],
            "rating": review["rating"],
            "published_at": review["published_at"]
        }
    )
    for review in reviews if review["text"]  # на всякий случай фильтруем пустые
]

# 3. Дробим тексты на чанки
text_splitter = RecursiveCharacterTextSplitter(
    chunk_size=1000,
    chunk_overlap=200,
)
split_documents = text_splitter.split_documents(documents)

print(f"Загружено отзывов: {len(documents)}")
print(f"После разбиения на фрагменты: {len(split_documents)}")

# 4. Создадим БД эмбедингов
embeddings = GigaChatEmbeddings(verify_ssl_certs=False)

db = Chroma.from_documents(
    documents,
    embeddings,
    client_settings=Settings(anonymized_telemetry=False),
)

# 5. Сделаем поиск по векторной БД
docs = db.similarity_search(question, k=4)
print(len(docs))
print(f"... {str(docs[0])} ...")

# 6. Зададим QnA цепочку для ответов на вопросы по Бд
qa_chain = RetrievalQA.from_chain_type(llm, retriever=db.as_retriever())

print(qa_chain({"query": question}))