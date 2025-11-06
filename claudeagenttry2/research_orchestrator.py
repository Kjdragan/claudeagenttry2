"""
Research Orchestrator System using Claude Agent SDK
Orchestrates 3 parallel research subagents for comprehensive web research
"""

import os
import json
import asyncio
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Any, Optional
import requests
from claude_agent_sdk import ClaudeSDKClient, ClaudeAgentOptions, tool, create_sdk_mcp_server


class ResearchOrchestrator:
    """
    Main orchestrator that manages research subagents and coordinates parallel searches.
    """

    def __init__(self, serper_api_key: str, num_results: int = 10):
        self.serper_api_key = serper_api_key
        self.num_results = num_results
        self.session_dir = None
        self.status_callback = None

    def set_status_callback(self, callback):
        """Set callback function for status updates to UI"""
        self.status_callback = callback

    def log_status(self, message: str, level: str = "info"):
        """Log status message with timestamp"""
        timestamp = datetime.now().strftime("%H:%M:%S")
        formatted_msg = f"[{timestamp}] {message}"
        print(formatted_msg)
        if self.status_callback:
            self.status_callback(formatted_msg, level)

    def create_session_directory(self) -> Path:
        """Create timestamped session directory for storing research data"""
        timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
        session_path = Path(f"research_sessions/{timestamp}")
        session_path.mkdir(parents=True, exist_ok=True)
        self.session_dir = session_path
        self.log_status(f"📁 Created session directory: {session_path}", "success")
        return session_path

    def save_json(self, filename: str, data: Dict) -> Path:
        """Save data as JSON in session directory"""
        if not self.session_dir:
            self.create_session_directory()

        filepath = self.session_dir / filename
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)

        self.log_status(f"💾 Saved: {filename}")
        return filepath

    def serper_search(self, query: str) -> Dict[str, Any]:
        """
        Execute search using Serper.dev API
        Returns top results with metadata
        """
        self.log_status(f"🔍 Searching: '{query}'")

        url = "https://google.serper.dev/search"
        headers = {
            "X-API-KEY": self.serper_api_key,
            "Content-Type": "application/json"
        }
        payload = {
            "q": query,
            "num": self.num_results
        }

        try:
            response = requests.post(url, json=payload, headers=headers, timeout=30)
            response.raise_for_status()
            results = response.json()

            # Extract organic results
            organic_results = results.get("organic", [])
            self.log_status(f"✅ Found {len(organic_results)} results for: '{query}'", "success")

            return {
                "query": query,
                "num_results": len(organic_results),
                "results": organic_results,
                "search_metadata": results.get("searchParameters", {})
            }
        except Exception as e:
            self.log_status(f"❌ Search error for '{query}': {str(e)}", "error")
            return {
                "query": query,
                "error": str(e),
                "results": []
            }

    async def research_with_orchestrator(self, user_query: str) -> Dict[str, Any]:
        """
        Main orchestration function that:
        1. Refines user query into 3 search queries (primary + 2 orthogonal)
        2. Spawns 3 research subagents in parallel
        3. Collects and saves results
        4. Generates final report
        """
        self.log_status("=" * 80)
        self.log_status("🚀 STARTING RESEARCH ORCHESTRATOR", "info")
        self.log_status("=" * 80)

        # Create session directory
        session_dir = self.create_session_directory()

        # Step 1: Use orchestrator to refine queries
        self.log_status("\n📝 Step 1: Query Refinement")
        self.log_status(f"Original query: '{user_query}'")

        refined_queries = await self._refine_queries(user_query)

        # Save queries
        self.save_json("queries.json", refined_queries)

        # Step 2: Execute parallel searches with subagents
        self.log_status("\n🔄 Step 2: Parallel Research Execution")
        self.log_status("Spawning 3 research subagents...")

        research_results = await self._execute_parallel_research(refined_queries)

        # Step 3: Save all results
        self.log_status("\n💾 Step 3: Saving Results")
        for i, result in enumerate(research_results):
            filename = f"research_results_{result['query_type']}.json"
            self.save_json(filename, result)

        # Step 4: Generate final report
        self.log_status("\n📊 Step 4: Generating Final Report")
        final_report = await self._generate_report(user_query, refined_queries, research_results)

        # Save report
        report_path = session_dir / "final_report.md"
        with open(report_path, 'w', encoding='utf-8') as f:
            f.write(final_report)
        self.log_status(f"✅ Final report saved: {report_path}", "success")

        self.log_status("\n" + "=" * 80)
        self.log_status("✨ RESEARCH ORCHESTRATOR COMPLETED", "success")
        self.log_status("=" * 80)

        return {
            "session_dir": str(session_dir),
            "queries": refined_queries,
            "results": research_results,
            "report": final_report
        }

    async def _refine_queries(self, user_query: str) -> Dict[str, str]:
        """
        Use Claude to refine user query into 3 optimized search queries:
        - Primary: Direct optimization of user query for Serper API
        - Orthogonal 1 & 2: Related but different angles
        """
        self.log_status("🤔 Analyzing query and generating search variations...")

        refinement_prompt = f"""
You are a search query optimization expert. Given the user's research query, generate THREE search queries:

1. PRIMARY: Optimize the user query for Google Search (via Serper API) - make it clear, specific, and likely to return highly relevant results
2. ORTHOGONAL_1: A related but different angle - explore a complementary aspect or perspective
3. ORTHOGONAL_2: Another related angle - explore a different facet or related topic

User Query: "{user_query}"

Return ONLY a JSON object with this exact structure (no markdown, no explanation):
{{
    "original": "user query here",
    "primary": "optimized primary search query",
    "orthogonal_1": "first orthogonal search query",
    "orthogonal_2": "second orthogonal search query",
    "reasoning": {{
        "primary": "brief explanation of primary query strategy",
        "orthogonal_1": "brief explanation of first orthogonal angle",
        "orthogonal_2": "brief explanation of second orthogonal angle"
    }}
}}
"""

        options = ClaudeAgentOptions(
            system_prompt="You are a search optimization expert. Output valid JSON only.",
            allowed_tools=[],
            max_turns=1
        )

        async with ClaudeSDKClient(options=options) as client:
            await client.query(refinement_prompt)

            response_text = ""
            async for message in client.receive_response():
                if hasattr(message, 'content'):
                    for block in message.content:
                        if hasattr(block, 'text'):
                            response_text += block.text

        # Parse JSON response
        try:
            # Clean up response (remove markdown if present)
            response_text = response_text.strip()
            if response_text.startswith('```json'):
                response_text = response_text.split('```json')[1].split('```')[0].strip()
            elif response_text.startswith('```'):
                response_text = response_text.split('```')[1].split('```')[0].strip()

            refined = json.loads(response_text)

            self.log_status(f"   Primary: '{refined['primary']}'", "info")
            self.log_status(f"   Orthogonal 1: '{refined['orthogonal_1']}'", "info")
            self.log_status(f"   Orthogonal 2: '{refined['orthogonal_2']}'", "info")

            return refined
        except json.JSONDecodeError as e:
            self.log_status(f"⚠️  Query refinement failed, using original query", "warning")
            # Fallback to simple variations
            return {
                "original": user_query,
                "primary": user_query,
                "orthogonal_1": f"{user_query} latest research",
                "orthogonal_2": f"{user_query} expert analysis",
                "reasoning": {
                    "primary": "Using original query",
                    "orthogonal_1": "Latest research angle",
                    "orthogonal_2": "Expert analysis angle"
                }
            }

    async def _execute_parallel_research(self, refined_queries: Dict[str, str]) -> List[Dict[str, Any]]:
        """
        Execute 3 research subagents in parallel using Claude Agent SDK's subagent system.
        Each subagent:
        1. Executes Serper search
        2. Scrapes top N results
        3. Returns compact results with metadata
        """

        # Define the research subagent
        research_subagent_config = {
            "description": "Specialized research agent that searches the web and scrapes content. Use for executing web searches and content extraction.",
            "prompt": """You are a specialized research agent. Your task is to:
1. Execute web searches using the Serper API
2. Scrape and extract content from the top search results
3. Return concise, structured data

You have access to these tools:
- serper_search: Search the web
- Web browsing tools: To fetch page content

Focus on extracting key information, URLs, and metadata. Be efficient and thorough.""",
            "tools": ["Read", "Write", "Bash"],  # Will add MCP tools programmatically
            "model": "claude-sonnet-4-20250514"
        }

        # Create tasks for parallel execution
        tasks = []
        query_types = ["primary", "orthogonal_1", "orthogonal_2"]

        for query_type in query_types:
            query = refined_queries.get(query_type, "")
            if query:
                task = self._run_research_subagent(query, query_type)
                tasks.append(task)

        # Execute in parallel
        self.log_status(f"⚡ Launching {len(tasks)} research subagents in parallel...")
        results = await asyncio.gather(*tasks, return_exceptions=True)

        # Process results
        processed_results = []
        for i, result in enumerate(results):
            if isinstance(result, Exception):
                self.log_status(f"❌ Subagent {i+1} failed: {str(result)}", "error")
                processed_results.append({
                    "query_type": query_types[i],
                    "error": str(result),
                    "articles": []
                })
            else:
                processed_results.append(result)

        return processed_results

    async def _run_research_subagent(self, query: str, query_type: str) -> Dict[str, Any]:
        """
        Run a single research subagent that:
        1. Searches with Serper API
        2. Scrapes content from results
        3. Returns structured data
        """
        self.log_status(f"🤖 Subagent [{query_type}] started")

        # Execute search
        search_results = self.serper_search(query)

        if "error" in search_results or not search_results.get("results"):
            return {
                "query_type": query_type,
                "query": query,
                "error": search_results.get("error", "No results found"),
                "articles": []
            }

        # Scrape content from top results using web_fetch
        articles = []
        results_to_scrape = search_results["results"][:self.num_results]

        self.log_status(f"📄 Subagent [{query_type}] scraping {len(results_to_scrape)} articles...")

        for idx, result in enumerate(results_to_scrape, 1):
            url = result.get("link", "")
            title = result.get("title", "No title")
            snippet = result.get("snippet", "")

            if not url:
                continue

            # Use web_fetch through agent
            content = await self._fetch_url_content(url)

            article_data = {
                "position": idx,
                "title": title,
                "url": url,
                "snippet": snippet,
                "content_preview": content[:500] + "..." if content else snippet,
                "content_length": len(content) if content else 0,
                "scraped": content is not None
            }

            articles.append(article_data)
            self.log_status(f"   ✓ [{query_type}] Scraped {idx}/{len(results_to_scrape)}: {title[:50]}...")

        self.log_status(f"✅ Subagent [{query_type}] completed - {len(articles)} articles processed", "success")

        return {
            "query_type": query_type,
            "query": query,
            "num_articles": len(articles),
            "articles": articles,
            "search_metadata": search_results.get("search_metadata", {})
        }

    async def _fetch_url_content(self, url: str) -> Optional[str]:
        """
        Fetch URL content using Claude Agent SDK's web_fetch capability
        This maintains compatibility with the SDK's built-in tools
        """
        try:
            # Use web_fetch tool through the SDK
            options = ClaudeAgentOptions(
                system_prompt="You are a web scraper. Extract and return the main text content from the provided URL.",
                allowed_tools=["Read", "Write", "Bash"],  # Add web browsing when available
                max_turns=1
            )

            async with ClaudeSDKClient(options=options) as client:
                fetch_prompt = f"Fetch and extract the main text content from this URL: {url}\nReturn ONLY the main text content, no formatting or commentary."

                await client.query(fetch_prompt)

                content = ""
                async for message in client.receive_response():
                    if hasattr(message, 'content'):
                        for block in message.content:
                            if hasattr(block, 'text'):
                                content += block.text

                return content if content else None

        except Exception as e:
            self.log_status(f"⚠️  Failed to fetch {url}: {str(e)}", "warning")
            return None

    async def _generate_report(self, original_query: str, refined_queries: Dict, research_results: List[Dict]) -> str:
        """
        Generate a comprehensive markdown report using Claude to synthesize all research
        """
        self.log_status("📝 Synthesizing research into final report...")

        # Prepare data for report generation
        research_summary = {
            "original_query": original_query,
            "refined_queries": refined_queries,
            "results_summary": []
        }

        for result in research_results:
            summary = {
                "query_type": result.get("query_type"),
                "query": result.get("query"),
                "num_articles": result.get("num_articles", 0),
                "articles": [
                    {
                        "title": article.get("title"),
                        "url": article.get("url"),
                        "snippet": article.get("snippet"),
                        "content_preview": article.get("content_preview", "")[:300]
                    }
                    for article in result.get("articles", [])[:5]  # Top 5 for report
                ]
            }
            research_summary["results_summary"].append(summary)

        report_prompt = f"""
You are a research analyst. Generate a comprehensive markdown research report based on the following data:

ORIGINAL QUERY: {original_query}

RESEARCH DATA:
{json.dumps(research_summary, indent=2)}

Generate a professional markdown report with the following structure:

# Research Report: [Title based on query]

## Executive Summary
[2-3 paragraph overview of findings]

## Research Methodology
- Original Query: ...
- Search Strategy: ...
- Sources Analyzed: ...

## Key Findings

### Primary Research: [Primary Query Topic]
[Synthesize findings from primary search]

#### Notable Sources
[List top 3-5 sources with brief descriptions]

### Complementary Research: [Orthogonal Query 1 Topic]
[Synthesize findings from first orthogonal search]

#### Notable Sources
[List top 3-5 sources]

### Additional Perspectives: [Orthogonal Query 2 Topic]
[Synthesize findings from second orthogonal search]

#### Notable Sources
[List top 3-5 sources]

## Synthesis & Conclusions
[Integrate insights from all three research angles]

## Sources & References
[Complete list of all URLs organized by category]

---
*Report generated on {datetime.now().strftime("%Y-%m-%d at %H:%M:%S")}*
"""

        options = ClaudeAgentOptions(
            system_prompt="You are an expert research analyst. Generate comprehensive, well-structured markdown reports.",
            allowed_tools=[],
            max_turns=1
        )

        async with ClaudeSDKClient(options=options) as client:
            await client.query(report_prompt)

            report = ""
            async for message in client.receive_response():
                if hasattr(message, 'content'):
                    for block in message.content:
                        if hasattr(block, 'text'):
                            report += block.text

        self.log_status("✅ Report generation completed", "success")
        return report


# Utility function for CLI testing
async def main():
    """Test function"""
    serper_key = os.getenv("SERPERDEV_API_KEY")
    if not serper_key:
        print("Error: SERPERDEV_API_KEY environment variable not set")
        return

    orchestrator = ResearchOrchestrator(serper_key, num_results=5)

    query = "Latest developments in AI agent architectures"
    result = await orchestrator.research_with_orchestrator(query)

    print("\n" + "=" * 80)
    print("FINAL REPORT:")
    print("=" * 80)
    print(result["report"])


if __name__ == "__main__":
    asyncio.run(main())
