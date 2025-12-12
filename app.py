from typing import TypedDict, Annotated, Sequence
from langchain_core.messages import BaseMessage, ToolMessage
from langgraph.graph import END, StateGraph
from langchain_openai import ChatOpenAI
import operator

from config import SQL_AGENT_SYSTEM_PROMPT
from tools import execute_sql_query, get_table_schema, list_tables

class AgentState(TypedDict):
    messages: Annotated[Sequence[BaseMessage], operator.add]
    sql_query: str
    query_results: str

class CricketAgent:
    def __init__(self):
        builder = StateGraph(AgentState)
        
        llm = ChatOpenAI(model="gpt-4o", temperature=0)
        all_tools = [list_tables, get_table_schema, execute_sql_query]
        
        # Bind tools to LLM
        llm_with_tools = llm.bind_tools(all_tools)
        
        # Define nodes
        builder.add_node("agent", self.agent_node)
        builder.add_node("execute_sql", self.execute_sql_node)
        
        # Set entry point
        builder.set_entry_point("agent")
        
        # Add conditional edges
        builder.add_conditional_edges(
            "agent",
            self.should_continue,
            {
                "continue": "agent",
                "execute_sql": "execute_sql",
                "end": END
            }
        )
        
        builder.add_edge("execute_sql", "agent")
        
        self.graph = builder.compile()
    
    def agent_node(self, state: AgentState):
        messages = state["messages"]
        response = self.llm_with_tools.invoke(messages)
        return {"messages": [response]}
    
    def execute_sql_node(self, state: AgentState):
        last_message = state["messages"][-1]
        if hasattr(last_message, 'tool_calls'):
            for tool_call in last_message.tool_calls:
                if tool_call['name'] == 'execute_sql_query':
                    sql = tool_call['args']['sql_query']
                    result = execute_sql_query.invoke({"sql_query": sql})
                    return {
                        "sql_query": sql,
                        "query_results": result,
                        "messages": [ToolMessage(content=result, tool_call_id=tool_call['id'])]
                    }
        return {}
    
    def should_continue(self, state: AgentState):
        last_message = state["messages"][-1]
        if hasattr(last_message, 'tool_calls') and last_message.tool_calls:
            tool_name = last_message.tool_calls[0]['name']
            if tool_name == 'execute_sql_query':
                return "execute_sql"
            return "continue"
        return "end"