# Technical Assumptions

* **Repository Structure:** Monorepo.
* **Service Architecture:** Monolith with PocketFlow Pattern.
* **Testing Requirements:** Unit + Integration.
* **Standardized PDF Pre-processing:** For the MVP, it is assumed that all uploaded PDF documents will be pre-processed by the administrator.
* **Additional Technical Assumptions and Requests:**
    * **Backend Stack:** Python, FastAPI, SQLite, Supabase (Postgres w/ pgvector), JWT, bcrypt, SSE, OpenAI API, Celery/Redis.
    * **Frontend Stack:** React, Vite, TypeScript, TailwindCSS, React Router.