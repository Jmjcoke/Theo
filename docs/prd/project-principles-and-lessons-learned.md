# Project Principles & Lessons Learned

## Trap #1: Inconsistent Development & Deployment Environments
* **Problem:** The previous version was developed simultaneously on a local machine and in a live production VM, leading to a chaotic, unrepeatable, and error-prone workflow.
* **Principle to Enforce:** **Local-First, Automated Deployment.**
* **Implementation:** 1) All features must be built and tested locally first. 2) The project will use Git and a central repository. 3) We will create a simple, automated deployment pipeline.

## Trap #2: Inconsistent Naming and Terminology
* **Problem:** The previous version used inconsistent names for the same concepts (e.g., "biblical" vs. "Bible").
* **Principle to Enforce:** **Standardized Terminology and Naming Conventions.**
* **Implementation:** 1) This PRD contains a glossary defining official terms. 2) The `architect` agent will produce a "Naming Convention" document.

## Trap #3: Architectural Drift and "Massive Node" Violation
* **Problem:** The previous version violated the PocketFlow philosophy, with nodes growing into massive monoliths.
* **Principle to Enforce:** **Strict Adherence to the PocketFlow Philosophy.**
* **Implementation:** 1) Every `Node` must have a single responsibility. 2) A `Node` **must not** exceed 150 lines of code. 3) Nodes must be stateless. 4) Nodes will be asynchronous.

## Trap #4: Disconnected and Opaque Architecture
* **Problem:** The previous version suffered from confusing authentication, a chaotic folder structure, a brittle upload system, and Supabase misconfiguration.
* **Principle to Enforce:** **A Clear, Documented, and Observable Architecture.**
* **Implementation:** 1) The architect **must** create a detailed Authentication Flow Diagram. 2) The architecture **must** include a Source Tree diagram. 3) The architecture **must** define a robust background job pipeline. 4) The database schema **must** be defined first, and the architecture must include a plan for structured logging.

## Trap #5: Outdated AI Knowledge and Dependency Hell
* **Problem:** The development AI often generated code based on outdated documentation or older versions of libraries.
* **Principle to Enforce:** **Proactive Dependency Management and Pattern Definition.**
* **Implementation:** 1) The `architect` is **required** to define the **exact version number** for every package. 2) The architecture **must** include a "Cookbook" with tested code snippets for critical libraries. 3) The `dev` agent is **required** to use only the pinned versions and patterns.