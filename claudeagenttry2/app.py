"""
Streamlit UI for Research Orchestrator
Provides chat interface with real-time process visibility and markdown rendering
"""

import streamlit as st
import asyncio
from pathlib import Path
import os
from datetime import datetime
from research_orchestrator import ResearchOrchestrator


# Page configuration
st.set_page_config(
    page_title="Research Orchestrator",
    page_icon="🔬",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS for better styling
st.markdown("""
<style>
    .status-box {
        background-color: #f0f2f6;
        padding: 15px;
        border-radius: 5px;
        margin: 10px 0;
        font-family: 'Courier New', monospace;
        font-size: 12px;
        max-height: 400px;
        overflow-y: auto;
    }
    .success-msg {
        color: #28a745;
        font-weight: bold;
    }
    .error-msg {
        color: #dc3545;
        font-weight: bold;
    }
    .info-msg {
        color: #17a2b8;
    }
    .warning-msg {
        color: #ffc107;
    }
    .chat-message {
        padding: 10px;
        margin: 10px 0;
        border-radius: 8px;
    }
    .user-message {
        background-color: #e3f2fd;
        border-left: 4px solid #2196f3;
    }
    .assistant-message {
        background-color: #f5f5f5;
        border-left: 4px solid #4caf50;
    }
</style>
""", unsafe_allow_html=True)


def init_session_state():
    """Initialize session state variables"""
    if 'messages' not in st.session_state:
        st.session_state.messages = []

    if 'status_logs' not in st.session_state:
        st.session_state.status_logs = []

    if 'current_research' not in st.session_state:
        st.session_state.current_research = None

    if 'research_complete' not in st.session_state:
        st.session_state.research_complete = False


def add_status_log(message: str, level: str = "info"):
    """Add a status log message"""
    st.session_state.status_logs.append({
        "message": message,
        "level": level,
        "timestamp": datetime.now().astimezone()
    })


def display_status_logs():
    """Display status logs in a styled container"""
    if st.session_state.status_logs:
        status_html = "<div class='status-box'>"

        for log in st.session_state.status_logs[-50:]:  # Show last 50 logs
            level_class = f"{log['level']}-msg"
            status_html += f"<div class='{level_class}'>{log['message']}</div>"

        status_html += "</div>"
        st.markdown(status_html, unsafe_allow_html=True)


def display_chat_message(role: str, content: str):
    """Display a chat message with styling"""
    if role == "user":
        st.markdown(f"""
        <div class='chat-message user-message'>
            <strong>🧑 You:</strong><br>
            {content}
        </div>
        """, unsafe_allow_html=True)
    else:
        st.markdown(f"""
        <div class='chat-message assistant-message'>
            <strong>🤖 Research Orchestrator:</strong><br>
            {content}
        </div>
        """, unsafe_allow_html=True)


async def run_research(query: str, num_results: int, api_key: str):
    """Run the research orchestrator"""
    try:
        # Clear previous logs
        st.session_state.status_logs = []
        st.session_state.research_complete = False

        # Create orchestrator
        orchestrator = ResearchOrchestrator(api_key, num_results=num_results)
        orchestrator.set_status_callback(add_status_log)

        # Run research
        result = await orchestrator.research_with_orchestrator(query)

        st.session_state.current_research = result
        st.session_state.research_complete = True

        return result

    except Exception as e:
        add_status_log(f"❌ ERROR: {str(e)}", "error")
        st.error(f"Research failed: {str(e)}")
        return None


def main():
    """Main Streamlit application"""

    # Initialize session state
    init_session_state()

    # Header
    st.title("🔬 Research Orchestrator")
    st.markdown("**AI-Powered Multi-Agent Research System**")
    st.markdown("---")

    # Sidebar configuration
    with st.sidebar:
        st.header("⚙️ Configuration")

        # API Key input
        api_key = st.text_input(
            "Serper.dev API Key",
            type="password",
            value=os.getenv("SERPERDEV_API_KEY", ""),
            help="Get your API key from https://serper.dev"
        )

        # Number of results
        num_results = st.slider(
            "Results per query",
            min_value=5,
            max_value=20,
            value=10,
            help="Number of search results to scrape per query"
        )

        st.markdown("---")
        st.markdown("### 📊 System Info")
        st.info("""
        **Architecture:**
        - 1 Orchestrator Agent
        - 3 Research Subagents (Parallel)
        - Serper.dev API Integration
        - Web Content Scraping
        - Timestamped Session Storage
        """)

        st.markdown("---")
        st.markdown("### 💡 How it works")
        st.markdown("""
        1. **Query Refinement**: Orchestrator analyzes your query and creates 3 optimized searches
        2. **Parallel Research**: 3 subagents search and scrape content simultaneously
        3. **Data Collection**: Results saved to timestamped session directory
        4. **Report Generation**: Comprehensive markdown report synthesizes all findings
        """)

        if st.session_state.current_research:
            st.markdown("---")
            st.markdown("### 📁 Current Session")
            st.code(st.session_state.current_research["session_dir"])
            run_timestamp = st.session_state.current_research.get("run_timestamp")
            if run_timestamp:
                try:
                    run_dt = datetime.fromisoformat(run_timestamp)
                    st.caption(f"Started: {run_dt.strftime('%Y-%m-%d %H:%M:%S %Z%z')}")
                except ValueError:
                    st.caption(f"Started: {run_timestamp}")

    # Main content area with two columns
    col1, col2 = st.columns([1, 1])

    with col1:
        st.header("💬 Research Query")

        # Chat interface
        query_input = st.text_area(
            "Enter your research query:",
            height=100,
            placeholder="e.g., Latest developments in quantum computing",
            help="Ask any research question - the orchestrator will break it down and research from multiple angles"
        )

        col_btn1, col_btn2 = st.columns([1, 3])
        with col_btn1:
            submit_button = st.button("🚀 Start Research", type="primary", use_container_width=True)
        with col_btn2:
            if st.button("🗑️ Clear History", use_container_width=True):
                st.session_state.messages = []
                st.session_state.status_logs = []
                st.session_state.current_research = None
                st.session_state.research_complete = False
                st.rerun()

        # Display chat history
        if st.session_state.messages:
            st.markdown("---")
            st.subheader("📜 Conversation History")
            for msg in st.session_state.messages:
                display_chat_message(msg["role"], msg["content"])

    with col2:
        st.header("📡 Process Monitor")

        # Status logs container
        status_container = st.container()
        with status_container:
            if st.session_state.status_logs:
                display_status_logs()
            else:
                st.info("Waiting for research to begin...")

    # Handle research submission
    if submit_button:
        if not api_key:
            st.error("❌ Please enter your Serper.dev API key in the sidebar")
        elif not query_input:
            st.error("❌ Please enter a research query")
        else:
            # Add user message
            st.session_state.messages.append({
                "role": "user",
                "content": query_input
            })

            # Show progress
            with st.spinner("🔄 Research in progress..."):
                # Run research
                result = asyncio.run(run_research(query_input, num_results, api_key))

                if result:
                    # Add assistant response
                    response_msg = f"✅ Research completed! Found insights from {sum([r.get('num_articles', 0) for r in result['results']])} articles across 3 research angles."
                    st.session_state.messages.append({
                        "role": "assistant",
                        "content": response_msg
                    })

            # Rerun to update UI
            st.rerun()

    # Display research results
    if st.session_state.research_complete and st.session_state.current_research:
        st.markdown("---")
        st.header("📊 Research Results")

        result = st.session_state.current_research

        # Create tabs for different views
        tab1, tab2, tab3 = st.tabs(["📄 Final Report", "🔍 Query Analysis", "📁 Raw Data"])

        with tab1:
            st.subheader("Final Research Report")

            # Render markdown report
            if "report" in result:
                st.markdown(result["report"])

                # Download button for report
                report_md = result["report"]
                run_timestamp_iso = result.get("run_timestamp")
                try:
                    run_dt = datetime.fromisoformat(run_timestamp_iso) if run_timestamp_iso else datetime.now().astimezone()
                except (TypeError, ValueError):
                    run_dt = datetime.now().astimezone()
                download_ts = run_dt.strftime("%Y%m%d_%H%M%S%z")
                st.download_button(
                    label="⬇️ Download Report (Markdown)",
                    data=report_md,
                    file_name=f"research_report_{download_ts}.md",
                    mime="text/markdown"
                )
                st.caption(f"Report reflects research run started at {run_dt.strftime('%Y-%m-%d %H:%M:%S %Z%z')}")

        with tab2:
            st.subheader("Query Refinement Analysis")

            if "queries" in result:
                queries = result["queries"]

                st.markdown("**Original Query:**")
                st.info(queries.get("original", "N/A"))

                col1, col2, col3 = st.columns(3)

                with col1:
                    st.markdown("**🎯 Primary Search**")
                    st.success(queries.get("primary", "N/A"))
                    if "reasoning" in queries:
                        with st.expander("Reasoning"):
                            st.write(queries["reasoning"].get("primary", "N/A"))

                with col2:
                    st.markdown("**🔄 Orthogonal 1**")
                    st.success(queries.get("orthogonal_1", "N/A"))
                    if "reasoning" in queries:
                        with st.expander("Reasoning"):
                            st.write(queries["reasoning"].get("orthogonal_1", "N/A"))

                with col3:
                    st.markdown("**🔄 Orthogonal 2**")
                    st.success(queries.get("orthogonal_2", "N/A"))
                    if "reasoning" in queries:
                        with st.expander("Reasoning"):
                            st.write(queries["reasoning"].get("orthogonal_2", "N/A"))

        with tab3:
            st.subheader("Research Data Files")

            session_dir = result.get("session_dir", "")
            st.code(session_dir)

            # Display research results summary
            if "results" in result:
                for res in result["results"]:
                    with st.expander(f"📊 {res.get('query_type', 'Unknown').upper()} - {res.get('num_articles', 0)} articles"):
                        st.json(res)


if __name__ == "__main__":
    main()
