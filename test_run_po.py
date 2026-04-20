import asyncio
from harnesscore.config.loader import load_config
from harnesscore.schema import SystemState
from harnesscore.agents.po import po_node

def main():
    config = load_config()
    state = SystemState(user_prompt="Create a simple fizzbuzz script in Python using best practices.")
    print("Testing PO Node directly...")
    try:
        res = po_node(state, config)
        print("PO Node Result:", res)
    except Exception as e:
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()
