import os
from dotenv import load_dotenv
from langchain_openai import ChatOpenAI
from langchain.schema import HumanMessage


openai_api_key = os.getenv("OPENAI_API_KEY")

load_dotenv()

llm = ChatOpenAI(model_name="gpt-3.5-turbo", temperature=0.7)

while True:
    user_input = input("You: ")
    if user_input.lower() in ["exit", "quit"]:
        break
    response = llm([HumanMessage(content=user_input)])
    print("Bot:", response.content)