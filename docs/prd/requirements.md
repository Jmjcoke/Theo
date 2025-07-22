# Requirements

## Functional Requirements
* **FR1:** Administrators shall be able to upload documents, categorized as 'biblical' (JSON format) or 'theological' (PDF format).
* **FR2:** The system shall process uploaded documents by loading, chunking, embedding, and storing them.
* **FR3:** Administrators must be able to view the real-time processing status of each uploaded document.
* **FR4:** A user registration system shall allow new users to sign up, with accounts pending admin approval.
* **FR5:** The system will provide two distinct user roles: 'Admin' and 'User'.
* **FR6:** Administrators shall have a dashboard to manage documents and users.
* **FR7:** Authenticated 'User' roles shall be able to interact with a chat interface.
* **FR8:** The RAG pipeline must perform a hybrid search (semantic and keyword).
* **FR9 (Updated):** All answers must include citations. For biblical texts: version, book, chapter, and verse number. For theological works: document name and page/section number.
* **FR10 (Updated):** Users must be able to export the **final, user-edited content** from the editor panel into multiple formats: PDF and Markdown.
* **FR11:** The chat interface shall include an interactive side panel containing a rich-text/markdown editor.
* **FR12:** Users shall be able to select from predefined output templates (e.g., Sermon, Article).
* **FR13:** Users must be able to directly edit and reformat the content within the editor panel.
* **FR14:** Users shall be able to apply formatting templates conversationally through the chat interface.
* **FR15:** The system shall support flexible, user-driven formatting changes via conversational prompts.
* **FR16:** The system must support the ingestion and management of multiple distinct versions of biblical texts.
* **FR17:** The system must be capable of retrieving and displaying large, contiguous blocks of biblical text.
* **FR18:** All AI-generated responses must be processed through a guiding framework of hermeneutical rules.

## Non-Functional Requirements
* **NFR1:** The backend shall be built using Python with the FastAPI web framework.
* **NFR2:** The frontend shall be a single-page application built using React 18 with Vite and TailwindCSS.
* **NFR3:** User authentication shall be managed using JWTs with passwords hashed by bcrypt.
* **NFR4:** Real-time progress updates shall be delivered using Server-Sent Events (SSE).
* **NFR5:** The system will use SQLite for local metadata and Supabase (PostgreSQL with pgvector) for embeddings.
* **NFR6 (Updated):** The system must enforce file upload size limits: 5MB for biblical JSON and **100MB** for theological PDF.
* **NFR7:** The backend business logic **must be implemented using the PocketFlow architectural pattern**.