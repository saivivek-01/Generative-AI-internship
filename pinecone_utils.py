import os
from dotenv import load_dotenv
from pinecone import Pinecone

load_dotenv()

pc = Pinecone(api_key=os.getenv("PINECONE_API_KEY"))

# Skip index creation – assume it exists
index = pc.Index("edu-quiz")  # This must match your created index name

def store_student_answer(student_id, answer_text):
    embedding = [0.01] * 2048
    index.upsert(vectors=[(student_id, embedding)])