-- Document Editor Module Database Schema
-- Extends existing SQLite schema for document editing functionality
-- Created: 2025-07-31
-- Version: 1.0

-- Document Editor Tables
CREATE TABLE editor_documents (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL,
    title TEXT NOT NULL,
    content TEXT NOT NULL,  -- Rich text/markdown content
    template_id TEXT,       -- References predefined templates
    document_type TEXT NOT NULL CHECK (document_type IN ('sermon', 'article', 'research_paper', 'lesson_plan', 'devotional')),
    status TEXT NOT NULL DEFAULT 'draft' CHECK (status IN ('draft', 'published', 'archived')),
    version INTEGER NOT NULL DEFAULT 1,
    word_count INTEGER DEFAULT 0,
    reading_time INTEGER DEFAULT 0, -- in minutes
    metadata TEXT,          -- JSON: formatting preferences, export settings
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
);

-- Document Version History
CREATE TABLE editor_document_versions (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    document_id INTEGER NOT NULL,
    version_number INTEGER NOT NULL,
    content TEXT NOT NULL,
    change_summary TEXT,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (document_id) REFERENCES editor_documents(id) ON DELETE CASCADE
);

-- Templates Management
CREATE TABLE editor_templates (
    id TEXT PRIMARY KEY,                    -- UUID string
    name TEXT NOT NULL,
    description TEXT,
    template_content TEXT NOT NULL,         -- Template structure/placeholders
    document_type TEXT NOT NULL CHECK (document_type IN ('sermon', 'article', 'research_paper', 'lesson_plan', 'devotional')),
    is_system BOOLEAN DEFAULT FALSE,        -- System vs user templates  
    created_by INTEGER,                     -- NULL for system templates
    metadata TEXT,                          -- JSON: styling, formatting rules
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (created_by) REFERENCES users(id)
);

-- Citation Links (connects to Supabase RAG sources)
CREATE TABLE editor_citations (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    document_id INTEGER NOT NULL,
    source_id TEXT NOT NULL,               -- Reference to Supabase document ID
    citation_text TEXT NOT NULL,
    position_start INTEGER,                 -- Character position in document
    position_end INTEGER,
    citation_format TEXT DEFAULT 'apa',    -- apa, mla, chicago, turabian
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (document_id) REFERENCES editor_documents(id) ON DELETE CASCADE
);

-- Document Comments (for collaboration)
CREATE TABLE editor_comments (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    document_id INTEGER NOT NULL,
    user_id INTEGER NOT NULL,
    parent_comment_id INTEGER,              -- For threaded discussions
    content TEXT NOT NULL,
    position_start INTEGER,                 -- Text selection start
    position_end INTEGER,                   -- Text selection end
    status TEXT DEFAULT 'active' CHECK (status IN ('active', 'resolved', 'deleted')),
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (document_id) REFERENCES editor_documents(id) ON DELETE CASCADE,
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
    FOREIGN KEY (parent_comment_id) REFERENCES editor_comments(id) ON DELETE CASCADE
);

-- Export History
CREATE TABLE editor_exports (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    document_id INTEGER NOT NULL,
    user_id INTEGER NOT NULL,
    export_format TEXT NOT NULL CHECK (export_format IN ('pdf', 'docx', 'markdown')),
    file_path TEXT NOT NULL,
    file_size INTEGER DEFAULT 0,
    export_status TEXT DEFAULT 'pending' CHECK (export_status IN ('pending', 'completed', 'failed')),
    error_message TEXT,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (document_id) REFERENCES editor_documents(id) ON DELETE CASCADE,
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
);

-- Indexes for performance optimization
CREATE INDEX idx_editor_documents_user_id ON editor_documents(user_id);
CREATE INDEX idx_editor_documents_type ON editor_documents(document_type);
CREATE INDEX idx_editor_documents_status ON editor_documents(status);
CREATE INDEX idx_editor_documents_created_at ON editor_documents(created_at);
CREATE INDEX idx_editor_documents_updated_at ON editor_documents(updated_at);

CREATE INDEX idx_editor_document_versions_document_id ON editor_document_versions(document_id);
CREATE INDEX idx_editor_document_versions_version ON editor_document_versions(version_number);

CREATE INDEX idx_editor_citations_document_id ON editor_citations(document_id);
CREATE INDEX idx_editor_citations_source_id ON editor_citations(source_id);

CREATE INDEX idx_editor_comments_document_id ON editor_comments(document_id);
CREATE INDEX idx_editor_comments_user_id ON editor_comments(user_id);
CREATE INDEX idx_editor_comments_parent ON editor_comments(parent_comment_id);

CREATE INDEX idx_editor_exports_document_id ON editor_exports(document_id);
CREATE INDEX idx_editor_exports_user_id ON editor_exports(user_id);
CREATE INDEX idx_editor_exports_status ON editor_exports(export_status);

-- Triggers to automatically update updated_at timestamps
CREATE TRIGGER update_editor_documents_updated_at 
    AFTER UPDATE ON editor_documents 
    FOR EACH ROW 
    BEGIN
        UPDATE editor_documents SET updated_at = CURRENT_TIMESTAMP WHERE id = NEW.id;
    END;

-- Trigger to automatically update word count and reading time
CREATE TRIGGER update_editor_documents_stats
    AFTER UPDATE OF content ON editor_documents
    FOR EACH ROW
    BEGIN
        UPDATE editor_documents 
        SET 
            word_count = (LENGTH(NEW.content) - LENGTH(REPLACE(NEW.content, ' ', '')) + 1),
            reading_time = CAST((LENGTH(NEW.content) - LENGTH(REPLACE(NEW.content, ' ', '')) + 1) / 200.0 AS INTEGER) + 1
        WHERE id = NEW.id;
    END;

-- Insert default system templates
INSERT INTO editor_templates (id, name, description, template_content, document_type, is_system, metadata) VALUES
('sermon-basic', 'Basic Sermon Template', 'Standard three-point sermon structure', 
'# [Sermon Title]

## Introduction
- Opening illustration or question
- Context and background
- Thesis statement

## Body
### Point 1: [Main Point]
- Scripture reference
- Explanation
- Application

### Point 2: [Main Point]
- Scripture reference
- Explanation
- Application

### Point 3: [Main Point]
- Scripture reference
- Explanation
- Application

## Conclusion
- Summary of main points
- Call to action
- Closing prayer

---
*Sources and Citations will appear here*', 'sermon', TRUE, '{"citation_style": "apa", "font_size": "12pt", "line_spacing": "double"}'),

('research-paper', 'Academic Research Paper', 'Standard academic paper format with citations', 
'# [Paper Title]

**Author:** [Your Name]  
**Institution:** [Institution Name]  
**Date:** [Date]

## Abstract
[150-300 word summary of your research]

## Introduction
- Research question or thesis
- Background and context
- Methodology overview

## Literature Review
- Previous scholarship
- Gaps in current research
- Theoretical framework

## Main Arguments
### Argument 1
- Evidence and analysis
- Supporting sources

### Argument 2
- Evidence and analysis
- Supporting sources

## Conclusion
- Summary of findings
- Implications for further research
- Final thoughts

## Bibliography
*Citations will be automatically generated*', 'research_paper', TRUE, '{"citation_style": "turabian", "font_size": "12pt", "margins": "1inch"}'),

('article-blog', 'Article/Blog Post', 'Engaging article structure for online publication', 
'# [Article Title]

## Hook
Start with a compelling question, statistic, or story that draws readers in.

## Problem/Context
What issue are you addressing? Why should readers care?

## Main Content
### Key Point 1
- Supporting details
- Examples or illustrations
- Biblical or theological insight

### Key Point 2
- Supporting details
- Examples or illustrations
- Biblical or theological insight

### Key Point 3
- Supporting details
- Examples or illustrations
- Biblical or theological insight

## Practical Application
How can readers apply these insights in their daily lives?

## Conclusion
- Summarize key takeaways
- End with inspiration or call to action

---
*Sources and further reading*', 'article', TRUE, '{"citation_style": "apa", "word_target": "1500", "tone": "conversational"}'),

('lesson-plan', 'Bible Study/Lesson Plan', 'Structured lesson plan for teaching', 
'# [Lesson Title]

**Scripture Focus:** [Bible passage]  
**Duration:** [Time estimate]  
**Audience:** [Target group]

## Learning Objectives
By the end of this lesson, participants will be able to:
1. [Objective 1]
2. [Objective 2]
3. [Objective 3]

## Opening (10 minutes)
- Welcome and prayer
- Ice breaker or review
- Introduce today''s topic

## Bible Study (25 minutes)
### Scripture Reading
[Bible passage]

### Discussion Questions
1. [Question 1]
2. [Question 2]
3. [Question 3]

### Key Insights
- [Main teaching point 1]
- [Main teaching point 2]
- [Main teaching point 3]

## Application (15 minutes)
### Personal Reflection
- [Reflection question]

### Group Activity
- [Activity description]

## Closing (10 minutes)
- Summary of key points
- Prayer requests
- Closing prayer

## Materials Needed
- [ ] Bibles
- [ ] Handouts
- [ ] [Other materials]

---
*Teacher Notes and Additional Resources*', 'lesson_plan', TRUE, '{"duration": "60", "group_size": "8-12", "preparation_time": "30"}'),

('devotional', 'Daily Devotional', 'Short inspirational devotional format', 
'# [Devotional Title]

**Date:** [Date]  
**Scripture:** [Bible verse reference]

## Today''s Verse
> "[Quote the main scripture verse here]"
> — [Reference]

## Reflection
[2-3 paragraphs reflecting on the scripture. What does it mean? How does it apply to daily life? What is God teaching us through this passage?]

## Prayer
*Heavenly Father, [personal prayer based on the day''s scripture and reflection. Include thanksgiving, confession, supplication, and commitment.] Amen.*

## Action Step
[One specific, practical way to apply today''s devotional in daily life]

---
*Additional Scriptures for Further Study*
- [Related verse 1]
- [Related verse 2]
- [Related verse 3]', 'devotional', TRUE, '{"word_count_target": "300", "reading_time": "3", "tone": "personal"}'
);