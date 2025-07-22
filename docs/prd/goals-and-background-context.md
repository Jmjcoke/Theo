# Goals and Background Context

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