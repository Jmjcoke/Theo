# 🧪 Coding Patterns & Standards Quick Reference

**AI Agent Search Terms:** `coding patterns`, `code patterns`, `style guide`, `coding standards`, `conventions`, `guidelines`

## 🚨 Critical PocketFlow Constraints (MANDATORY)

### **150-Line Node Limit**
- **EVERY PocketFlow Node MUST NOT exceed 150 lines**
- Validate with: `wc -l {node_file}.py` ≤ 150
- Break complex logic into multiple Nodes if needed

### **PocketFlow Architecture Patterns**
```python
# Node Structure (REQUIRED)
class ExampleNode:
    def prep(self, shared_store):
        # Prepare data, validate inputs
        pass
    
    def exec(self, shared_store):
        # Core business logic
        pass
    
    def post(self, shared_store):
        # Cleanup, store results
        pass
```

## 📁 File Naming Conventions

### **PocketFlow Components**
- **Nodes**: `{purpose}_node.py` → `login_node.py`, `parse_node.py`
- **Flows**: `{workflow}_flow.py` → `auth_flow.py`, `chat_flow.py`
- **Classes**: `{Purpose}Node`, `{Workflow}Flow`

### **General File Naming**
- **Directories**: `kebab-case` → `user-management`, `document-processing`
- **React Components**: `PascalCase` → `UserDashboard.tsx`, `DocumentTable.tsx`
- **Utilities**: `camelCase` → `apiClient.ts`, `dateUtils.ts`
- **Constants**: `SCREAMING_SNAKE_CASE` → `MAX_FILE_SIZE`, `API_BASE_URL`

### **Database & API**
- **Tables/Columns**: `snake_case` → `users`, `user_id`, `created_at`
- **API Endpoints**: `kebab-case` → `/api/user-management`, `/api/document-upload`
- **JSON Keys**: `camelCase` → `userId`, `createdAt`, `processingStatus`

## 🏗️ PocketFlow File Organization

```
apps/api/src/
├── nodes/{category}/{purpose}_node.py     # Sync nodes
├── flows/{workflow}_flow.py               # Sync flows
apps/workers/src/
├── nodes/{category}/{purpose}_node.py     # Async nodes  
├── flows/{workflow}_flow.py               # Async flows
```

## 🔗 Complete Standards Documentation

| **Topic** | **Location** | **Purpose** |
|-----------|--------------|-------------|
| **Coding Standards** | `docs/architecture/coding-standards.md` | Complete naming & quality standards |
| **PocketFlow Patterns** | `system_instructions.md` | 1,669 lines of framework patterns |
| **Development Guide** | `.cursorrules` | Comprehensive dev guidance |
| **Tech Stack** | `docs/architecture/tech-stack.md` | Technology decisions |
| **Project Structure** | `docs/architecture/source-tree.md` | File organization |
| **API Standards** | `docs/architecture/rest-api-spec.md` | REST API conventions |

## ⚡ Quick Commands

```bash
# Validate Node size limit
wc -l apps/api/src/nodes/**/*_node.py

# Check coding standards
cat docs/architecture/coding-standards.md

# View PocketFlow patterns  
cat system_instructions.md

# Format code
npm run lint && npm run format
```

## 🎯 Dev Agent Priority

1. **ALWAYS** check PocketFlow 150-line Node limit first
2. Reference cookbook patterns: `PocketFlow-main/cookbook/`
3. Follow naming conventions exactly as specified
4. Use AsyncNode for I/O operations, Node for business logic

---

**For Complete Details**: See `docs/architecture/coding-standards.md`