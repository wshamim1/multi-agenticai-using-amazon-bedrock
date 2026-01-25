"""
Streamlit Client Application for Multi-Agent AI System
Provides interactive UI for interacting with Weather, Stock, and News agents
"""

import streamlit as st
import uuid
import json
import base64
from typing import Optional, Dict, Any
import sys
from pathlib import Path

# Add parent directory to path
sys.path.append(str(Path(__file__).parent))

from config import config
from core.agent_manager import AgentManager
from core.knowledge_base_manager import KnowledgeBaseManager

# Page configuration
st.set_page_config(
    page_title="Multi-Agent AI System",
    page_icon="🤖",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS
st.markdown("""
<style>
/* Main title styling */
.main-title {
    text-align: center;
    font-size: 2.5em;
    color: #4CAF50;
    font-weight: bold;
    margin-bottom: 10px;
}

.subtitle {
    text-align: center;
    font-size: 1.3em;
    color: #555;
    margin-bottom: 30px;
}

/* Chat message styling */
.stChatMessage {
    padding: 1rem;
    border-radius: 12px;
    margin-bottom: 10px;
}

.stChatMessage.user {
    background-color: #e6f2ff;
    border-left: 4px solid #3399ff;
}

.stChatMessage.assistant {
    background-color: #f0fff4;
    border-left: 4px solid #33cc66;
}

/* Sidebar styling */
[data-testid="stSidebar"] {
    background-color: #f5f5f5;
    padding: 20px;
}

/* Button styling */
button[kind="primary"] {
    background-color: #4CAF50 !important;
    color: white !important;
    border-radius: 8px !important;
    font-weight: bold !important;
}

button[kind="primary"]:hover {
    background-color: #45a049 !important;
}

/* Input styling */
textarea {
    border-radius: 8px !important;
    border: 2px solid #ddd !important;
}

/* Success/Error messages */
.success-box {
    padding: 15px;
    background-color: #d4edda;
    border-left: 4px solid #28a745;
    border-radius: 5px;
    margin: 10px 0;
}

.error-box {
    padding: 15px;
    background-color: #f8d7da;
    border-left: 4px solid #dc3545;
    border-radius: 5px;
    margin: 10px 0;
}

.info-box {
    padding: 15px;
    background-color: #d1ecf1;
    border-left: 4px solid #17a2b8;
    border-radius: 5px;
    margin: 10px 0;
}
</style>
""", unsafe_allow_html=True)


class StreamlitApp:
    """Main Streamlit application class"""
    
    def __init__(self):
        """Initialize the application"""
        self.config = config
        
        # Initialize managers
        self.agent_mgr = AgentManager(
            config.aws.bedrock_agent_client,
            config.aws.bedrock_agent_runtime_client,
            config.aws.account_id,
            config.aws.region
        )
        
        self.kb_mgr = KnowledgeBaseManager(
            config.aws.bedrock_agent_client,
            config.aws.account_id,
            config.aws.region
        )
        
        # Initialize session state
        if 'session_id' not in st.session_state:
            st.session_state.session_id = str(uuid.uuid4())
        
        if 'chat_history' not in st.session_state:
            st.session_state.chat_history = []
        
        if 'current_mode' not in st.session_state:
            st.session_state.current_mode = "Agent Chat"
    
    def render_header(self):
        """Render application header"""
        col1, col2, col3 = st.columns([1, 2, 1])
        
        with col2:
            st.markdown('<div class="main-title">🤖 Multi-Agent AI System 🧠</div>', unsafe_allow_html=True)
            st.markdown('<div class="subtitle">Weather, Stock Market & News Intelligence</div>', unsafe_allow_html=True)
    
    def render_sidebar(self):
        """Render sidebar with configuration options"""
        with st.sidebar:
            st.image("https://via.placeholder.com/300x100/4CAF50/FFFFFF?text=Multi-Agent+AI", width='stretch')
            
            st.markdown("## ⚙️ Configuration")
            
            # Mode selection
            mode = st.selectbox(
                "Select Mode",
                [
                    "Agent Chat",
                    "Knowledge Base Search",
                    "Text Generation",
                    "Document Analysis"
                ],
                key="mode_selector"
            )
            st.session_state.current_mode = mode
            
            # Model selection for text generation
            if mode in ["Text Generation", "Document Analysis"]:
                st.selectbox(
                    "LLM Model",
                    [
                        "anthropic.claude-3-sonnet-20240229-v1:0",
                        "amazon.nova-pro-v1:0",
                        "amazon.titan-text-premier-v1:0"
                    ],
                    key="llm_model"
                )
            
            st.markdown("---")
            
            # System information
            st.markdown("## 📊 System Info")
            st.info(f"**Region:** {self.config.aws.region}")
            st.info(f"**Session ID:** {st.session_state.session_id[:8]}...")
            
            # Clear chat button
            if st.button("🗑️ Clear Chat History", width='stretch'):
                st.session_state.chat_history = []
                st.session_state.session_id = str(uuid.uuid4())
                st.rerun()
            
            st.markdown("---")
            
            # Help section
            with st.expander("ℹ️ Help & Info"):
                st.markdown("""
                ### Available Modes:
                
                **Agent Chat**
                - Ask about weather conditions and forecasts
                - Get stock market data and company information
                - Search for latest news and headlines
                - Multi-agent system routes to appropriate specialist
                
                **Knowledge Base Search**
                - Search documentation and guides
                - Get answers from knowledge base
                - Retrieve relevant information
                
                **Text Generation**
                - Generate text using LLMs
                - Create documentation
                - Answer questions
                
                **Document Analysis**
                - Analyze uploaded documents
                - Extract information
                - Summarize content
                
                ### Example Queries:
                - "What's the weather in New York?"
                - "Get me the stock price for AAPL"
                - "Show me today's top tech news"
                - "What's the forecast for San Francisco this week?"
                - "Get market summary"
                """)
    
    def invoke_agent(self, query: str) -> str:
        """
        Invoke multi-agent system
        
        Args:
            query: User query
            
        Returns:
            Agent response
        """
        try:
            # Get supervisor agent
            agent = self.agent_mgr.get_agent_by_name(self.config.agent.supervisor_agent_name)
            if not agent:
                return "❌ Supervisor agent not found. Please deploy the system first."
            
            agent_id = agent['agentId']
            st.write(f"🔍 Debug: Agent ID: {agent_id}")
            st.write(f"🔍 Debug: Foundation Model: {agent.get('foundationModel', 'Not set')}")
            
            # Get alias - look for "multi-agent-alias"
            aliases = self.agent_mgr.client.list_agent_aliases(
                agentId=agent_id,
                maxResults=10
            )
            
            if not aliases.get('agentAliasSummaries'):
                return "❌ No agent alias found. Please prepare the agent first."
            
            # Find the multi-agent-alias
            alias_id = None
            for alias in aliases['agentAliasSummaries']:
                if alias['agentAliasName'] == 'multi-agent-alias':
                    alias_id = alias['agentAliasId']
                    st.write(f"🔍 Debug: Found alias: {alias['agentAliasName']} ({alias_id})")
                    break
            
            if not alias_id:
                # Fallback to first alias if multi-agent-alias not found
                alias_id = aliases['agentAliasSummaries'][0]['agentAliasId']
                st.write(f"🔍 Debug: Using first alias: {aliases['agentAliasSummaries'][0]['agentAliasName']} ({alias_id})")
            
            st.write(f"🔍 Debug: Invoking agent {agent_id} with alias {alias_id}")
            
            # Invoke agent
            response = self.agent_mgr.invoke_agent(
                agent_id,
                alias_id,
                st.session_state.session_id,
                query
            )
            
            return response
            
        except Exception as e:
            import traceback
            error_details = traceback.format_exc()
            st.error(f"Full error details:\n{error_details}")
            return f"❌ Error invoking agent: {str(e)}"
    
    def search_knowledge_base(self, query: str) -> str:
        """
        Search knowledge base
        
        Args:
            query: Search query
            
        Returns:
            Search results
        """
        try:
            # Get KB
            kb = self.kb_mgr.get_knowledge_base_by_name(self.config.kb.kb_name)
            if not kb:
                return "❌ Knowledge Base not found. Please deploy the system first."
            
            kb_id = kb['knowledgeBaseId']
            
            # Retrieve documents
            results = self.kb_mgr.retrieve_from_kb(kb_id, query, number_of_results=3)
            
            if not results:
                return "No relevant documents found."
            
            # Format response
            response = "### 📚 Knowledge Base Results\n\n"
            for i, result in enumerate(results, 1):
                response += f"**Result {i}** (Score: {result['score']:.3f})\n\n"
                response += f"{result['content']}\n\n"
                response += "---\n\n"
            
            return response
            
        except Exception as e:
            return f"❌ Error searching knowledge base: {str(e)}"
    
    def generate_text(self, prompt: str, model: str) -> str:
        """
        Generate text using Bedrock
        
        Args:
            prompt: Text prompt
            model: Model ID
            
        Returns:
            Generated text
        """
        try:
            response = self.config.aws.bedrock_runtime_client.invoke_model(
                modelId=model,
                body=json.dumps({
                    "anthropic_version": "bedrock-2023-05-31",
                    "max_tokens": 2000,
                    "messages": [
                        {
                            "role": "user",
                            "content": prompt
                        }
                    ]
                })
            )
            
            result = json.loads(response['body'].read())
            return result['content'][0]['text']
            
        except Exception as e:
            return f"❌ Error generating text: {str(e)}"
    
    def generate_image(self, prompt: str) -> Optional[str]:
        """
        Generate image using Titan
        
        Args:
            prompt: Image prompt
            
        Returns:
            Base64 encoded image or None
        """
        try:
            response = self.config.aws.bedrock_runtime_client.invoke_model(
                modelId="amazon.titan-image-generator-v2:0",
                body=json.dumps({
                    "taskType": "TEXT_IMAGE",
                    "textToImageParams": {
                        "text": prompt
                    },
                    "imageGenerationConfig": {
                        "numberOfImages": 1,
                        "quality": "standard",
                        "height": 512,
                        "width": 512
                    }
                })
            )
            
            result = json.loads(response['body'].read())
            return result['images'][0]
            
        except Exception as e:
            st.error(f"Error generating image: {str(e)}")
            return None
    
    def render_chat_interface(self):
        """Render main chat interface"""
        # Display chat history
        for message in st.session_state.chat_history:
            with st.chat_message(message["role"]):
                st.markdown(message["content"])
        
        # File uploader for document analysis
        uploaded_file = None
        if st.session_state.current_mode == "Document Analysis":
            uploaded_file = st.file_uploader(
                "Upload document (PDF, TXT, JSON)",
                type=['pdf', 'txt', 'json']
            )
        
        # Chat input
        if prompt := st.chat_input("Type your message here..."):
            # Add user message to history
            st.session_state.chat_history.append({
                "role": "user",
                "content": prompt
            })
            
            # Display user message
            with st.chat_message("user"):
                st.markdown(prompt)
            
            # Process based on mode
            with st.chat_message("assistant"):
                with st.spinner("Processing..."):
                    if st.session_state.current_mode == "Agent Chat":
                        response = self.invoke_agent(prompt)
                    
                    elif st.session_state.current_mode == "Knowledge Base Search":
                        response = self.search_knowledge_base(prompt)
                    
                    elif st.session_state.current_mode == "Text Generation":
                        model = st.session_state.get('llm_model', 'anthropic.claude-3-sonnet-20240229-v1:0')
                        response = self.generate_text(prompt, model)
                    
                    elif st.session_state.current_mode == "Document Analysis":
                        if uploaded_file:
                            content = uploaded_file.read().decode('utf-8')
                            analysis_prompt = f"Analyze this document:\n\n{content}\n\nUser question: {prompt}"
                            model = st.session_state.get('llm_model', 'anthropic.claude-3-sonnet-20240229-v1:0')
                            response = self.generate_text(analysis_prompt, model)
                        else:
                            response = "Please upload a document first."
                    
                    else:
                        response = "Mode not implemented yet."
                    
                    st.markdown(response)
            
            # Add assistant response to history
            st.session_state.chat_history.append({
                "role": "assistant",
                "content": response
            })
    
    def run(self):
        """Run the Streamlit application"""
        self.render_header()
        self.render_sidebar()
        self.render_chat_interface()


def main():
    """Main entry point"""
    app = StreamlitApp()
    app.run()


if __name__ == "__main__":
    main()

