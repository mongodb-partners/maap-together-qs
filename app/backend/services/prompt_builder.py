def build_agent_prompt(config: dict, topic: str, context_data: dict) -> str:
    context_summary = "\n\n".join([
        f"{col}: {docs[:2]}" for col, docs in context_data.items()
    ])
    return f"""
You are {config['name']}, a {config['role']} who {config['description']}.
Your task is to respond to the following topic:
"{topic}"

Use insights from your assigned datasets:
{context_summary}

Respond based on your unique perspective ({config['role']}), and be prepared to challenge or support other agents.
Always provide a rationale for your responses and answer in brief within 50 words. Keep it concise and to the point.
Your response should be in the format:
Stance: **<Your stance here>**
Rationale: <Your rationale here>
"""