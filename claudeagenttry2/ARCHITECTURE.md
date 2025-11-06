# 🧠 Agent Communication & Context Management Architecture

## Deep Dive: How Orchestrator and Subagents Communicate

---

## Table of Contents
1. [Context Window Management](#context-window-management)
2. [Agent Communication Patterns](#agent-communication-patterns)
3. [Data Flow Architecture](#data-flow-architecture)
4. [File-Based Context Sharing](#file-based-context-sharing)
5. [Parallel Execution Model](#parallel-execution-model)
6. [Best Practices](#best-practices)

---

## Context Window Management

### The Challenge

Claude models have finite context windows:
- **Claude Sonnet 4**: ~200K tokens
- **Claude Opus 4**: ~200K tokens

When conducting research with 30 articles of ~5KB each, we could easily exceed this:
- 30 articles × 5,000 tokens = 150,000 tokens
- Plus orchestrator instructions, queries, metadata: +50,000 tokens
- **Total: 200,000 tokens** ⚠️ (at or over limit)

### The Solution: Context Isolation

Our system uses **hierarchical context isolation** to keep each agent's context manageable:

```
┌─────────────────────────────────────────────┐
│         ORCHESTRATOR CONTEXT (~50K)         │
│                                             │
│  - User query                               │
│  - 3 refined queries                        │
│  - Compact summaries (NOT full content)    │
│  - Report instructions                      │
│                                             │
└─────────────────────────────────────────────┘
                     │
        ┌────────────┴────────────┐
        │   ISOLATED CONTEXTS     │
        └────────────┬────────────┘
                     │
        ┏━━━━━━━━━━━━┻━━━━━━━━━━━━┓
        ┃                          ┃
┌───────▼────────┐  ┌──────────────▼───────┐
│  SUBAGENT #1   │  │  SUBAGENT #2 & #3   │
│ CONTEXT (~150K)│  │ CONTEXT (~150K each)│
│                │  │                      │
│ - Search query │  │ - Search queries     │
│ - 10 URLs      │  │ - 10 URLs each       │
│ - Full content │  │ - Full content       │
│ - Scraping     │  │ - Scraping           │
│   instructions │  │   instructions       │
└────────────────┘  └──────────────────────┘
```

### Key Principle: **Information Reduction**

Each layer reduces information density:

1. **Subagent (150K tokens)**:
   - Full article content: 10 × 15,000 = 150,000 tokens

2. **Returns to Orchestrator** (~5K tokens):
   - Title: ~50 tokens
   - URL: ~20 tokens
   - Snippet: ~100 tokens
   - Content preview (500 chars): ~125 tokens
   - **Per article: ~300 tokens**
   - **10 articles: ~3,000 tokens**

3. **Orchestrator receives** (~15K tokens total):
   - 3 subagents × 3,000 tokens = 9,000 tokens
   - Query data: ~2,000 tokens
   - Instructions: ~4,000 tokens
   - **Total: ~15K tokens** ✅ (Well under limit!)

---

## Agent Communication Patterns

### Pattern 1: Spawn & Isolate

```python
# Orchestrator spawns subagents with ISOLATED contexts
async def _execute_parallel_research(self, queries):
    tasks = [
        self._run_research_subagent(query1, "primary"),      # Isolated context #1
        self._run_research_subagent(query2, "orthogonal_1"), # Isolated context #2
        self._run_research_subagent(query3, "orthogonal_2")  # Isolated context #3
    ]

    # Each subagent has NO KNOWLEDGE of other subagents
    results = await asyncio.gather(*tasks)

    # Orchestrator receives COMPACT results only
    return results
```

**What happens:**
1. Orchestrator creates 3 separate agent instances
2. Each gets its own `ClaudeSDKClient` session
3. Each maintains isolated context window
4. No cross-talk between subagents
5. Only orchestrator sees all results

### Pattern 2: Compact Return

```python
# Subagent processes FULL content but returns COMPACT summary
async def _run_research_subagent(self, query, query_type):
    # Scrape full content (lives in subagent's context)
    articles = []
    for result in search_results:
        full_content = await self._fetch_url_content(result['url'])  # 15K tokens

        # Store full content to FILE (not returned to orchestrator!)
        # Return only compact summary
        articles.append({
            "title": result['title'],           # 50 tokens
            "url": result['url'],               # 20 tokens
            "snippet": result['snippet'],       # 100 tokens
            "content_preview": full_content[:500],  # 125 tokens (NOT 15K!)
            "content_length": len(full_content)     # Metadata
        })

    return {
        "query_type": query_type,
        "articles": articles  # Compact summaries only!
    }
```

**Key Insight:** Subagent does the "heavy lifting" with full content in its context, but only passes lightweight summaries to orchestrator.

### Pattern 3: File-Based Context Extension

```python
# When orchestrator needs full content, it reads from files
def access_full_content_if_needed(self):
    # Orchestrator can load full results from JSON files
    session_dir = Path("research_sessions/2025-01-15_14-30-45")

    with open(session_dir / "research_results_primary.json") as f:
        full_results = json.load(f)
        # Now orchestrator has full content WITHOUT it being in context
        # (File I/O doesn't consume context tokens!)
```

---

## Data Flow Architecture

### Complete Flow Diagram

```
┌─────────────────────────────────────────────────────────────┐
│                         USER INPUT                          │
│              "Research quantum computing trends"             │
└────────────────────────┬────────────────────────────────────┘
                         │
                         ▼
┌─────────────────────────────────────────────────────────────┐
│                  ORCHESTRATOR AGENT                         │
│  Context: 50K tokens                                        │
│                                                             │
│  Step 1: QUERY REFINEMENT                                  │
│  ┌──────────────────────────────────────────────────────┐  │
│  │ Prompt to Claude:                                    │  │
│  │ "Generate 3 optimized search queries..."            │  │
│  │                                                      │  │
│  │ Returns JSON:                                        │  │
│  │ {                                                    │  │
│  │   "primary": "quantum computing breakthroughs 2024" │  │
│  │   "orthogonal_1": "quantum error correction..."     │  │
│  │   "orthogonal_2": "quantum algorithms..."           │  │
│  │ }                                                    │  │
│  └──────────────────────────────────────────────────────┘  │
│                                                             │
│  Step 2: SPAWN SUBAGENTS                                   │
│  ┌──────────────────────────────────────────────────────┐  │
│  │ Creates 3 isolated agent instances:                 │  │
│  │                                                      │  │
│  │ Task 1: search(query="quantum computing...")        │  │
│  │ Task 2: search(query="quantum error...")            │  │
│  │ Task 3: search(query="quantum algorithms...")       │  │
│  │                                                      │  │
│  │ Executes: asyncio.gather(*tasks)                    │  │
│  └──────────────────────────────────────────────────────┘  │
└───────────────────┬──────────────┬──────────────┬──────────┘
                    │              │              │
         ┏━━━━━━━━━━┻━━━━━━━━━━┓  │              │
         ┃   PARALLEL EXECUTION  ┃  │              │
         ┗━━━━━━━━━━┳━━━━━━━━━━┛  │              │
                    │              │              │
     ┌──────────────▼──┐  ┌────────▼───────┐  ┌──▼──────────────┐
     │  SUBAGENT #1    │  │ SUBAGENT #2    │  │  SUBAGENT #3    │
     │  (Primary)      │  │ (Orthogonal 1) │  │  (Orthogonal 2) │
     │                 │  │                │  │                 │
     │  Context: 150K  │  │ Context: 150K  │  │  Context: 150K  │
     │                 │  │                │  │                 │
     │  ┌───────────┐  │  │ ┌───────────┐ │  │  ┌───────────┐  │
     │  │ 1. Search │  │  │ │ 1. Search │ │  │  │ 1. Search │  │
     │  │   Serper  │  │  │ │   Serper  │ │  │  │   Serper  │  │
     │  │   API     │  │  │ │   API     │ │  │  │   API     │  │
     │  └─────┬─────┘  │  │ └─────┬─────┘ │  │  └─────┬─────┘  │
     │        │        │  │       │       │  │        │        │
     │  ┌─────▼─────┐  │  │ ┌─────▼─────┐ │  │  ┌─────▼─────┐  │
     │  │ 2. Get 10 │  │  │ │ 2. Get 10 │ │  │  │ 2. Get 10 │  │
     │  │    URLs   │  │  │ │    URLs   │ │  │  │    URLs   │  │
     │  └─────┬─────┘  │  │ └─────┬─────┘ │  │  └─────┬─────┘  │
     │        │        │  │       │       │  │        │        │
     │  ┌─────▼─────┐  │  │ ┌─────▼─────┐ │  │  ┌─────▼─────┐  │
     │  │ 3. Scrape │  │  │ │ 3. Scrape │ │  │  │ 3. Scrape │  │
     │  │   Content │  │  │ │   Content │ │  │  │   Content │  │
     │  │   (10x)   │  │  │ │   (10x)   │ │  │  │   (10x)   │  │
     │  └─────┬─────┘  │  │ └─────┬─────┘ │  │  └─────┬─────┘  │
     │        │        │  │       │       │  │        │        │
     │  ┌─────▼─────┐  │  │ ┌─────▼─────┐ │  │  ┌─────▼─────┐  │
     │  │ 4. Save   │  │  │ │ 4. Save   │ │  │  │ 4. Save   │  │
     │  │   to JSON │  │  │ │   to JSON │ │  │  │   to JSON │  │
     │  └─────┬─────┘  │  │ └─────┬─────┘ │  │  └─────┬─────┘  │
     │        │        │  │       │       │  │        │        │
     │  ┌─────▼─────┐  │  │ ┌─────▼─────┐ │  │  ┌─────▼─────┐  │
     │  │ 5. Return │  │  │ │ 5. Return │ │  │  │ 5. Return │  │
     │  │  COMPACT  │  │  │ │  COMPACT  │ │  │  │  COMPACT  │  │
     │  │  Summary  │  │  │ │  Summary  │ │  │  │  Summary  │  │
     │  └─────┬─────┘  │  │ └─────┬─────┘ │  │  └─────┬─────┘  │
     └────────┼────────┘  └────────┼───────┘  └────────┼────────┘
              │                    │                    │
              └────────────┬───────┴────────────────────┘
                           │
                           ▼
     ┌─────────────────────────────────────────────────────────┐
     │              ORCHESTRATOR RECEIVES                       │
     │                                                          │
     │  Result 1: { query_type: "primary",                     │
     │              articles: [10 compact summaries] }          │
     │                                                          │
     │  Result 2: { query_type: "orthogonal_1",                │
     │              articles: [10 compact summaries] }          │
     │                                                          │
     │  Result 3: { query_type: "orthogonal_2",                │
     │              articles: [10 compact summaries] }          │
     │                                                          │
     │  Total context usage: ~15K tokens ✅                    │
     └─────────────────┬───────────────────────────────────────┘
                       │
                       ▼
     ┌─────────────────────────────────────────────────────────┐
     │              REPORT GENERATION                           │
     │                                                          │
     │  Orchestrator synthesizes findings:                      │
     │  - Reads compact summaries (in context)                  │
     │  - Optionally reads full content from files              │
     │  - Generates comprehensive markdown report               │
     └─────────────────┬───────────────────────────────────────┘
                       │
                       ▼
     ┌─────────────────────────────────────────────────────────┐
     │                   FILE SYSTEM                            │
     │                                                          │
     │  research_sessions/2025-01-15_14-30-45/                 │
     │  ├── queries.json                                        │
     │  ├── research_results_primary.json     (Full content)    │
     │  ├── research_results_orthogonal_1.json (Full content)   │
     │  ├── research_results_orthogonal_2.json (Full content)   │
     │  └── final_report.md                                     │
     └──────────────────────────────────────────────────────────┘
```

---

## File-Based Context Sharing

### Why Files Instead of Context?

**Option A: Pass Full Content in Context** ❌
```python
# BAD: This would overflow context!
def bad_approach():
    results = {
        "articles": [
            {
                "title": "...",
                "url": "...",
                "full_content": "...15,000 tokens of content..."  # ❌ Too big!
            }
            # × 30 articles = 450,000 tokens! ⚠️ OVERFLOW!
        ]
    }
    return results
```

**Option B: Use File System** ✅
```python
# GOOD: Store in files, pass only references
def good_approach():
    # Subagent saves full content to file
    self.save_json("research_results_primary.json", {
        "articles": [full_article_data]  # Full 15K tokens per article
    })

    # Return only compact summary to orchestrator
    return {
        "articles": [
            {
                "title": "...",
                "url": "...",
                "content_preview": "first 500 chars...",  # Only 125 tokens!
                "file_ref": "research_results_primary.json"
            }
        ]
    }
```

### File System as "Shared Memory"

Think of the file system as a **shared memory space** that doesn't consume context:

```
┌─────────────────────────────────────────┐
│        AGENT MEMORY (Context)           │
│  - Consumed from 200K token budget      │
│  - Must be minimized                    │
│  - Volatile (exists only during run)    │
└─────────────────────────────────────────┘
                    vs
┌─────────────────────────────────────────┐
│        FILE SYSTEM (Disk)               │
│  - No token cost                        │
│  - Can store unlimited data             │
│  - Persistent (survives between runs)   │
│  - Accessible by any agent              │
└─────────────────────────────────────────┘
```

---

## Parallel Execution Model

### Sequential vs Parallel

**Sequential Execution** (Traditional):
```python
# BAD: Slow, linear processing
async def sequential_research():
    result1 = await search_and_scrape(query1)  # 20 seconds
    result2 = await search_and_scrape(query2)  # 20 seconds
    result3 = await search_and_scrape(query3)  # 20 seconds
    # Total: 60 seconds ⏱️
```

**Parallel Execution** (Our Approach):
```python
# GOOD: Fast, concurrent processing
async def parallel_research():
    results = await asyncio.gather(
        search_and_scrape(query1),  # ┐
        search_and_scrape(query2),  # ├─ All execute simultaneously
        search_and_scrape(query3)   # ┘
    )
    # Total: 20 seconds ⚡ (3x faster!)
```

### Parallel Safety

Each subagent is **completely isolated**:

```python
# Each subagent gets its own:
# 1. ClaudeSDKClient instance
# 2. Context window
# 3. Tool access
# 4. Session state

subagent1 = ClaudeSDKClient(options=options1)  # Isolated
subagent2 = ClaudeSDKClient(options=options2)  # Isolated
subagent3 = ClaudeSDKClient(options=options3)  # Isolated

# No shared state = No race conditions ✅
# No context pollution = Clean separation ✅
```

---

## Best Practices

### 1. **Always Return Compact Summaries**

```python
# ✅ GOOD: Compact return
return {
    "title": article.title,
    "url": article.url,
    "snippet": article.snippet[:200],
    "content_preview": article.content[:500]
}

# ❌ BAD: Full content return
return {
    "title": article.title,
    "url": article.url,
    "full_content": article.content  # Could be 15K tokens!
}
```

### 2. **Use File System for Large Data**

```python
# ✅ GOOD: Save to file, reference in context
self.save_json("large_dataset.json", huge_data)
return {"data_reference": "large_dataset.json", "summary": brief_summary}

# ❌ BAD: Include in return value
return {"full_data": huge_data}
```

### 3. **Limit Subagent Context**

```python
# ✅ GOOD: Focused system prompt
system_prompt = """
You are a research agent. Your task:
1. Search for: {query}
2. Scrape top 10 results
3. Return compact summaries

DO NOT include full article text in your response.
"""

# ❌ BAD: Verbose, unfocused prompt
system_prompt = """
You are an amazing research assistant with incredible capabilities...
[thousands of unnecessary tokens]
"""
```

### 4. **Implement Token Budgets**

```python
# ✅ GOOD: Monitor and limit context usage
class ResearchAgent:
    MAX_CONTEXT_TOKENS = 150_000
    MAX_RETURN_TOKENS = 5_000

    def ensure_compact_return(self, data):
        # Truncate if needed to stay under budget
        if estimate_tokens(data) > self.MAX_RETURN_TOKENS:
            data = self.truncate_to_limit(data, self.MAX_RETURN_TOKENS)
        return data
```

### 5. **Use Async for Parallelism**

```python
# ✅ GOOD: True parallelism with asyncio
async def parallel_tasks():
    results = await asyncio.gather(
        task1(),
        task2(),
        task3()
    )

# ❌ BAD: Sequential execution
async def sequential_tasks():
    r1 = await task1()
    r2 = await task2()
    r3 = await task3()
```

---

## Performance Metrics

### Context Usage Breakdown

| Component | Context Tokens | Percentage |
|-----------|---------------|------------|
| Orchestrator Base | 5,000 | 10% |
| Refined Queries | 500 | 1% |
| Subagent Returns (3×) | 9,000 | 18% |
| Report Generation | 35,000 | 71% |
| **Total Orchestrator** | **49,500** | **~50K** ✅ |

### Subagent Context (Per Agent)

| Component | Context Tokens | Percentage |
|-----------|---------------|------------|
| Search Query | 50 | 0.03% |
| Search Results (10) | 5,000 | 3.3% |
| Scraped Content (10) | 140,000 | 93.3% |
| Instructions | 5,000 | 3.3% |
| **Total Per Subagent** | **150,050** | **~150K** ✅ |

### Time Comparison

| Approach | Time | Speedup |
|----------|------|---------|
| Sequential | 60s | 1x |
| Parallel (Our System) | 20s | 3x ⚡ |

---

## Conclusion

The Research Orchestrator demonstrates **enterprise-grade context management** through:

1. **Hierarchical Isolation**: Each layer maintains appropriate context size
2. **Compact Communication**: Only essential data flows between layers
3. **File-Based Storage**: Large data stored externally, not in context
4. **Parallel Execution**: 3x speedup through concurrent subagent operation
5. **Token Budgeting**: Strict limits prevent context overflow

This architecture enables **scalable research** with dozens of sources while maintaining optimal performance and staying well within context limits.

---

**Ready to scale? Try increasing to 5 subagents with 20 results each - the architecture handles it!** 🚀
