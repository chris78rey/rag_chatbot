# ⚡ Quick Start — Configuration Setup

## 🎯 Objective

Get your RAF Chatbot configuration running in **5 minutes**.

---

## Step 1: Copy Client Configuration

**Source:**
```
G:\zed_projects\raf_chatbot\configs\client\client.yaml.example
```

**Action:**
1. Copy this file to the same directory
2. Rename to `client.yaml`
3. No changes needed for local Docker development

**Result:**
```
G:\zed_projects\raf_chatbot\configs\client\client.yaml
```

---

## Step 2: Copy RAG Configuration

**Source:**
```
G:\zed_projects\raf_chatbot\configs\rags\example_rag.yaml
```

**Action:**
1. Copy this file to the same directory
2. Rename to `my_first_rag.yaml` (or any name you want)
3. Adjust these fields:
   - `rag_id`: change to `my_first_rag`
   - `collection.name`: change to `my_first_rag_docs`
   - `sources.directory`: change to `my_first_rag_sources`

**Result:**
```
G:\zed_projects\raf_chatbot\configs\rags\my_first_rag.yaml
```

---

## Step 3: Create Source Directory

**Action:**
Create the directory for your RAG documents:
```
G:\zed_projects\raf_chatbot\data\sources\my_first_rag_sources\
```

Add your documents here (.pdf, .txt, .md, .docx)

---

## Step 4: Create Prompt Templates

**Action:**
Create the templates directory and files:
```
G:\zed_projects\raf_chatbot\configs\templates\
```

Create `system_prompt.txt`:
```
You are a helpful assistant. Answer questions based on the provided context.
Always cite your sources.

Context:
{{ context }}
```

Create `user_prompt.txt`:
```
User Query: {{ query }}

Previous History:
{{ history }}

Please answer based on the context provided above.
```

---

## Step 5: Set Environment Variable

**Action:**
Set your OpenRouter API key:

**On Windows (Command Prompt):**
```cmd
set OPENROUTER_API_KEY=sk-your-api-key-here
```

**On Windows (PowerShell):**
```powershell
$env:OPENROUTER_API_KEY='sk-your-api-key-here'
```

**On Linux/Mac:**
```bash
export OPENROUTER_API_KEY='sk-your-api-key-here'
```

---

## Step 6: Verify Configuration

**Check file structure:**
```
G:\zed_projects\raf_chatbot\
├── configs/
│   ├── client/
│   │   ├── client.yaml              ✅
│   │   └── client.yaml.example      (keep for reference)
│   ├── rags/
│   │   ├── my_first_rag.yaml        ✅
│   │   └── example_rag.yaml         (keep for reference)
│   └── templates/
│       ├── system_prompt.txt        ✅
│       └── user_prompt.txt          ✅
│
└── data/
    └── sources/
        └── my_first_rag_sources/    ✅ (with your docs)
```

---

## Quick Reference

### Main Configuration File
**Path:** `G:\zed_projects\raf_chatbot\configs\client\client.yaml`

**Key Fields:**
- `app.port`: 8000 (FastAPI port)
- `qdrant.url`: http://qdrant:6333 (Vector DB)
- `redis.url`: redis://redis:6379/0 (Cache)
- `llm.api_key_env_var`: OPENROUTER_API_KEY

### RAG Configuration File
**Path:** `G:\zed_projects\raf_chatbot\configs\rags\my_first_rag.yaml`

**Key Fields:**
- `rag_id`: unique identifier
- `collection.name`: Qdrant collection name (unique per RAG)
- `embeddings.model_name`: sentence-transformers/all-MiniLM-L6-v2
- `sources.directory`: subdirectory in data/sources/

---

## What's Next?

1. **Start Docker**: `make docker-up`
2. **Ingest Documents**: (Subproject 5+)
3. **Query Your RAG**: (Subproject 5+)
4. **Monitor**: Check logs with `make docker-logs-api`

---

## Troubleshooting

### "Collection not found"
- Check `collection.name` in your RAG yaml matches what's in Qdrant
- Ensure `sources.directory` exists and has files

### "API Key Error"
- Verify `OPENROUTER_API_KEY` environment variable is set
- Check it's a valid OpenRouter key

### "Template file not found"
- Verify paths in `prompting.system_template_path` and `user_template_path`
- Files should exist in `configs/templates/`

---

## Full Documentation

For complete field reference and examples:
```
G:\zed_projects\raf_chatbot\docs\configuration.md
```

---

## Validation Checklist

Before running:
- [ ] `configs/client/client.yaml` exists
- [ ] `configs/rags/my_first_rag.yaml` exists
- [ ] `data/sources/my_first_rag_sources/` exists with documents
- [ ] `configs/templates/system_prompt.txt` exists
- [ ] `configs/templates/user_prompt.txt` exists
- [ ] `OPENROUTER_API_KEY` environment variable is set

---

**Next Subproject**: Schema Validation (validates YAML syntax)