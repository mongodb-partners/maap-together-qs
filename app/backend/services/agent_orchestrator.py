import traceback
import asyncio
from services.mongo_client import fetch_agent_config, get_query_results, fetch_context_data
from services.prompt_builder import build_agent_prompt
from services.llm_caller import call_llm
from services.summarizer import summarize_debate

async def orchestrate_debate(topic: str, agents: dict, context_scope: list, aggregator_model: str) -> dict:
        try: 
            tasks = []
            agent_context = {}
            # Fetch data from MongoDB
            for collection in context_scope:
                if collection == "sales_data": 
                    # Fetch data from MongoDB
                    agent_context[collection] = await fetch_context_data(collection)
                else:
                    # Perform vector search
                    agent_context[collection] = await get_query_results(topic, collection)
                 
            for agent in agents: 
                config = await fetch_agent_config(agent)
                prompt = build_agent_prompt(config, topic, agent_context)
                tasks.append(call_llm(agents.get(agent), prompt, agent))

            responses = await asyncio.gather(*tasks)
            # print("Responses", responses)
            summary = await summarize_debate(topic, responses, aggregator_model)

            return {
                "topic": topic,
                "agents": [r['agent'] for r in responses],
                "responses": responses,
                "summary": summary
            }
        except Exception as e:
            error_traceback = traceback.format_exc()
            print(f"Error in orchestrating debate: {str(e)}\nTraceback:\n{error_traceback}")
            return {
                "error": str(e),
                "traceback": error_traceback
            }