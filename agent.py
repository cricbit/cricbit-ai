import operator
from langchain_core.messages import BaseMessage, ToolMessage, SystemMessage
from langchain_openai import ChatOpenAI
from langgraph.graph import END, StateGraph
from typing import TypedDict, Annotated, Sequence

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
        
        self.llm_with_tools = llm.bind_tools(all_tools)
        self.tools = {tool.name: tool for tool in all_tools}
        
        builder.add_node("agent", self.agent_node)
        builder.add_node("tools", self.tools_node)
        
        builder.set_entry_point("agent")
       
        builder.add_conditional_edges(
            "agent",
            self.should_continue,
            {
                "continue": "tools",
                "end": END
            }
        )
        
        builder.add_edge("tools", "agent")
        
        self.graph = builder.compile()
    
    def agent_node(self, state: AgentState):
        messages = state["messages"]
        
        if not any(isinstance(msg, SystemMessage) for msg in messages):
            messages = [SystemMessage(content=SQL_AGENT_SYSTEM_PROMPT)] + list(messages)
        
        response = self.llm_with_tools.invoke(messages)
        return {"messages": [response]}

    def tools_node(self, state: AgentState):
        """Execute all tool calls from the last message"""
        last_message = state["messages"][-1]
        tool_messages = []
        
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
                        return {
                            "sql_query": tool_args.get('sql_query', ''),
                            "query_results": str(result),
                            "messages": tool_messages
                        }
        
        return {"messages": tool_messages}
    
    def should_continue(self, state: AgentState):
        last_message = state["messages"][-1]
        if hasattr(last_message, 'tool_calls') and last_message.tool_calls:
            return "continue"  # Go to tools node
        return "end"  # No tool calls, we're done
