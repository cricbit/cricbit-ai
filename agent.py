import operator
from langchain_core.messages import BaseMessage, ToolMessage, SystemMessage
from langchain_openai import ChatOpenAI
from langgraph.graph import END, StateGraph
from typing import TypedDict, Annotated, Sequence

from config import MAX_ITERATIONS, SQL_AGENT_SYSTEM_PROMPT
from tools import execute_sql_query, get_table_schema, list_tables, get_sample_data


class AgentState(TypedDict):
    messages: Annotated[Sequence[BaseMessage], operator.add]
    user_query: str
    current_iteration: int
    final_answer: str
    has_final_answer: bool

class CricketAgent:
    def __init__(self):
        builder = StateGraph(AgentState)
        
        llm = ChatOpenAI(model="gpt-4o", temperature=0)
        all_tools = [list_tables, get_table_schema, execute_sql_query, get_sample_data]
        
        self.llm_with_tools = llm.bind_tools(all_tools)
        self.tools = {tool.name: tool for tool in all_tools}
        
        builder.add_node("agent", self.agent_node)
        builder.add_node("tools", self.tools_node)
        
        builder.set_entry_point("agent")
       
        builder.add_conditional_edges(
            "agent",
            self.should_continue,
            {
                "tools": "tools",
                "end": END
            }
        )
        
        builder.add_edge("tools", "agent")
        
        self.graph = builder.compile()
    
    def agent_node(self, state: AgentState):
        messages = state["messages"]
        current_iteration = state.get("current_iteration", 0)
        
        system_msg = SystemMessage(content=SQL_AGENT_SYSTEM_PROMPT.format(
            current_iteration=current_iteration,
        ))
        
        full_messages = [system_msg] + list(messages)
        
        response = self.llm_with_tools.invoke(full_messages)
        
        new_iteration = current_iteration + 1
        
        return {
            "messages": [response],
            "current_iteration": new_iteration
        }
    
    def tools_node(self, state: AgentState):
        last_message = state["messages"][-1]
        tool_messages = []
        
        last_sql_query = state.get("sql_query", "")
        last_query_results = state.get("query_results", "")
        
        if hasattr(last_message, 'tool_calls') and last_message.tool_calls:
            for tool_call in last_message.tool_calls:
                tool_name = tool_call['name']
                tool_args = tool_call['args']
                
                if tool_name in self.tools:
                    tool = self.tools[tool_name]
                    result = tool.invoke(tool_args)
                    
                    tool_message = ToolMessage(
                        content=str(result),
                        tool_call_id=tool_call['id']
                    )
                    tool_messages.append(tool_message)
                    
                    if tool_name == 'execute_sql_query':
                        last_sql_query = tool_args.get('sql_query', '')
                        last_query_results = str(result)
        
        return {
            "messages": tool_messages,
            "sql_query": last_sql_query,
            "query_results": last_query_results
        }

    def should_continue(self, state: AgentState) -> str:
        messages = state["messages"]
        last_message = messages[-1]
        iteration_count = state.get("current_iteration", 0)
        
        if iteration_count >= MAX_ITERATIONS:
            return "end"
        
        if hasattr(last_message, "tool_calls") and last_message.tool_calls:
            return "tools"
        
        return "end"

