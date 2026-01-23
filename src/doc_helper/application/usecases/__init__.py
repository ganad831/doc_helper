"""Application Use Cases.

Use-case classes provide a clean boundary between Presentation and Application layers.
Presentation layer injects use-case classes and calls their methods with primitives/DTOs.
All domain type construction and command/query orchestration happens in use-cases.

RULE 0 ENFORCEMENT (MANDATORY):
- Presentation MUST NOT import commands, queries, or facades
- Presentation MUST NOT instantiate commands, queries, or facades
- Presentation MUST NOT access repositories (directly or via reach-through)
- Presentation MUST ONLY call use-case methods

Available Use Cases:
- DocumentUseCases: Document generation operations (generate Word/Excel/PDF)
- ProjectUseCases: ALL project operations (get, save, export, import, search, history)
- SchemaUseCases: All schema designer operations (create entity, add field, export, etc.)
- WelcomeUseCases: Welcome screen operations (create project, recent projects)
"""

from doc_helper.application.usecases.document_usecases import DocumentUseCases
from doc_helper.application.usecases.project_usecases import ProjectUseCases
from doc_helper.application.usecases.schema_usecases import SchemaUseCases
from doc_helper.application.usecases.welcome_usecases import WelcomeUseCases

__all__ = [
    "DocumentUseCases",
    "ProjectUseCases",
    "SchemaUseCases",
    "WelcomeUseCases",
]
