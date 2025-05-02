from fastapi import FastAPI
from pydantic import BaseModel
from dotenv import load_dotenv
from langchain_openai import ChatOpenAI
from langchain.schema import HumanMessage
import os

load_dotenv()
openai_api_key = os.getenv("OPENAI_API_KEY")

app = FastAPI()
llm = ChatOpenAI(openai_api_key=openai_api_key, model="gpt-3.5-turbo")

class ChatRequest(BaseModel):
    message: str

@app.post("/chat")
def chat(request: ChatRequest):
    response = llm([HumanMessage(content=request.message)])
    return {"response": response.content}
