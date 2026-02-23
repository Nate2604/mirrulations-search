# Frontend Tech Stack

## Overview

The frontend will be built using React and JavaScript, styled with Tailwind CSS, and integrated with the existing Flask backend served by Gunicorn. This stack aligns with the current project architecture while allowing flexibility for future backend changes (e.g., FastAPI).

---

## Frontend

### Language: JavaScript

We will use JavaScript as the primary frontend language.

* Matches the current project structure
* No TypeScript overhead for a small team
* Faster onboarding for contributors

### Framework: React

We will use React for building the user interface.

* Component-based architecture for modular UI
* Works well with API-driven backend
* Scales as the application grows

### Styling: Vanilla CSS

We will use standard (vanilla) CSS for styling instead of a CSS framework.

* Simplest approach with no additional dependencies
* Easy for all team members to understand and maintain
* Full control over styles and class naming
* Appropriate for current project size and UI complexity

This keeps the frontend lightweight and avoids introducing extra tooling while the UI remains relatively simple.

### State Management

We will use React built-in state and Context API.

* Sufficient for current app complexity
* Avoids heavier libraries (e.g., Redux)
* Simple global state (auth, session, theme)

---

## Backend Integration

### Current Backend: Flask + Gunicorn

The frontend will communicate with the existing Flask backend via REST APIs.

* Already implemented in the project
* Stable and well-understood by the team
* Gunicorn provides a production WSGI server

### Possible Future Backend: FastAPI

We may evaluate migration to FastAPI later (as suggested by the team).

Potential benefits:

* Faster async request handling
* Automatic API documentation (Swagger/OpenAPI)
* Better performance at scale

This change would not require major frontend changes because both Flask and FastAPI expose REST APIs.

---

### Deployment Model

Current approach:

* Flask served by Gunicorn
* Frontend served as static assets by Flask
* Single deployment unit (same server)

