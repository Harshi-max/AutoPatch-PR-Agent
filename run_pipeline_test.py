import asyncio
import os
from agents.orchestrator import run_pipeline

repo='https://github.com/Harshi31-g/Voice_to_code_visualiser'
# token pulled from environment or hardcoded fallback
token=os.environ.get('GITHUB_TOKEN') 

async def main():
    try:
        await run_pipeline(repo, token, 'main')
    except Exception as e:
        print('PIPELINE ERROR:', e)

if __name__ == '__main__':
    asyncio.run(main())
