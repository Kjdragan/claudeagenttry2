# 📚 Quick Reference Guide

## 🚀 Getting Started (3 Steps)

### 1. Install Dependencies
```bash
pip install -r requirements.txt
```

### 2. Set API Keys
```bash
export ANTHROPIC_API_KEY="your_anthropic_key"
export SERPERDEV_API_KEY="your_serper_key"
```

### 3. Launch
```bash
# Option A: Streamlit UI (Recommended)
streamlit run app.py

# Option B: CLI
python research_orchestrator.py

# Option C: Quick Start Script
./start.sh
```

---

## 🎯 Key Commands

### Streamlit UI
```bash
streamlit run app.py
# Access: http://localhost:8501
```

### Test Setup
```bash
python test_setup.py
```

### Quick Start
```bash
./start.sh
```

---

## 📂 File Structure

```
research_orchestrator/
├── app.py                    # Streamlit UI
├── research_orchestrator.py  # Core orchestrator logic
├── requirements.txt          # Python dependencies
├── test_setup.py            # Setup validation
├── start.sh                 # Quick start script
├── .env.example             # API key template
├── README.md                # Full documentation
├── ARCHITECTURE.md          # Technical deep dive
└── research_sessions/       # Output directory (created on first run)
    └── YYYY-MM-DD_HH-MM-SS/
        ├── queries.json
        ├── research_results_primary.json
        ├── research_results_orthogonal_1.json
        ├── research_results_orthogonal_2.json
        └── final_report.md
```

---

## 🔧 Configuration Options

### In Streamlit UI
- **API Keys**: Enter in sidebar
- **Results per query**: Slider (5-20)
- **View Options**: Multiple tabs for different views

### In Code
```python
orchestrator = ResearchOrchestrator(
    serper_api_key="your_key",
    num_results=10  # Configurable: 5-20
)
```

---

## 🎨 Streamlit UI Features

### Main Interface
- 💬 **Chat-style query input**
- 📡 **Real-time process monitoring**
- 📊 **Result visualization**
- 📄 **Markdown report rendering**

### Tabs
1. **📄 Final Report**: Rendered markdown with download
2. **🔍 Query Analysis**: Shows query refinement reasoning
3. **📁 Raw Data**: JSON data and file references

### Status Monitoring
- ✅ Success messages (green)
- ❌ Error messages (red)
- ℹ️ Info messages (blue)
- ⚠️ Warning messages (yellow)

---

## 📊 Understanding Output

### Session Directory
```
research_sessions/2025-01-15_14-30-45/
```
- Timestamped for easy tracking
- Contains all research data
- Preserves complete audit trail

### queries.json
```json
{
  "original": "user query",
  "primary": "optimized query",
  "orthogonal_1": "related angle 1",
  "orthogonal_2": "related angle 2",
  "reasoning": {...}
}
```

### research_results_*.json
```json
{
  "query_type": "primary",
  "query": "actual search",
  "num_articles": 10,
  "articles": [
    {
      "position": 1,
      "title": "...",
      "url": "...",
      "snippet": "...",
      "content_preview": "...",
      "content_length": 5420,
      "scraped": true
    }
  ]
}
```

### final_report.md
- Professional markdown format
- Executive summary
- Methodology
- Key findings per search angle
- Synthesis & conclusions
- Complete bibliography

---

## 🔍 Monitoring & Debugging

### Status Messages

#### Agent Activity
```
🤖 Subagent [primary] started
📄 Subagent [primary] scraping 10 articles...
✓ [primary] Scraped 1/10: Article Title...
✅ Subagent [primary] completed - 10 articles processed
```

#### File Operations
```
📁 Created session directory: research_sessions/2025-01-15_14-30-45
💾 Saved: queries.json
💾 Saved: research_results_primary.json
```

#### API Calls
```
🔍 Searching: 'optimized query'
✅ Found 10 results for: 'optimized query'
```

---

## ⚡ Performance Tips

### Optimize Speed
- **Reduce num_results**: 5-7 for quick research
- **Use concise queries**: Helps with faster searches

### Maximize Thoroughness
- **Increase num_results**: 15-20 for deep research
- **Review orthogonal queries**: Ensure good coverage

### Balance Both
- **Default (10 results)**: Good balance
- **Primary + 2 orthogonal**: Multiple perspectives

---

## 🐛 Troubleshooting

### "API Key Not Set"
```bash
export ANTHROPIC_API_KEY="sk-..."
export SERPERDEV_API_KEY="..."
```

### "Module Not Found"
```bash
pip install -r requirements.txt
```

### "Rate Limit Exceeded"
- Wait a few minutes
- Reduce num_results
- Check Serper.dev quota

### "Context Window Exceeded"
- This shouldn't happen! The system is designed to prevent it
- If it does: reduce num_results to 5-7
- Report as a bug

### "Search Returns No Results"
- Check internet connection
- Verify Serper API key is valid
- Try a different query

---

## 🎓 Best Practices

### Writing Queries

**Good Examples:**
```
✅ "Latest developments in transformer architectures"
✅ "Comparison of vector database technologies"
✅ "State of autonomous vehicle regulations 2024"
```

**Bad Examples:**
```
❌ "AI" (too broad)
❌ "good coding" (too vague)
❌ "news" (needs specificity)
```

### Interpreting Results

1. **Read Executive Summary**: Quick overview
2. **Check Primary Research**: Direct answers
3. **Review Orthogonal Searches**: Additional context
4. **Cross-reference Sources**: Verify consistency
5. **Note Publication Dates**: Assess timeliness

### Using File System

```bash
# Navigate to session directory
cd research_sessions/2025-01-15_14-30-45

# View queries
cat queries.json | jq

# Count articles
cat research_results_*.json | jq '.num_articles'

# View report
cat final_report.md
```

---

## 📈 Scaling Up

### More Results
```python
orchestrator = ResearchOrchestrator(
    serper_api_key="key",
    num_results=20  # Up from 10
)
```

### More Subagents
```python
# Modify _execute_parallel_research to add more
query_types = [
    "primary",
    "orthogonal_1",
    "orthogonal_2",
    "orthogonal_3",  # Add more!
    "orthogonal_4"
]
```

### Custom Search Logic
```python
# Override serper_search method
def custom_search(self, query):
    # Your custom search logic
    pass
```

---

## 🔗 Useful Links

- **Anthropic Console**: https://console.anthropic.com
- **Serper.dev**: https://serper.dev
- **Claude Agent SDK Docs**: https://docs.claude.com/en/api/agent-sdk
- **Streamlit Docs**: https://docs.streamlit.io

---

## 💡 Pro Tips

1. **Save Good Queries**: Keep a note of effective search queries
2. **Compare Sessions**: Look at different timestamp directories
3. **Export Reports**: Download markdown for external use
4. **Monitor Context**: Check status logs for any warnings
5. **Iterate Queries**: Refine based on initial results

---

## 📞 Support

### Check Documentation
1. README.md - Complete guide
2. ARCHITECTURE.md - Technical details
3. This file - Quick reference

### Test Your Setup
```bash
python test_setup.py
```

### Common Solutions
- Restart Streamlit: Ctrl+C then restart
- Clear browser cache: Hard refresh (Ctrl+Shift+R)
- Check logs: Look in terminal for error messages

---

**Happy Researching! 🔬✨**

Last Updated: 2025-01-15
