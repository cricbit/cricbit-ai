import gradio as gr
from agent import CricketAgent  # Your agent file

agent = CricketAgent()

def chat(message, history):
    result = agent.graph.invoke({
        "messages": [{"role": "user", "content": message}],
        "user_query": message,
        "current_iteration": 0
    })
    
    last_message = result["messages"][-1]
    return last_message.content

demo = gr.ChatInterface(
    fn=chat,
    title="🏏 Cricket Stats Assistant",
    examples=[
        "Who has the most centuries in ODIs?",
        "Top 5 wicket takers in Tests"
    ],
)

demo.launch()