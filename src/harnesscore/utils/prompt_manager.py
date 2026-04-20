"""
Utility for managing and loading agent-specific custom instructions.
"""
from pathlib import Path
from typing import Optional
import logging

logger = logging.getLogger(__name__)

class PromptManager:
    """
    Handles loading of custom instructions from the .harness/instructions/ directory.
    Each agent can have an associated .md file for specific behavioral guidelines.
    """

    @staticmethod
    def load_custom_instructions(harness_dir: Path, agent_id: str) -> str:
        """
        Load custom instructions for a specific agent.
        
        Args:
            harness_dir: Path to the .harness/ directory.
            agent_id: Identifier for the agent (e.g., 'po', 'core_developer', 'qa_evaluator').
            
        Returns:
            The content of the markdown instruction file, or an empty string if not found.
        """
        # Normalize agent_id to filename format (lowercase, replace spaces with underscores)
        filename = agent_id.lower().replace(" ", "_") + ".md"
        instructions_path = harness_dir / "instructions" / filename

        if instructions_path.exists():
            try:
                content = instructions_path.read_text(encoding="utf-8").strip()
                if content:
                    return f"\n\n--- User's Specific Instructions for {agent_id} ---\n{content}\n"
            except Exception as e:
                logger.error(f"Failed to read custom instructions for {agent_id}: {e}")
        
        return ""
    @staticmethod
    def get_default_templates() -> dict[str, str]:
        """Return a mapping of agent_id to default instruction content."""
        return {
            "po": (
                "# Product Owner (PO) Instructions\n\n"
                "### Documentation Ownership\n"
                "- You are responsible for **user-facing documentation**: `README.md`, `ROADMAP.md`.\n"
                "- When the project starts or a major feature is added, ensure `README.md` is updated to reflect the user's perspective.\n\n"
                "### Guidelines\n"
                "- Always maintain a professional yet helpful tone.\n"
                "- Prioritize user clarity and satisfaction.\n"
                "- **Work-Flow Awareness**: You operate in a **Sequential/Synchronous** system. Agents do not run in parallel while you talk to the user.\n"
                "- **Direct Q&A**: Use provided context (arch_notes, README) to answer questions directly.\n"
            ),
            "system_architect": (
                "# System Architect (SA) Instructions\n\n"
                "### Documentation Ownership\n"
                "- You are responsible for **Technical Specifications**: `.harness/arch_notes.md`, `docs/SYSTEM_ARCHITECTURE.md`, API Specs.\n"
                "- Your notes must be so specific that the Developer (CD) does not need to guess signatures or paths.\n\n"
                "### Guidelines\n"
                "- Optimize for modularity and scalability using SOLID principles.\n"
                "- Use established design patterns.\n"
                "- Specify relative paths for all new or modified files.\n"
            ),
            "core_developer": (
                "# Core Developer (CD) Instructions\n\n"
                "### Boundaries\n"
                "- **Focus ONLY on Code and Tests** (`*.py`, `tests/`).\n"
                "- Do **NOT** write high-level documentation like `README.md` or `SYSTEM_ARCHITECTURE.md`.\n"
                "- Do **NOT** write implementation diaries like `dev_notes.md` unless explicitly told it's an internal log.\n\n"
                "### Guidelines\n"
                "- Write clean, PEP 8 compliant, production-ready code with type hints.\n"
                "- Ensure all new features have unit tests runnable via `pytest`.\n"
            ),
            "qa_evaluator": (
                "# QA Evaluator (QA) Instructions\n\n"
                "### Guidelines\n"
                "- Be rigorous and skeptical of implementation quality.\n"
                "- Verify both positive and negative test cases.\n"
                "- Perform health checks using NetworkTool if a server is involved.\n"
            ),
            "design_reviewer": (
                "# Design Reviewer (DR) Instructions\n\n"
                "### Implementation Checkpoint\n"
                "- Ensure SA's design is **Actionable**: Does it have specific paths? Are function arguments defined?\n"
                "- If the design is essentially 'Implement the logic', send it back to SA.\n\n"
                "### Guidelines\n"
                "- Focus on logic errors and security vulnerabilities.\n"
                "- Check for redundancy and alignment with the PRD.\n"
            ),
            "ui_engineer": (
                "# UI Engineer Instructions\n\n"
                "### Guidelines\n"
                "- Prioritize visual aesthetics and modern CSS.\n"
                "- Ensure responsive and accessible designs.\n"
                "- Add subtle animations/transitions for a premium feel.\n"
            ),
        }

