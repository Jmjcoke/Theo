# Theo Project BMad Method Customizations

## Project-Specific Configuration

### Core Configuration (`.bmad-core/core-config.yaml`)
```yaml
slashPrefix: BMad                          # Command prefix for BMad agents
devStoryLocation: docs/stories             # Location of story files
prdSharded: true                          # PRD is broken into shards
prdShardedLocation: docs/prd              # Location of PRD shards
epicFilePattern: epic-{n}*.md             # Pattern for epic files
```

### PocketFlow Integration
- **Framework Version**: PocketFlow v0.0.2
- **Node Size Limit**: 150 lines per Node (strictly enforced)
- **Pattern**: AsyncNode for all database operations
- **Location**: Backend nodes in `apps/api/src/nodes/`
- **Cookbook**: Available in `PocketFlow-main/cookbook/`

### Story Naming Convention
- **Format**: `{epic_number}.{story_number}.{story_title}.md`
- **Example**: `3.1.backend-job-queue-setup.md`
- **Location**: `docs/stories/`
- **Archive**: Old format stories moved to `docs/stories/archive/`
- **Epic Pattern**: `{n}.*.md` (matches all stories in epic)

### DevLoadAlwaysFiles (Auto-loaded for Dev Agent)
1. `CODING_PATTERNS.md` - **Quick reference for all coding standards & patterns**
2. `docs/architecture/coding-standards.md` - Complete coding standards documentation
3. `docs/architecture/tech-stack.md` - Technology stack and decisions
4. `docs/architecture/source-tree.md` - Project structure and organization
5. `system_instructions.md` - Core PocketFlow patterns and constraints
6. `.cursorrules` - Development guidance and workflow patterns

### Agent Specializations
- **BMad Orchestrator**: Master coordinator for workflow management
- **Analyst (Mary)**: Market research and brainstorming
- **Architect**: System design and PocketFlow compliance
- **Developer**: Implementation with 150-line Node limits
- **QA (Quinn)**: Testing and quality validation
- **Scrum Master**: Story management and epic progression

### Web Bundle Support
- **Dual Format**: `.md` files for IDE, `.txt` bundles for web UI
- **Location**: `web-bundles/agents/`
- **Size**: Expanded versions (428-8,755 lines) with all dependencies included

### Current Project State
- **Epic 1**: ✅ Project initialization complete
- **Epic 2**: ✅ Authentication system complete  
- **Epic 3**: 🚧 In progress (Job queue setup)
- **Next Story**: Epic 3.2 (TBD)

### Quality Gates
- ✅ PocketFlow Node compliance (≤150 lines)
- ✅ Story naming convention adherence
- ✅ BMad Method agent validation
- ✅ Test coverage requirements
- ✅ Security validation

### Key Dependencies
1. **PocketFlow**: `pip install -e ./PocketFlow-main`
2. **BMad Method**: v4.31.0 (fully installed)
3. **Python**: 3.12+ for backend
4. **Node.js**: 18+ for frontend
5. **OpenAI API**: Set `OPENAI_API_KEY` in `.env` for PocketFlow examples

### OpenAI Integration
- **Environment Variable**: `OPENAI_API_KEY` (required for PocketFlow cookbook)
- **Utility Module**: `apps/api/src/utils/openai_client.py`
- **Default Model**: gpt-4o
- **Configuration**: Automatic detection from environment

## Validation Commands

```bash
# Test BMad Method integrity
python .bmad-core/utils/story-validator.py

# Verify PocketFlow installation
python -c "import pocketflow; print('PocketFlow imported successfully')"

# Check agent functionality
/BMad:agents:orchestrator    # Use in Claude Code IDE
```

## Maintenance Notes

- **System Health**: All 202 BMad files intact (`install-manifest.yaml`)
- **No Corruption Detected**: Claude Code errors did not damage BMad core
- **Dual Agent Formats**: Normal architecture feature, not corruption
- **Archive Migration**: Successfully moved old story format to archive/

---

**Status**: ✅ BMad Method fully operational and integrated with PocketFlow
**Last Validated**: July 22, 2025