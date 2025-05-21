import httpx
import os
from together import AsyncTogether, Together


TOGETHER_API_KEY = os.getenv("TOGETHER_API_KEY")

async_client = AsyncTogether(api_key=TOGETHER_API_KEY)

async def generate_embeddings(text: str, model: str = "togethercomputer/m2-bert-80M-32k-retrieval") -> list:
    """Generate embeddings for given text using Together AI."""
    response = await async_client.embeddings.create(
        model=model,
        input=text
    )
    return response.data[0].embedding

async def call_llm(model: str, prompt: str, agent_name: str) -> dict:
    """Run a single LLM call with a reference model."""
    response = await async_client.chat.completions.create(
        model=model,
        messages=[{"role": "user", "content": prompt}],
        temperature=0.7,
        max_tokens=512,
    )
    
    print("Response from : ", model, ": " , response)
    return {
                "agent": agent_name,
                "model": model,
                "response": response.choices[0].message.content
            }