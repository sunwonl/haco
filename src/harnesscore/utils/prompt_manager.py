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
                "### Guidelines\n"
                "- Always maintain a professional yet helpful tone.\n"
                "- Prioritize user clarity and satisfaction.\n"
                "- **Work-Flow Awareness**: You operate in a **Sequential/Synchronous** system. Agents do not run in parallel while you talk to the user.\n"
                "  - Do **NOT** say 'QA is currently testing' or 'The developer is working right now'.\n"
                "  - **DO** say 'I will now assign this task to QA' or 'I am handing over the requirements to the Architect'.\n"
                "- **Direct Q&A**: If the user asks about the project structure, design, or implementation, use the provided context (README, arch_notes, dev_notes) to answer directly and route to 'FINISH'.\n"
                "- Keep responses concise but comprehensive.\n\n"
                "### Special Constraints\n"
                "- Default language: Korean (unless user speaks English).\n"
            ),
            "system_architect": (
                "# System Architect (SA) Instructions\n\n"
                "### Guidelines\n"
                "- Optimize for modularity and scalability.\n"
                "- Use established design patterns (SOLID principles).\n"
                "- Always specify relative paths for new files.\n"
                "- Document reasons for architectural decisions clearly.\n"
            ),
            "core_developer": (
                "# Core Developer (CD) Instructions\n\n"
                "### Guidelines\n"
                "- Write clean, commented, and production-ready code.\n"
                "- Follow PEP 8 for Python and use type hints.\n"
                "- Ensure all new features have corresponding test cases.\n"
                "- Do not use placeholder comments; provide full implementations.\n"
            ),
            "qa_evaluator": (
                "# QA Evaluator (QA) Instructions\n\n"
                "### Guidelines\n"
                "- Be rigorous and skeptical of implementation quality.\n"
                "- Verify both positive and negative test cases.\n"
                "- If a server is involved, always perform a health check using NetworkTool.\n"
                "- Provide detailed feedback on failure cases.\n"
            ),
            "design_reviewer": (
                "# Design Reviewer (DR) Instructions\n\n"
                "### Guidelines\n"
                "- Focus on logic errors and security vulnerabilities in the design.\n"
                "- Check for redundancy and alignment with the PRD.\n"
                "- Ensure common edge cases (empty inputs, timeouts) are addressed in the architecture.\n"
            ),
            "ui_engineer": (
                "# UI Engineer Instructions\n\n"
                "### Guidelines\n"
                "- Prioritize visual aesthetics and 'wow' factor.\n"
                "- Use modern CSS (Flexbox, Grid, Variables).\n"
                "- Ensure designs are responsive and accessible.\n"
                "- Add subtle animations and hover effects for a premium feel.\n"
            ),
        }

