from services.llm_caller import call_llm

async def summarize_debate(topic: str, agent_responses: list, aggregator_model) -> str:
    compiled = "\n\n".join([f"{r['agent']}: {r['response']}" for r in agent_responses])
    prompt = f"""
You are a debate moderator.
Summarize the debate on: "\033[32m{topic}\033[0m", make a final decision, and provide a detailed rationale. 
Here are the arguments from each agent:
\033[32m{compiled}\033[0m

Only suggest a final stance and rationale, no other information.
The summary should be in the format:
Final Stance: **<Your stance here>**
Rationale: <Your detailed rationale here>
"""
    result = await call_llm(aggregator_model, prompt, "Moderator")
    print("Summary", result)
    return result['response']