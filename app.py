import streamlit as st
from datetime import datetime

from agent import CricketAgent


# Page config
st.set_page_config(
    page_title="Cricket Stats Assistant",
    page_icon="🏏",
    layout="wide"
)

# Initialize agent (cached so it only runs once)
@st.cache_resource
def get_agent():
    return CricketAgent()

agent = get_agent()


# Initialize session state
if "messages" not in st.session_state:
    st.session_state.messages = []

if "query_history" not in st.session_state:
    st.session_state.query_history = []


# Sidebar
with st.sidebar:
    st.title("🏏 Cricket Stats")
    st.markdown("---")
    
    # Example queries
    st.subheader("Example Queries")
    examples = [
        "Who has the most centuries in ODIs?",
        "Virat Kohli's batting average in T20Is",
        "Top 5 wicket takers in Test cricket",
        "Jasprit Bumrah's economy rate in powerplay",
        "India's win percentage at home"
    ]
    
    for example in examples:
        if st.button(example, key=f"example_{example}", use_container_width=True):
            st.session_state.messages.append({
                "role": "user",
                "content": example,
                "timestamp": datetime.now()
            })
            st.rerun()
    
    st.markdown("---")
    
    # Show SQL toggle
    st.session_state.show_sql = st.checkbox("Show SQL Queries", value=True)
    
    # Clear chat
    if st.button("Clear Chat", use_container_width=True):
        st.session_state.messages = []
        st.rerun()
    
    st.markdown("---")
    
    # Query history
    if st.session_state.query_history:
        st.subheader("Recent Queries")
        for i, query in enumerate(st.session_state.query_history[-5:]):
            st.caption(f"{i+1}. {query[:50]}...")


# Main content
st.title("🏏 Cricket Statistics Assistant")
st.markdown("Ask me anything about cricket stats!")

# Display chat messages
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])
        
        # Show SQL if available and enabled
        if (message["role"] == "assistant" and 
            st.session_state.show_sql and 
            "sql" in message):
            with st.expander("🔍 View SQL Query"):
                st.code(message["sql"], language="sql")


# Chat input
if prompt := st.chat_input("Ask about cricket stats..."):
    # Add user message
    st.session_state.messages.append({
        "role": "user",
        "content": prompt,
        "timestamp": datetime.now()
    })
    
    # Display user message
    with st.chat_message("user"):
        st.markdown(prompt)
    
    # Get agent response
    with st.chat_message("assistant"):
        with st.spinner("🤔 Thinking..."):
            try:
                # Run your agent
                result = agent.graph.invoke({
                    "messages": [{"role": "user", "content": prompt}],
                    "user_query": prompt,
                    "current_iteration": 0
                })
                
                # Extract response
                last_message = result["messages"][-1]
                response_content = last_message.content if hasattr(last_message, 'content') else str(last_message)
                
                # Extract SQL if available
                sql_query = result.get("sql_query", None)
                
                # Display response
                st.markdown(response_content)
                
                # Show SQL if available
                if sql_query and st.session_state.show_sql:
                    with st.expander("🔍 View SQL Query"):
                        st.code(sql_query, language="sql")
                
                # Add to messages
                st.session_state.messages.append({
                    "role": "assistant",
                    "content": response_content,
                    "sql": sql_query,
                    "timestamp": datetime.now()
                })
                
                # Add to history
                st.session_state.query_history.append(prompt)
                
            except Exception as e:
                error_msg = f"Sorry, I encountered an error: {str(e)}"
                st.error(error_msg)
                st.session_state.messages.append({
                    "role": "assistant",
                    "content": error_msg,
                    "timestamp": datetime.now()
                })


st.markdown("---")
st.caption("💡 Tip: Try asking about specific players, teams, or tournaments!")