from agent import CricketAgent
from langchain_core.messages import HumanMessage


def main():
    agent = CricketAgent()
    
    query = "Present the scorecard for the IPL 2024 Final"
    
    initial_state = {
        "messages": [HumanMessage(content=query)],
        "sql_query": "",
        "query_results": ""
    }
    
    result = agent.graph.invoke(initial_state)
    
    final_message = result["messages"][-1]
    print("Agent Response:", final_message.content)
    
    if result.get("sql_query"):
        print("\nSQL Query:", result["sql_query"])
    if result.get("query_results"):
        print("\nQuery Results:", result["query_results"])

if __name__ == "__main__":
    main()