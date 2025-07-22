# High Level Architecture

* **Technical Summary:** A fullstack monorepo application using a React/Vite frontend and a FastAPI/Python backend, deployed on DigitalOcean. The backend uses the modular PocketFlow pattern for AI workflows, leveraging Supabase for its vector database and Celery/Redis for background jobs.
* **Platform and Infrastructure Choice:** DigitalOcean (Droplets, Managed Redis, Spaces).
* **Repository Structure:** Monorepo using `npm workspaces`.
* **High Level Architecture Diagram:**
```mermaid
graph TD
    subgraph User Browser; A[React Frontend]; end
    subgraph DigitalOcean; B[FastAPI Backend]; C[Celery Worker]; D[Redis Queue]; E[SQLite Database]; F[File Storage (Spaces)]; end
    subgraph External Services; G[OpenAI API]; H[Supabase (Vector DB)]; end
    A -- REST API --> B; B -- Queues Job --> D; C -- Takes Job --> D; B -- Stores/Reads Metadata --> E; B -- Stores File --> F; C -- Reads File --> F; C -- Generates Embeddings --> G; C -- Generates Text --> G; C -- Stores/Queries Vectors --> H;
```