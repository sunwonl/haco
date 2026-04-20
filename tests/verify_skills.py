import sys
from pathlib import Path
from unittest.mock import MagicMock

# Add src to path
sys.path.append(str(Path(__file__).parent.parent / "src"))

from harnesscore.agents.base import run_agent_react_loop
from harnesscore.schema import SystemState

def test_skills_injection():
    # Mock LLM and Tools
    mock_llm = MagicMock()
    mock_llm.bind_tools.return_value = mock_llm
    
    # Define a custom tool that immediately submit work to break the loop
    def submit_work(message: str):
        pass
    
    # Mock response that calls submit_work
    mock_response = MagicMock()
    mock_response.tool_calls = [{"name": "submit_work", "args": {"message": "done"}, "id": "1"}]
    mock_response.content = ""
    mock_llm.invoke.return_value = mock_response
    
    state = SystemState(user_prompt="Verify Skills")
    harness_dir = Path(__file__).parent.parent / ".harness"
    
    # Ensure dir exists
    (harness_dir / "skills").mkdir(parents=True, exist_ok=True)
    (harness_dir / "skills" / "global.md").write_text("# Global Skill\nAlways be polite.")
    (harness_dir / "skills" / "core_developer.md").write_text("# CD Skill\nIndent with 4 spaces.")
    
    print("\n--- Running Skills Injection Test ---")
    
    # We want to capture the messages sent to LLM
    def side_effect(messages):
        # The messages[1] is the HumanMessage which contains context_str
        human_msg = messages[1].content
        print(f"Captured HumanMessage length: {len(human_msg)}")
        assert "--- 🛠️ ACTIVE SKILLS & PROTOCOLS ---" in human_msg
        assert "### SKILL: GLOBAL" in human_msg
        assert "### SKILL: CORE_DEVELOPER" in human_msg
        assert "Always be polite." in human_msg
        assert "Indent with 4 spaces." in human_msg
        print("✅ Skills successfully found in prompt context!")
        return mock_response

    mock_llm.invoke.side_effect = side_effect
    
    try:
        run_agent_react_loop(
            agent_name="Core Developer",
            state=state,
            llm=mock_llm,
            tools=[submit_work],
            sys_prompt="You are a dev.",
            context_str="Start work.",
            harness_dir=harness_dir,
            max_loops=1
        )
    except Exception as e:
        print(f"Loop ended: {e}")

if __name__ == "__main__":
    test_skills_injection()
