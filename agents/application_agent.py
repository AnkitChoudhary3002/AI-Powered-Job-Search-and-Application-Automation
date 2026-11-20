
import os
import json

from pathlib import Path
from dotenv import load_dotenv
from openai import OpenAI

from application_tracker import can_apply, record_application

load_dotenv()

BASE_DIR = Path(__file__).resolve().parent.parent
OUTPUT_DIR = BASE_DIR / "outputs"

JOBS_PATH = OUTPUT_DIR / "enriched_jobs.json"
PROFILE_PATH = OUTPUT_DIR / "candidate_summary.json"
QUEUE_PATH = OUTPUT_DIR / "application_queue.json"

client = OpenAI(
    base_url="https://openrouter.ai/api/v1",
    api_key=os.getenv("OPENROUTER_API_KEY")
)

MODEL = os.getenv("OPENROUTER_MODEL", "openrouter/free")


def load_json(path):
    with open(path, "r", encoding="utf-8") as file:
        return json.load(file)


def evaluate_job(job, candidate):
    prompt = f"""
Evaluate this job against the candidate profile.

Candidate:
{json.dumps(candidate, ensure_ascii=False)}

Job:
{json.dumps(job, ensure_ascii=False)}

Return only valid JSON with these keys:
{{
    "fit_score": 0,
    "decision": "apply or skip",
    "matching_skills": [],
    "missing_skills": [],
    "reason": "",
    "cover_letter": ""
}}

Rules:
- Be honest. Do not invent candidate experience.
- Consider education, skills, projects and experience.
- A high score must reflect genuine alignment.
- Keep the cover letter concise and job-specific.
- Do not include private contact details.
"""

    response = client.chat.completions.create(
        model=MODEL,
        messages=[
            {
                "role": "user",
                "content": prompt
            }
        ],
        temperature=0.2
    )

    content = response.choices[0].message.content

    if not content:
        raise ValueError("Model returned empty response.")

    content = content.strip()

    if content.startswith("```"):
        content = content.split("\n", 1)[1]
        content = content.rsplit("```", 1)[0]

    return json.loads(content)


def main():
    if not os.getenv("OPENROUTER_API_KEY"):
        raise ValueError("OPENROUTER_API_KEY missing from .env")

    jobs = load_json(JOBS_PATH)
    candidate = load_json(PROFILE_PATH)

    application_queue = []

    for index, job in enumerate(jobs, start=1):
        company = job.get("company")
        title = job.get("job_title")

        print(f"\n[{index}/{len(jobs)}] Evaluating: {title}")

        if not company:
            print("Skipped: Company name unavailable.")
            continue

        if not can_apply(company):
            print(f"Skipped: {company} is in the 7-day cooldown.")
            continue

        try:
            evaluation = evaluate_job(job, candidate)
        except Exception as error:
            print(f"Evaluation failed: {error}")
            continue

        if evaluation.get("decision", "").lower() != "apply":
            print("Skipped: Job is not a suitable match.")
            continue

        application = {
            "company": company,
            "job_title": title,
            "apply_url": job.get("apply_url"),
            "fit_score": evaluation.get("fit_score"),
            "matching_skills": evaluation.get("matching_skills", []),
            "missing_skills": evaluation.get("missing_skills", []),
            "reason": evaluation.get("reason"),
            "cover_letter": evaluation.get("cover_letter"),
            "status": "awaiting_approval"
        }

        application_queue.append(application)

        print("Fit score:", application["fit_score"])
        print("Reason:", application["reason"])

    QUEUE_PATH.parent.mkdir(parents=True, exist_ok=True)

    with open(QUEUE_PATH, "w", encoding="utf-8") as file:
        json.dump(
            application_queue,
            file,
            indent=4,
            ensure_ascii=False
        )

    print("\nApplication preparation completed.")
    print("Eligible applications:", len(application_queue))
    print("Saved to:", QUEUE_PATH)

    for application in application_queue:
        print("\n--------------------------------")
        print(application["company"])
        print(application["job_title"])
        print("Fit:", application["fit_score"])
        print("Apply URL:", application["apply_url"])

        print("\nDo you want to open this job for manual application?")
        approval = input("Open? (y/n): ").strip().lower()

        if approval != "y":
            continue

        import webbrowser
        webbrowser.open(application["apply_url"])

        submitted = input(
            "Did you successfully submit this application? (y/n): "
        ).strip().lower()

        if submitted == "y":
            record_application(
                application["company"],
                application["job_title"],
                application["apply_url"]
            )
            application["status"] = "submitted"
            print("Application recorded.")
        else:
            application["status"] = "not_submitted"
            print("Application not recorded.")

        with open(QUEUE_PATH, "w", encoding="utf-8") as file:
            json.dump(
                application_queue,
                file,
                indent=4,
                ensure_ascii=False
            )


if __name__ == "__main__":
    main()
