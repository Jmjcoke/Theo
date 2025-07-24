# Agent Quick Reference Guide
*Eliminate search delays - Direct paths to all agent resources*

## 🏃 Scrum Master (sm) Agent Resources

### Core Templates
- **Story Template**: `.bmad-core/templates/story-tmpl.yaml`
- **PRD Template**: `.bmad-core/templates/prd-tmpl.yaml`
- **Brownfield Story Template**: `.bmad-core/templates/brownfield-prd-tmpl.yaml`

### Primary Tasks
- **Create Next Story**: `.bmad-core/tasks/create-next-story.md`
- **Execute Checklist**: `.bmad-core/tasks/execute-checklist.md`
- **Correct Course**: `.bmad-core/tasks/correct-course.md`

### Checklists
- **Story Draft Checklist**: `.bmad-core/checklists/story-draft-checklist.md`
- **Story Definition of Done**: `.bmad-core/checklists/story-dod-checklist.md`

## 📝 Product Owner (po) Agent Resources

### Core Templates
- **Story Template**: `.bmad-core/templates/story-tmpl.yaml`
- **Architecture Template**: `.bmad-core/templates/architecture-tmpl.yaml`

### Primary Tasks
- **Validate Next Story**: `.bmad-core/tasks/validate-next-story.md`
- **Shard Document**: `.bmad-core/tasks/shard-doc.md`
- **Execute Checklist**: `.bmad-core/tasks/execute-checklist.md`
- **Correct Course**: `.bmad-core/tasks/correct-course.md`

### Checklists
- **PO Master Checklist**: `.bmad-core/checklists/po-master-checklist.md`
- **Change Checklist**: `.bmad-core/checklists/change-checklist.md`

## 🛠️ Development (dev) Agent Resources

### Core Architecture Documents
- **Coding Standards**: `docs/architecture/coding-standards.md`
- **Tech Stack**: `docs/architecture/tech-stack.md`
- **Source Tree**: `docs/architecture/source-tree.md`
- **Backend Architecture**: `docs/architecture/backend-architecture/` (sharded)
- **REST API Spec**: `docs/architecture/rest-api-spec/` (sharded)
- **Testing Strategy**: `docs/architecture/testing-strategy.md`

### Templates
- **Architecture Template**: `.bmad-core/templates/architecture-tmpl.yaml`
- **Frontend Architecture**: `.bmad-core/templates/front-end-architecture-tmpl.yaml`

### Project Context
- **PRD Main**: `docs/prd.md`
- **Stories Directory**: `docs/stories/`

## 🔍 QA (qa) Agent Resources

### Primary Tasks
- **Review Story**: `.bmad-core/tasks/review-story.md`
- **Execute Checklist**: `.bmad-core/tasks/execute-checklist.md`

### Checklists
- **Story DOD Checklist**: `.bmad-core/checklists/story-dod-checklist.md`
- **Change Checklist**: `.bmad-core/checklists/change-checklist.md`

### Testing References
- **Testing Strategy**: `docs/architecture/testing-strategy.md`

## 🏗️ Architect Agent Resources

### Core Templates
- **Architecture Template**: `.bmad-core/templates/architecture-tmpl.yaml`
- **Fullstack Architecture**: `.bmad-core/templates/fullstack-architecture-tmpl.yaml`
- **Frontend Architecture**: `.bmad-core/templates/front-end-architecture-tmpl.yaml`
- **Brownfield Architecture**: `.bmad-core/templates/brownfield-architecture-tmpl.yaml`

### Checklists
- **Architect Checklist**: `.bmad-core/checklists/architect-checklist.md`

### Primary Tasks
- **Document Project**: `.bmad-core/tasks/document-project.md`
- **Create Doc**: `.bmad-core/tasks/create-doc.md`

## 📊 Project Manager (pm) Agent Resources

### Templates
- **Project Brief**: `.bmad-core/templates/project-brief-tmpl.yaml`
- **Market Research**: `.bmad-core/templates/market-research-tmpl.yaml`
- **Competitor Analysis**: `.bmad-core/templates/competitor-analysis-tmpl.yaml`

### Checklists
- **PM Checklist**: `.bmad-core/checklists/pm-checklist.md`

### Primary Tasks
- **Facilitate Brainstorming**: `.bmad-core/tasks/facilitate-brainstorming-session.md`
- **Advanced Elicitation**: `.bmad-core/tasks/advanced-elicitation.md`

## 🎨 UX Expert Agent Resources

### Templates
- **Frontend Spec**: `.bmad-core/templates/front-end-spec-tmpl.yaml`
- **Frontend Architecture**: `.bmad-core/templates/front-end-architecture-tmpl.yaml`

### Primary Tasks
- **Generate AI Frontend Prompt**: `.bmad-core/tasks/generate-ai-frontend-prompt.md`

## 📈 Analyst Agent Resources

### Templates
- **Market Research**: `.bmad-core/templates/market-research-tmpl.yaml`
- **Competitor Analysis**: `.bmad-core/templates/competitor-analysis-tmpl.yaml`
- **Brainstorming Output**: `.bmad-core/templates/brainstorming-output-tmpl.yaml`

### Primary Tasks
- **Create Deep Research Prompt**: `.bmad-core/tasks/create-deep-research-prompt.md`
- **KB Mode Interaction**: `.bmad-core/tasks/kb-mode-interaction.md`

### Data Resources
- **BMad Knowledge Base**: `.bmad-core/data/bmad-kb.md`
- **Technical Preferences**: `.bmad-core/data/technical-preferences.md`
- **Brainstorming Techniques**: `.bmad-core/data/brainstorming-techniques.md`
- **Elicitation Methods**: `.bmad-core/data/elicitation-methods.md`

## 🚀 Universal Resources

### Workflows
- **Brownfield Fullstack**: `.bmad-core/workflows/brownfield-fullstack.yaml`
- **Brownfield Service**: `.bmad-core/workflows/brownfield-service.yaml`
- **Brownfield UI**: `.bmad-core/workflows/brownfield-ui.yaml`
- **Greenfield Fullstack**: `.bmad-core/workflows/greenfield-fullstack.yaml`
- **Greenfield Service**: `.bmad-core/workflows/greenfield-service.yaml`
- **Greenfield UI**: `.bmad-core/workflows/greenfield-ui.yaml`

### Agent Teams
- **Team All**: `.bmad-core/agent-teams/team-all.yaml`
- **Team Fullstack**: `.bmad-core/agent-teams/team-fullstack.yaml`
- **Team No UI**: `.bmad-core/agent-teams/team-no-ui.yaml`
- **Team IDE Minimal**: `.bmad-core/agent-teams/team-ide-minimal.yaml`

### Utilities
- **Workflow Management**: `.bmad-core/utils/workflow-management.md`
- **BMad Doc Template**: `.bmad-core/utils/bmad-doc-template.md`

## 📋 Quick Search Patterns

Instead of using wildcards, agents should reference this file first:

### For Story Templates:
✅ **Direct**: `.bmad-core/templates/story-tmpl.yaml`  
❌ **Avoid**: `**/*story*template*.yaml`

### For Tasks:
✅ **Direct**: `.bmad-core/tasks/create-next-story.md`  
❌ **Avoid**: `**/*create*story*.md`

### For Architecture Docs:
✅ **Direct**: `docs/architecture/coding-standards.md`  
❌ **Avoid**: `**/*coding*standards*.md`

---
*This file eliminates agent search delays by providing direct paths to all resources. Always check this file FIRST before doing wildcard searches.*