import json
from fastapi import FastAPI, HTTPException
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from typing import List, Dict
from services.agent_orchestrator import orchestrate_debate
from services.mongo_client import load_data as load_data_mongo, generate_embeddings
import uvicorn
import os
from services.mongo_client import get_field_data, insert_field_data, create_vector_index

app = FastAPI()

class DebateRequest(BaseModel):
    topic: str
    agents: Dict[str, str]
    context_scope: List[str]
    aggregator_model: str

@app.post("/debate")
async def start_debate(request: DebateRequest):
    try:
        print("Request : ", request)
        result = await orchestrate_debate(request.topic, request.agents, request.context_scope, request.aggregator_model)
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    

@app.get("/load_data")
async def load_data():
    async def generate():
        try:
            # Loading data for each collection         
            files = [f for f in os.listdir('util') if f.endswith('.json')]
            for file in files:
                with open(os.path.join('util', file), 'r') as f:
                    data = json.load(f)
                    collection_name = file.split('.')[0]
                    yield f"Loading {collection_name}...\n"
                    load_data_mongo(collection_name, data)
                    yield f"{collection_name} loaded successfully!\n"
            
            # Creating vector embeddings
            yield f"Generating embeddings...\n"
            embedding_dict = {
                "customer_feedback": "feedback",
                "performance_logs" : "summary"
            }

            for collection, field in embedding_dict.items():
                # Create vector index for each collection
                await create_vector_index(collection)
                yield f"Creating vector index for {collection}...\n"
                collection_data = await get_field_data(collection, field)
                # print("Collection data", collection_data)
                for data in collection_data:
                    text = data[field]
                    embedding = generate_embeddings(text)
                    doc_id = data['_id']
                    await insert_field_data(collection, doc_id, "embedding", embedding)
                
                yield f"Vector index for {collection} created successfully!\n"
            
            

            yield "All data loaded and embeddings created successfully!\n"
 
        except Exception as e:
            raise HTTPException(status_code=500, detail=str(e))
    
    return StreamingResponse(generate(), media_type="text/plain")

@app.get("/health")
async def health_check():
    return {"status": "healthy"}

if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)