import subprocess
import sys
from pathlib import Path


BASE_DIR = Path(__file__).resolve().parent

WORKFLOW = [
    "agents/candidate_profiler.py",
    "agents/job_discovery.py",
    "agents/job_enrichment.py",
    "agents/job_validator.py",
    "agents/application_agent.py",
]


def main():
    for index, script in enumerate(WORKFLOW, start=1):
        print(f"\n[{index}/{len(WORKFLOW)}] Running {script}")

        result = subprocess.run(
            [sys.executable, script],
            cwd=BASE_DIR,
        )

        if result.returncode != 0:
            raise SystemExit(
                f"Workflow stopped: {script} exited with "
                f"code {result.returncode}"
            )

    print("\nWorkflow completed successfully.")


if __name__ == "__main__":
    main()
