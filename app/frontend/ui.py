import gradio as gr
import requests
from get_models import get_together_models
import os
import json
from dotenv import load_dotenv
load_dotenv()

# Define agent personas
AGENT_PERSONAS = {
    "Nova": "Advocates for innovation and future potential.",
    "Zeta": "Identifies flaws, risks, and uncertainties.",
    "Axel": "Focuses on factual data and trends."
}

# Available LLM models
LLM_MODELS = get_together_models(os.getenv("TOGETHER_API_KEY"))
LLM_MODELS_ID = [model["id"] for model in LLM_MODELS if model["type"]== "chat" or model["type"]== "language"]

IPV4 = os.getenv("IPV4") 
BASE_URL = f"http://{IPV4}"

def process_all_agents(message, nova_model, zeta_model, axel_model, aggregator_model, collection_names):
    responses = {}
    agent_models = {"Nova": nova_model, "Zeta": zeta_model, "Axel": axel_model}
    print(agent_models)
    url = f"{BASE_URL}/debate"

    payload = json.dumps({
        "topic": message,
        "agents": agent_models,
        "context_scope": collection_names,
        "aggregator_model": aggregator_model
    })
    headers = {
    'Content-Type': 'application/json'
    }

    print("Payload: ", payload)
    try :
        response = requests.request("POST", url, headers=headers, data=payload)
        if response.status_code == 200 : 
            print(response.json())
            response_data = response.json()['responses'] 
        else:
            raise gr.Error("Error: " + response.json().get("error", response.text))
        for i in range(len(response_data)):
            responses[response_data[i]['agent']] = response_data[i]['response']

        responses["Aggregator"] = response.json().get("summary", "No response from server")
            
                
        return  [{"role" : "assistant" , "content" : responses["Nova"] }],\
                [{"role" : "assistant" , "content" : responses["Zeta"] }],\
                [{"role" : "assistant" , "content" : responses["Axel"] }], \
                [{"role" : "assistant" , "content" : responses["Aggregator"] }]

    except Exception as e:
        responses = f"Error connecting to backend: {str(e)}"
        raise gr.Error(f"Error: {str(e)}")

with gr.Blocks(theme=gr.themes.Soft()) as demo:
    with gr.Tabs():
        with gr.TabItem("Home"):
            gr.Markdown(
                """
                <div style="text-align: center; font-size: 2.5em; font-weight: bold; color: #4A90E2; margin-top: 20px;">
                    🤖 AI Board Meeting Analytics System
                </div>

                <p style="text-align: center; font-size: 1.2em; margin-bottom: 30px; color: #DDE6F0;">
                    Welcome to your virtual executive boardroom—where powerful AI agents collaborate like seasoned executives to drive data-informed, strategic business decisions.
                </p>

                <div style="font-size: 1.1em; color: #CCCCCC; margin-bottom: 30px;">
                    In this immersive environment, each AI functions as a domain expert, offering distinct perspectives to help you evaluate business scenarios, assess risks, and unlock opportunities for growth. With their combined insights, you gain a multi-dimensional view that empowers confident decision-making.
                </div>

                <hr style="margin: 40px 0; border: 1px solid #333;">

                <div style="font-size: 1.4em; font-weight: bold; color: #FFFFFF; margin-bottom: 20px;">
                    🧠 Meet Your AI Board Members
                </div>

                <div style="margin-bottom: 30px;">
                    <h3 style="color: #4FC3F7;">🎯 Nova: The Data-Driven Director</h3>
                    <p style="color: #BBBBBB;">
                        Nova thrives on innovation and future-focused thinking. Constantly analyzing real-time data and emerging market trends, Nova identifies scalable growth opportunities and offers insights grounded in evidence. Whether you're exploring a new initiative or refining a product roadmap, Nova brings clarity through data-backed recommendations.
                    </p>
                </div>

                <div style="margin-bottom: 30px;">
                    <h3 style="color: #FFD54F;">💡 Zeta: The Creative Strategist</h3>
                    <p style="color: #BBBBBB;">
                        Zeta brings a fresh, analytical perspective to the table, focusing on identifying risks, market uncertainties, and competitive threats. With a sharp eye for potential pitfalls and strategic misalignments, Zeta challenges assumptions and proposes bold, unconventional approaches that balance creativity with critical evaluation.
                    </p>
                </div>

                <div style="margin-bottom: 30px;">
                    <h3 style="color: #81C784;">⚙️ Axel: The Technical Implementation Expert</h3>
                    <p style="color: #BBBBBB;">
                        Axel specializes in evaluating the technical feasibility of ideas and initiatives. With a deep understanding of engineering constraints, system architecture, and historical performance trends, Axel provides realistic timelines, estimates resource needs, and highlights potential implementation challenges. Axel ensures that ideas are not only visionary but also executable.
                    </p>
                </div>

                <hr style="margin: 40px 0; border: 1px solid #333;">

                <div style="font-size: 1.4em; font-weight: bold; color: #FFFFFF; margin-bottom: 20px;">
                    🚀 How It Works
                </div>

                <div style="font-size: 1.4em; color: #CCCCCC;">
                    <p><strong>Step 1:</strong> Enter your business question or strategic challenge.</p>
                    <p><strong>Step 2:</strong> Select relevant data sources or upload supporting documents.</p>
                    <p><strong>Step 3:</strong> Assign AI models to each board member—or use the default expert configuration.</p>
                    <p><strong>Step 4:</strong> Receive a comprehensive, board-style response combining creativity, logic, feasibility, and foresight.</p>
                </div>

                <p style="margin-top: 30px; font-size: 1.2em; text-align: center; color: #DDE6F0;">
                    Whether you're planning a product launch, entering a new market, or evaluating a high-stakes pivot, your AI board is ready to collaborate.
                </p>
                <p style="text-align: center; font-size: 1.2em; color: #DDE6F0;">
                    <strong>Let's get started!</strong>
                </p>
                """
            )
            gr.Image("TogetherAI.drawio.png", show_label=False)

        with gr.TabItem("Upload Data"):
            gr.Markdown(
                """
                <div style="text-align: center; font-size: 2em; font-weight: bold; color: #4A90E2;">
                    📤 Data Configuration
                </div>
                <p style="text-align: center; font-size: 1.2em; margin-bottom: 30px; color: #DDE6F0;">
                    View MongoDB connection and load sample data for analysis.
                </p>
                """
            )
            with gr.Row():
                def mask_mongodb_uri(uri):
                    if not uri or uri == "Not configured":
                        return uri, uri
                    try:
                        # Replace credentials with asterisks while keeping the structure
                        parts = uri.split('@')
                        if len(parts) > 1:
                            credentials = parts[0].split('://')
                            if len(credentials) > 1:
                                masked = f"{credentials[0]}://*****:*****@{parts[1]}"
                                return masked
                    except:
                        return "Invalid URI format"
                    return uri

                mongodb_uri = gr.Textbox(
                    value=mask_mongodb_uri(os.getenv("MONGODB_URI", "Not configured")),
                    label="MongoDB URI",
                    interactive=False,
                    show_copy_button=True
                )
            
            with gr.Row():
                load_btn = gr.Button("Load Sample Data", variant="primary")

            with gr.Row():
                console_output = gr.Textbox(
                    label="Console Output",
                    placeholder="Operation results will appear here...",
                    interactive=False
                )

            def load_sample_data():
                try:
                    response = requests.get(f"{BASE_URL}/load_data")
                    if response.status_code == 200:
                        return gr.update(value=response.text)
                    else:
                        raise gr.Error(f"Error: {response.text}")
                except Exception as e:
                    raise gr.Error(f"Error loading sample data: {str(e)}")

            load_btn.click(
                fn=load_sample_data,
                outputs=console_output
            )

        with gr.TabItem("Chat with Agents"):

            with gr.Group():
                prompt = gr.Textbox(
                    label="Your Question",
                    placeholder="Enter your question here...",
                    scale=40
                )
                submit_btn = gr.Button("🚀 Get Analysis", variant="primary")
            
            # Add dropdown for selecting collection names
            # with gr.Row():
            collection_names = ["customer_feedback", "sales_data", "performance_logs"]
            collection_selector = gr.Dropdown(
                choices=collection_names,
                value=collection_names[1],
                label="Data Collection",
                multiselect=True,
                scale=2,
                interactive=True
            )
            # with gr.Tabs():
            # with gr.TabItem("Individual Responses"):
            with gr.Row():
                with gr.Column():
                    nova_model_selector = gr.Dropdown(
                        choices=LLM_MODELS_ID,
                        value=LLM_MODELS_ID[0],
                        label="Nova",
                        scale=1
                    )
                    nova_output = gr.Chatbot(type="messages")
                    gr.Markdown(f"*{AGENT_PERSONAS['Nova']}*")
                with gr.Column():
                    zeta_model_selector = gr.Dropdown(
                        choices=LLM_MODELS_ID,
                        value=LLM_MODELS_ID[0],
                        label="Zeta",
                        scale=1
                    )
                    # zeta_output = gr.Textbox(
                    #     label="Zeta's Response",
                    #     lines=5,
                    #     scale=1
                    # )
                    zeta_output = gr.Chatbot(type="messages")
                    gr.Markdown(f"*{AGENT_PERSONAS['Zeta']}*")
                with gr.Column():
                    axel_model_selector = gr.Dropdown(
                        choices=LLM_MODELS_ID,
                        value=LLM_MODELS_ID[0],
                        label="Axel",
                        scale=1
                    )
                    # axel_output = gr.Textbox(
                    #     label="Axel's Response",
                    #     lines=5,
                    #     scale=1
                    # )
                    axel_output = gr.Chatbot(type="messages")
                    gr.Markdown(f"*{AGENT_PERSONAS['Axel']}*")
            
            # with gr.TabItem("Aggregated Analysis"):
            with gr.Row():
                with gr.Column():
                    aggregator_model_selector = gr.Dropdown(
                    choices=LLM_MODELS_ID,
                    value=LLM_MODELS_ID[0],
                    label="Aggregator",
                    interactive=True,
                    scale=1
                    )
                    aggregator_output = gr.Chatbot(type="messages")

            submit_btn.click(
                fn=process_all_agents,
                inputs=[prompt, nova_model_selector, zeta_model_selector, axel_model_selector, aggregator_model_selector, collection_selector],
                outputs=[nova_output, zeta_output, axel_output, aggregator_output]
            )


if __name__ == "__main__":
    demo.launch(server_name="0.0.0.0", server_port=7860)