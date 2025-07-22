# Theo Product Requirements Document (PRD)

### **Goals and Background Context**

**Goals**
* Administrators must be able to upload, manage, and monitor the processing of biblical (JSON) and theological (PDF) documents.
* Users must be able to register and, once approved, query the managed content through an intelligent chat interface.
* The system must provide users with clear, real-time feedback on the status of document uploads and processing.
* The application must enforce secure access controls, distinguishing between "Admin" and "User" roles.
* Users must be able to export chat conversations and their cited sources into multiple formats (PDF, Word, Google Sheets, etc.).

**Background Context**
The "Theo" application is designed to address the need for a specialized Retrieval Augmented Generation (RAG) system tailored specifically for biblical and theological research. The necessity for this custom-built application stems from the fact that foundational LLMs have been predominantly trained on modern theological frameworks (like Reformed Theology) that are in direct opposition to Moral Government Theology. A simple off-the-shelf RAG or Custom GPT would still be susceptible to this bias during the "Generation" phase of its responses. Therefore, a specialized system with a strong "Hermeneutics Filter" is required to ensure that all generated content is purely and verifiably derived from the provided biblical and MGT source texts, creating a 'clean room' for theological research.

**Change Log**
| Date       | Version | Description      | Author |
| :--------- | :------ | :--------------- | :----- |
| 2025-07-21 | 1.0     | Initial draft    | PM     |

**Project Resources**
* **Source Code Repository:** `https://github.com/Jmjcoke/Theo`

### **Project Principles & Lessons Learned**

#### **Trap #1: Inconsistent Development & Deployment Environments**
* **Problem:** The previous version was developed simultaneously on a local machine and in a live production VM, leading to a chaotic, unrepeatable, and error-prone workflow.
* **Principle to Enforce:** **Local-First, Automated Deployment.**
* **Implementation:** 1) All features must be built and tested locally first. 2) The project will use Git and a central repository. 3) We will create a simple, automated deployment pipeline.

#### **Trap #2: Inconsistent Naming and Terminology**
* **Problem:** The previous version used inconsistent names for the same concepts (e.g., "biblical" vs. "Bible").
* **Principle to Enforce:** **Standardized Terminology and Naming Conventions.**
* **Implementation:** 1) This PRD contains a glossary defining official terms. 2) The `architect` agent will produce a "Naming Convention" document.

#### **Trap #3: Architectural Drift and "Massive Node" Violation**
* **Problem:** The previous version violated the PocketFlow philosophy, with nodes growing into massive monoliths.
* **Principle to Enforce:** **Strict Adherence to the PocketFlow Philosophy.**
* **Implementation:** 1) Every `Node` must have a single responsibility. 2) A `Node` **must not** exceed 150 lines of code. 3) Nodes must be stateless. 4) Nodes will be asynchronous.

#### **Trap #4: Disconnected and Opaque Architecture**
* **Problem:** The previous version suffered from confusing authentication, a chaotic folder structure, a brittle upload system, and Supabase misconfiguration.
* **Principle to Enforce:** **A Clear, Documented, and Observable Architecture.**
* **Implementation:** 1) The architect **must** create a detailed Authentication Flow Diagram. 2) The architecture **must** include a Source Tree diagram. 3) The architecture **must** define a robust background job pipeline. 4) The database schema **must** be defined first, and the architecture must include a plan for structured logging.

#### **Trap #5: Outdated AI Knowledge and Dependency Hell**
* **Problem:** The development AI often generated code based on outdated documentation or older versions of libraries.
* **Principle to Enforce:** **Proactive Dependency Management and Pattern Definition.**
* **Implementation:** 1) The `architect` is **required** to define the **exact version number** for every package. 2) The architecture **must** include a "Cookbook" with tested code snippets for critical libraries. 3) The `dev` agent is **required** to use only the pinned versions and patterns.

### **Project Glossary & Data Dictionary**
| Term                | Definition                                                                                    | Standardized Name (for code) |
| :------------------ | :-------------------------------------------------------------------------------------------- | :--------------------------- |
| Biblical Content    | Refers to scriptural texts, like the Bible, provided in a structured JSON format.             | `biblical`                   |
| Theological Content | Refers to secondary works, such as the writings of Gordon C. Olson, in PDF format.            | `theological`                |
| Other Content       | Refers to any content that is not specifically biblical or theological.                       | `other`                      |
| Hermeneutics Filter | The set of guiding principles applied to every LLM generation request.                        | `hermeneutics_filter`        |
| PocketFlow Node     | A single, self-contained unit of work in the backend pipeline.                                | `PocketFlowNode`             |
| PocketFlow Flow     | An orchestration of multiple Nodes to perform a complex task.                                 | `PocketFlow`                 |

### **Requirements**

#### **Functional Requirements**
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

#### **Non-Functional Requirements**
* **NFR1:** The backend shall be built using Python with the FastAPI web framework.
* **NFR2:** The frontend shall be a single-page application built using React 18 with Vite and TailwindCSS.
* **NFR3:** User authentication shall be managed using JWTs with passwords hashed by bcrypt.
* **NFR4:** Real-time progress updates shall be delivered using Server-Sent Events (SSE).
* **NFR5:** The system will use SQLite for local metadata and Supabase (PostgreSQL with pgvector) for embeddings.
* **NFR6 (Updated):** The system must enforce file upload size limits: 5MB for biblical JSON and **100MB** for theological PDF.
* **NFR7:** The backend business logic **must be implemented using the PocketFlow architectural pattern**.

### **User Interface Design Goals**
* **Overall UX Vision:** A dual-interface experience. A data-driven, clean Admin panel, and a minimalist, intuitive User chat interface.
* **Key Interaction Paradigms:** Admin Dashboard, Document Management table, Drag-and-Drop Upload modal, two-column Chat Interface with an interactive document editor panel.
* **Core Screens and Views:** Login, Admin Dashboard, Admin Document Management, Admin User Management, User Chat Interface.
* **Accessibility:** Adhere to **WCAG AA** standards.
* **Branding:** A modern, professional design with a dynamic color theme: a **blue theme (#3B82F6)** for biblical content, a **light maroon theme (#B03060)** for theological, and a **green theme (#10B981)** for other.
* **Target Device and Platforms:** A **Web Responsive** application.

### **Technical Assumptions**
* **Repository Structure:** Monorepo.
* **Service Architecture:** Monolith with PocketFlow Pattern.
* **Testing Requirements:** Unit + Integration.
* **Standardized PDF Pre-processing:** For the MVP, it is assumed that all uploaded PDF documents will be pre-processed by the administrator.
* **Additional Technical Assumptions and Requests:**
    * **Backend Stack:** Python, FastAPI, SQLite, Supabase (Postgres w/ pgvector), JWT, bcrypt, SSE, OpenAI API, Celery/Redis.
    * **Frontend Stack:** React, Vite, TypeScript, TailwindCSS, React Router.

### **Epic & Story Details**

---
#### **Epic 1: Foundational Infrastructure**
**Expanded Goal:** The goal of this epic is to create the complete, foundational skeleton of the application. This includes setting up the monorepo, initializing the frontend and backend applications, establishing the database schemas, and creating a simple, automated deployment pipeline to DigitalOcean.

* **Story 1.1: Project Initialization**
    * **As a** developer, **I want** a standardized monorepo structure with initial Git and linter configurations, **so that** I can begin development in a clean, consistent, and version-controlled environment.
    * **Acceptance Criteria:**
        1.  A Git repository is initialized on GitHub.
        2.  A monorepo is created with a root `package.json` and a folder structure including `apps/` and `packages/`.
        3.  Base linter and TypeScript configurations are added to the root of the monorepo.
        4.  A basic `README.md` file is created with the project title.

* **Story 1.2: Backend App Setup**
    * **As a** developer, **I want** a basic FastAPI backend application with a single health-check endpoint, **so that** I can verify the server is running correctly on my local machine.
    * **Acceptance Criteria:**
        1.  A new FastAPI application named `api` is created within the `apps/` directory.
        2.  All necessary Python dependencies (FastAPI, Uvicorn) are defined and installable.
        3.  A `/health` endpoint is created that returns a `{"status": "ok"}` JSON response.
        4.  The backend server can be started with a single command.

* **Story 1.3: Frontend App Setup**
    * **As a** developer, **I want** a basic React (Vite + TypeScript) frontend application that displays a simple message, **so that** I can verify the frontend build process and development server are working correctly.
    * **Acceptance Criteria:**
        1.  A new React application named `web` is created within the `apps/` directory.
        2.  TailwindCSS is installed and configured.
        3.  The default landing page is modified to display only the text "Welcome to Theo."
        4.  The frontend development server can be started with a single command.

* **Story 1.4: Database Schema Initialization**
    * **As a** developer, **I want** the initial database schemas for both SQLite and Supabase defined and creatable, **so that** the application has a persistent data layer to connect to.
    * **Acceptance Criteria:**
        1.  An SQL script is created that defines the tables for the local SQLite database (`users`, `documents`, etc.).
        2.  An SQL script is created that defines the tables for the Supabase (PostgreSQL) database and enables the `pgvector` extension.
        3.  Instructions are documented for applying these schemas to the respective databases.

* **Story 1.5: Automated Deployment Pipeline**
    * **As a** developer, **I want** a basic, automated CI/CD pipeline, **so that** any code pushed to the `main` branch is automatically built and deployed to our DigitalOcean server.
    * **Acceptance Criteria:**
        1.  A CI/CD pipeline is configured (e.g., using GitHub Actions).
        2.  The pipeline successfully builds both the `api` and `web` applications.
        3.  The pipeline includes a step to deploy the built applications to the DigitalOcean Droplet.
        4.  After a successful deployment, the live backend URL's `/health` endpoint returns `{"status": "ok"}`.
        5.  After a successful deployment, the live frontend URL correctly displays "Welcome to Theo."

---
#### **Epic 2: Secure Authentication System**
**Expanded Goal:** The goal of this epic is to build a robust and secure wall around our application, implementing a complete user registration process, a secure login system using JWTs, a workflow for admins to approve new users, and middleware to protect specific routes.

* **Story 2.1: User Data Model**
    * **As a** developer, **I want** a `User` model and a corresponding database table, **so that** I can securely store and manage user information like credentials, roles, and status.
    * **Acceptance Criteria:**
        1.  A `User` model is defined in the backend code.
        2.  The model includes fields for a unique ID, email, hashed password, role, and status.
        3.  The schema scripts for both SQLite and Supabase are updated to include the `users` table.
        4.  The password field in the database is designed to never store plain-text passwords.

* **Story 2.2: New User Registration**
    * **As a** new user, **I want** to be able to register for an account, **so that** my account can be created with a 'pending' status for admin review.
    * **Acceptance Criteria:**
        1.  A public `/api/register` endpoint is created on the backend.
        2.  The endpoint accepts an email and a password that meets the security policy.
        3.  The user's password is securely hashed using bcrypt before being stored.
        4.  A new record is created in the `users` table with the role set to 'user' and the status set to 'pending'.
        5.  A success message is returned upon successful registration.

* **Story 2.3: Secure User Login**
    * **As an** approved user, **I want** to be able to log in with my email and password, **so that** I can receive a secure authentication token.
    * **Acceptance Criteria:**
        1.  A public `/api/login` endpoint is created on the backend.
        2.  The endpoint authenticates the user's credentials against the hashed password.
        3.  The endpoint prevents login for any user whose status is not 'approved'.
        4.  Upon successful login, the system generates and returns a JWT access token.
        5.  The JWT payload contains the user's ID and role.

* **Story 2.4: Backend Route Protection**
    * **As a** developer, **I want** to create authentication middleware for the backend, **so that** I can protect specific API endpoints from unauthorized access.
    * **Acceptance Criteria:**
        1.  Middleware is implemented in FastAPI that validates the JWT from the `Authorization` header.
        2.  A protected test endpoint is created that is only accessible with a valid 'user' or 'admin' token.
        3.  A protected admin endpoint is created that is *only* accessible with a valid 'admin' token.
        4.  The middleware returns a `401 Unauthorized` or `403 Forbidden` error appropriately.

* **Story 2.5: Frontend Login and Registration UI**
    * **As a** user, **I want** a user-friendly interface for registration and login, **so that** I can easily access the application.
    * **Acceptance Criteria:**
        1.  A `/register` page and a `/login` page with forms are created on the frontend.
        2.  The frontend application securely stores the JWT after login and includes it in all subsequent API requests.
        3.  The application provides a "logout" functionality.
        4.  After a successful login, the user is redirected to a placeholder dashboard page.

---
#### **Epic 3: Upload Interface & Job Queue**
**Expanded Goal:** The goal of this epic is to build the application's primary data-entry point. We will create a user-friendly interface for administrators to upload documents and connect it to a robust backend job queue using Celery and Redis.

* **Story 3.1: Backend Job Queue Setup**
    * **As a** developer, **I want** to integrate Celery and Redis into the FastAPI backend, **so that** the application can reliably manage and execute long-running, asynchronous tasks.
    * **Acceptance Criteria:**
        1.  Redis is configured and integrated as the message broker for Celery.
        2.  A Celery worker process is defined and can be run alongside the main FastAPI application.
        3.  The project's environment configuration includes the necessary settings for the Redis connection.
        4.  A simple test task can be successfully dispatched to the queue and executed by the worker.

* **Story 3.2: Document Upload API Endpoint**
    * **As an** administrator, **I want** a secure API endpoint to upload document files, **so that** the system can create a record and schedule it for processing.
    * **Acceptance Criteria:**
        1.  A protected `/api/admin/upload` endpoint is created that requires 'admin' role authentication.
        2.  The endpoint accepts a file upload and associated metadata.
        3.  Upon receiving a file, the endpoint creates a new record in the `documents` table with a status of `queued`.
        4.  A new background job is dispatched to the Celery/Redis queue.
        5.  The endpoint immediately returns a success response with the ID of the new document record.

* **Story 3.3: Frontend Upload Component**
    * **As an** administrator, **I want** a clear and intuitive drag-and-drop interface, **so that** I can easily select and upload document files.
    * **Acceptance Criteria:**
        1.  A new file upload component is created in the React admin dashboard.
        2.  The component provides a drag-and-drop zone and a traditional file selection button.
        3.  The component validates the selected file on the client-side (type and size).
        4.  The component includes a dropdown menu for the admin to categorize the document.
        5.  On submission, the component sends the file and its metadata to the `/api/admin/upload` endpoint.

* **Story 3.4: Real-time Job Status Connection**
    * **As an** administrator, **I want** to receive real-time status updates after uploading a file, **so that** I have immediate confirmation that the processing job has been successfully queued.
    * **Acceptance Criteria:**
        1.  A backend Server-Sent Events (SSE) endpoint is created that requires 'admin' role authentication.
        2.  After a successful upload, the frontend connects to this SSE endpoint.
        3.  The backend is able to push an initial status update (e.g., `{"status": "queued"}`) to the connected client.
        4.  The frontend displays this initial status in a user-friendly way.

---
#### **Epic 4: PocketFlow Processing Pipeline**
**Expanded Goal:** The goal of this epic is to build the core data processing engine. This involves creating a PocketFlow pipeline that activates when a new job appears in the queue to handle chunking, embedding, and storing of document content.

* **Story 4.1: The 'File Loader' Node**
    * **As a** developer, **I want** a PocketFlow `Node` that retrieves an uploaded file's content from storage, **so that** the processing pipeline can begin.
    * **Acceptance Criteria:**
        1.  A `FileLoaderNode` is created that accepts a `document_id`.
        2.  The node retrieves the file's path and metadata from the SQLite database.
        3.  It successfully reads the content of the specified file.
        4.  It places the raw text content into the PocketFlow `Shared Store`.
        5.  It updates the document's status in the SQLite database to `processing`.

* **Story 4.2: The 'Document Chunker' Node**
    * **As a** developer, **I want** a PocketFlow `Node` that chunks document content according to its type, **so that** the text is properly prepared for the embedding model.
    * **Acceptance Criteria:**
        1.  A `DocumentChunkerNode` is created.
        2.  For `biblical` documents, it chunks the text into groups of 5 verses with a 1-verse overlap, preserving citation metadata.
        3.  For `theological` documents, it chunks the text into 1000-character segments with a 200-character overlap.
        4.  The node outputs a list of all text chunks into the `Shared Store`.

* **Story 4.3: The 'Embedding Generator' Node**
    * **As a** developer, **I want** a PocketFlow `Node` that generates vector embeddings for text chunks using OpenAI, **so that** they can be used for semantic search.
    * **Acceptance Criteria:**
        1.  An `EmbeddingGeneratorNode` is created.
        2.  It successfully calls the OpenAI API (`text-embedding-ada-002`) to get a vector embedding for each chunk.
        3.  The node gracefully handles potential API errors or rate limits.
        4.  It outputs the list of chunks, now paired with their corresponding vector embeddings, back into the `Shared Store`.

* **Story 4.4: The 'Supabase Storage' Node**
    * **As a** developer, **I want** a PocketFlow `Node` that stores text chunks and their embeddings in our Supabase vector database, **so that** the data becomes queryable.
    * **Acceptance Criteria:**
        1.  A `SupabaseStorageNode` is created.
        2.  It successfully connects to the Supabase database.
        3.  It inserts each chunk's content, its vector embedding, and all its associated metadata into the correct table.
        4.  Upon successful completion, it updates the document's status in the SQLite database to `completed`.

* **Story 4.5: The Document Processing Flow**
    * **As a** developer, **I want** a main PocketFlow `Flow` that orchestrates the entire document ingestion pipeline, **so that** a job from the queue is processed automatically.
    * **Acceptance Criteria:**
        1.  A `DocumentProcessingFlow` is created that connects all the ingestion `Nodes` in the correct sequence.
        2.  The Celery task is updated to execute this main `Flow`.
        3.  The flow includes robust error handling: if any node fails, the document's status is updated to `failed` and the error is logged.

---
#### **Epic 5: MVP Administrative Dashboard**
**Expanded Goal:** The goal of this epic is to provide administrators with the essential tools to manage the application, including the user approval workflow and document management.

**Dependencies:** This epic depends on the completion of Epic 4 (Processing Pipeline) to display accurate document processing statuses in the admin dashboard.

* **Story 5.1: Admin Dashboard UI**
    * **As an** administrator, **I want** to see a dashboard with key system statistics, **so that** I can quickly understand the current state of the application.
    * **Acceptance Criteria:**
        1.  A protected `/admin/dashboard` route is created, accessible only to admins.
        2.  The dashboard UI calls new backend endpoints to fetch and display key metrics.
        3.  The UI presents this information in a clear and easily scannable format.
        4.  The page includes the main application navigation.

* **Story 5.2: User Management Page**
    * **As an** administrator, **I want** a page to view and manage pending user registrations, **so that** I can grant or deny access.
    * **Acceptance Criteria:**
        1.  A protected `/admin/users` route is created.
        2.  The page displays a list of all users with a status of `pending`.
        3.  Each user in the list has an "Approve" and a "Deny" button.
        4.  Clicking "Approve" calls a backend API to update the user's status to `approved`.
        5.  Clicking "Deny" calls a backend API to delete the user record.
        6.  The list in the UI updates automatically.

* **Story 5.3: Document Management Page**
    * **As an** administrator, **I want** a page to view and manage all uploaded documents, **so that** I can monitor their status and remove content.
    * **Acceptance Criteria:**
        1.  A protected `/admin/documents` route is created.
        2.  The page displays a paginated list of all documents from the backend.
        3.  The list displays filename, document type, upload date, and processing status.
        4.  If a document's status is `failed`, the error message is visible.
        5.  Each document in the list has a "Delete" button with a confirmation modal.
        6.  Upon confirmation, the backend deletes the document record and its associated data from Supabase.

---
#### **Epic 6: Core Chat UI & Basic RAG**
**Expanded Goal:** The goal of this epic is to deliver a working chat interface that can answer user questions based on the ingested documents by connecting the UI to a simplified RAG pipeline.

* **Story 6.1: Basic RAG Pipeline Backend**
    * **As a** developer, **I want** a basic PocketFlow `Flow` that can take a user's query, find relevant chunks, and generate a simple answer, **so that** we have a functional RAG engine.
    * **Acceptance Criteria:**
        1.  A new, protected `/api/chat` endpoint is created.
        2.  A `BasicRAGFlow` is created using PocketFlow.
        3.  The flow includes a `QueryEmbedderNode`, a `SupabaseSearchNode`, and a `SimpleGeneratorNode`.
        4.  The final API response includes the generated answer and a list of the source document chunks.

* **Story 6.2: Frontend Chat Interface**
    * **As a** user, **I want** a clean and intuitive chat interface, **so that** I can easily ask questions and view the AI's responses.
    * **Acceptance Criteria:**
        1.  A protected `/chat` route and page is created.
        2.  The UI includes a message display area and a text input form.
        3.  The UI clearly distinguishes between user messages and AI responses.
        4.  A loading indicator is displayed while the AI is processing.

* **Story 6.3: Source Citation Display**
    * **As a** user, **I want** to see the sources the AI used, **so that** I can verify the information and trust the system's responses.
    * **Acceptance Criteria:**
        1.  A side panel is implemented in the chat interface.
        2.  After an AI response is received, this panel is populated with a list of the source document chunks.
        3.  Each source in the list displays its metadata (filename, version, citation).
        4.  The panel updates with new sources for each new AI response.

---
#### **Epic 7: Advanced RAG & Hermeneutics Engine**
**Expanded Goal:** The goal of this epic is to upgrade the basic RAG pipeline into the highly specialized, theologically-aligned engine, adding re-ranking and the Hermeneutics Filter.

* **Story 7.1: The 'Re-ranker' Node**
    * **As a** developer, **I want** to add a PocketFlow `Node` that re-ranks the initial search results for improved contextual relevance, **so that** the generator receives the best possible information.
    * **Acceptance Criteria:**
        1.  A new `ReRankerNode` is created in the backend.
        2.  The node takes the user's query and the initial list of document chunks.
        3.  It uses a secondary, more focused LLM call to re-score and re-order the chunks.
        4.  The node places the newly ordered, top-k chunks back into the `Shared Store`.

* **Story 7.2: The 'Hermeneutics Filter' Implementation**
    * **As a** theological expert, **I want** to implement a master system prompt with the core rules of hermeneutics, **so that** the AI's reasoning is consistently guided.
    * **Acceptance Criteria:**
        1.  A configuration file or database entry is created to store the hermeneutics system prompt.
        2.  The generator `Node` is upgraded to an `AdvancedGeneratorNode`.
        3.  This new node is required to prepend the hermeneutics system prompt to every call it makes to the OpenAI generation model.
        4.  The final prompt is structured as: `[Hermeneutics Rules] + [Re-ranked Context] + [User's Question]`.

* **Story 7.3: Advanced RAG Pipeline Integration**
    * **As a** developer, **I want** to update the main RAG `Flow` to include the new capabilities, **so that** the chat endpoint uses the advanced pipeline.
    * **Acceptance Criteria:**
        1.  The `BasicRAGFlow` is upgraded to an `AdvancedRAGFlow`.
        2.  The new `ReRankerNode` is correctly inserted into the flow's sequence.
        3.  The `SimpleGeneratorNode` is replaced with the `AdvancedGeneratorNode`.
        4.  The `/api/chat` endpoint is confirmed to be using this new, advanced flow.

* **Story 7.4: Hermeneutics Filter Validation**
    * **As a** project owner, **I want** to test the pipeline against an expert-curated "golden dataset," **so that** I can validate the effectiveness of the Hermeneutics Filter.
    * **Acceptance Criteria:**
        1.  The project expert will provide a small dataset of 10-15 questions and their ideal answers.
        2.  A test script will be created to run each of these questions through the `AdvancedRAGFlow`.
        3.  The script will log the AI's actual response for each question.
        4.  The project owner will review the results to qualitatively assess the filter's performance.

---
#### **Epic 8: MVP Output & Export System**
**Expanded Goal:** The goal of this epic is to build the user's content creation and export toolkit, focusing on conversational reformatting and exporting to Markdown and PDF.

* **Story 8.1: Intent Recognition for Formatting Commands**
    * **As a** developer, **I want** to enhance the chat API to recognize when a user's prompt is a formatting command versus a new question, **so that** the system can respond appropriately.
    * **Acceptance Criteria:**
        1.  The `/api/chat` endpoint logic is updated to include an "intent recognition" step.
        2.  This step classifies the user's input as either a `new_query` or a `format_request`.
        3.  If the intent is `format_request`, the system must skip the RAG search pipeline.
        4.  The recognized intent is passed to the next stage.

* **Story 8.2: Conversational Formatting Service**
    * **As a** user, **I want** the AI to reformat its previous answer based on my text commands, **so that** I can conversationally shape the output.
    * **Acceptance Criteria:**
        1.  A new `FormattingNode` or service is created in the backend.
        2.  The service accepts the *previous* AI-generated text and the user's *new* formatting command.
        3.  It uses a specialized LLM prompt to apply the user's command to the text.
        4.  The `/api/chat` endpoint, upon detecting a `format_request`, routes the request to this service.

* **Story 8.3: Frontend Editor Panel**
    * **As a** user, **I want** the AI's responses and my formatting changes to appear in the side editor panel, **so that** I can see my final document taking shape.
    * **Acceptance Criteria:**
        1.  The side panel in the React app is implemented with a text area.
        2.  When a response is received, its content is rendered in this panel.
        3.  When a `format_request` is sent, the content in the panel is updated with the new version.
        4.  The panel includes "Export as PDF" and "Export as Markdown" buttons.

* **Story 8.4: PDF & Markdown Export**
    * **As a** user, **I want** to export the content from the editor panel into PDF and Markdown files, **so that** I can use my refined answer in my own work.
    * **Acceptance Criteria:**
        1.  A new, protected `/api/export/pdf` endpoint is created on the backend that accepts Markdown and returns a PDF file.
        2.  Clicking the "Export as Markdown" button generates and downloads a `.md` file.
        3.  Clicking the "Export as PDF" button sends the panel's content to the `/api/export/pdf` endpoint and initiates a download.
