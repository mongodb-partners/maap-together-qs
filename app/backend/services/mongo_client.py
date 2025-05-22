import motor.motor_asyncio
from bson.json_util import dumps
import os
from typing import List
from together import AsyncTogether, Together
from pymongo.operations import SearchIndexModel
from dotenv import load_dotenv
load_dotenv()

from services.llm_caller import generate_embeddings

client = motor.motor_asyncio.AsyncIOMotorClient(os.getenv("MONGODB_URI"))
db = client[os.getenv("DATABASE_NAME")]

async def fetch_context_data(collection: str):
    """Fetch context data from MongoDB collection."""
    try:
        # for name in collections:
        data = await db[collection].find(
            {},{"_id": 0}
        ).limit(10).to_list(length=None)
        return data
    except Exception as e:
        raise RuntimeError(f"Error fetching context data: {str(e)}")


def load_data(collection_name: str, data: List[dict]) -> None:
    """Load data into MongoDB collection."""
    try:
        collection = db[collection_name]
        # Insert new data
        if data:
            collection.insert_many(data)
    except Exception as e:
        raise RuntimeError(f"Error loading data into {collection_name}: {str(e)}")


async def get_query_results(query, collection: str) -> List[dict]:
    """Gets results from a vector search query.
    Args:
        query (str): The query string to search for.
        collections (list): List of collection names to search in.
    Returns:
        List[dict]: A list of dictionaries containing the search results.
    """
    query_embedding = await generate_embeddings(query)
    pipeline = [
        {
            "$vectorSearch": {
                "index": "vector_index",
                "queryVector": query_embedding,
                "path": "embedding",
                "numCandidates": 10,
                "limit": 2
            }
        }, {
            "$project": {
                "_id": 0,
                "summary": 1,
                "feedback": 1
            }
        }
    ]
    
    results = db[collection].aggregate(pipeline)
    array_of_results = []
    array_of_results = await results.to_list(length=None)
    
    return array_of_results


async def get_field_data(collection_name: str, field_name: str):
    """Fetch data for a specific field from a MongoDB collection.
    
    Args:
        collection_name (str): Name of the collection to query
        field_name (str): Name of the field to retrieve
        return_json (bool): If True returns JSON, if False returns text
        
    Returns:
        Union[str, dict]: Data in either JSON or text format
    """
    try:
        collection = db[collection_name]
        data = await collection.find({}, {field_name: 1}).to_list(length=None)    
        return data
       
    except Exception as e:
        raise RuntimeError(f"Error fetching field data: {str(e)}")


async def insert_field_data(collection_name: str, doc_id: str, field_name: str, field_value: any) -> bool:
    """Insert a new field in a document by its _id.
    
    Args:
        collection_name (str): Name of the collection
        doc_id (str): The _id of the document
        field_name (str): Name of the new field to insert
        field_value (any): Value for the new field
        
    Returns:
        bool: True if insert successful, False otherwise
    """
    try:
        collection = db[collection_name]
        result = await collection.update_one(
            {"_id": doc_id},
            {"$set": {field_name: field_value}},
            upsert=False
        )
        return result.upserted_id is not None or result.modified_count > 0
    except Exception as e:
        raise RuntimeError(f"Error inserting field data: {str(e)}")


async def create_vector_index(collection_name: str, field_name: str = "embedding") -> bool:
    """Create a vector index on a MongoDB collection field.
    
    Args:
        collection_name (str): Name of the collection
        field_name (str): Name of the field to index
        
    Returns:
        bool: True if index creation successful, False otherwise
    """
    try:
        collection = db[collection_name]

        search_index_model = SearchIndexModel(
            definition={
                "fields": [
                    {
                        "type": "vector",
                        "numDimensions": 768,
                        "path": field_name,
                        "similarity": "cosine"
                    }
                ]},
            name="vector_index",
            type="vectorSearch"
        )
        await collection.create_search_index(model=search_index_model)
        print("New search index on " + collection_name +" is building.")
        return True
    
    except Exception as e:
        raise RuntimeError(f"Error creating vector index: {str(e)}")

async def fetch_agent_config(agent_name: str) -> dict:  
    """Fetch agent configuration from MongoDB.
    Args:
        agent_name (str): The name of the agent to fetch.
    Returns:
        dict: The agent configuration.
    """
    return await db.agents.find_one({"name": agent_name})