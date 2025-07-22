# UI/UX Specification: Theo

### **Introduction**
This document defines the user experience goals, information architecture, user flows, and visual design specifications for the "Theo" application. It serves as the foundation for visual design and frontend development, ensuring a cohesive and user-centered experience.

### **Overall UX Goals & Principles**
* **Target User Personas:**
    * **The Administrator:** A detail-oriented user responsible for managing the system's corpus and user base. They require an efficient, data-rich interface.
    * **The Researcher (User):** A knowledge-seeking user who needs to trust the information provided. They require a simple, focused interface.
* **Usability Goals:**
    * **Efficiency (for Admins):** Core management tasks should be accomplishable in the fewest possible steps.
    * **Trust (for Users):** Every AI-generated answer must be transparently linked to its source material.
    * **Clarity:** The interface must be unambiguous.
    * **Low Cognitive Load:** The interface should present information progressively.
* **Design Principles:**
    1.  **Clarity Over Cleverness:** Prioritize clear communication.
    2.  **Role-Focused Design:** Admin and User interfaces will be distinctly tailored.
    3.  **Trust Through Transparency:** The system will always show its work.
    4.  **Progressive Disclosure:** Start simple and reveal advanced features contextually.

### **Information Architecture (IA)**
#### **Site Map / Screen Inventory**
```mermaid
graph TD
    subgraph Public Area; A[Login / Register Page]; end
    subgraph Admin Section; B[Admin Dashboard]; C[Document Management]; D[User Management]; E[Account Settings]; end
    subgraph Researcher Section; F[Chat Interface]; G[Account Settings]; end
    A -- Admin Login --> B; A -- Researcher Login --> F;
    B --- C; B --- D; B --- E;
    Admin_Section_Nav --> F; F --- G;
    style Admin_Section_Nav stroke-width:0px, fill:none;
    linkStyle 9 stroke:red,stroke-width:2px,fill:none,stroke-dasharray: 3 3;
