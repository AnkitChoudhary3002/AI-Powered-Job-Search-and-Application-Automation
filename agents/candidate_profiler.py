
import json
from pathlib import Path

import yaml
from dotenv import load_dotenv
from openai import OpenAI

load_dotenv()

BASE_DIR = Path(__file__).resolve().parent.parent
PROFILE_PATH = BASE_DIR / "candidate" / "candidate_profile.yaml"
OUTPUT_PATH = BASE_DIR / "outputs" / "candidate_summary.json"

client = OpenAI(
    base_url="https://openrouter.ai/api/v1",
    api_key=__import__("os").getenv("OPENROUTER_API_KEY")
)


def load_profile():
    with open(PROFILE_PATH, "r", encoding="utf-8") as file:
        profile = yaml.safe_load(file)

    # Do not send personal contact information to the API.
    profile["candidate"].pop("contact", None)

    return profile


def profile_candidate(profile):
 
    prompt = f"""
You are a candidate profiling assistant.

Analyze the supplied candidate profile.

Rules:
- Use only facts present in the supplied profile.
- Never invent experience, skills, or metrics.
- Treat 65% as confirmed DNA test-set accuracy.
- Do not count DNA internship and project as separate experiences.
- Salary expectation is flexible / negotiable.
- Contact details are intentionally excluded for privacy.
- LinkedIn and GitHub URLs are provided but pending verification.
- Do not assume a student is ineligible for full-time employment.

Return valid JSON only:

{{
    "candidate_name": "",
    "professional_summary": "",
    "education": [],
    "technical_strengths": [],
    "experience_summary": [],
    "project_strengths": [],
    "target_roles": [],
    "role_alignment": [],
    "missing_information": [],
    "profile_warnings": []
}}

Candidate profile:
{json.dumps(profile, indent=2)}
"""

    response = client.chat.completions.create(
        model="openrouter/free",
        messages=[
            {"role": "user", "content": prompt}
        ]
    )

    message = response.choices[0].message

    print("Finish reason:", response.choices[0].finish_reason)
    print("Message:", message)

    if not message.content:
        raise ValueError("OpenRouter returned no text content.")

    result = message.content.strip()

    # Remove optional Markdown code fences.
    if result.startswith("```"):
        result = result.split("\n", 1)[1].rsplit("```", 1)[0]

    print("RAW RESPONSE:")
    print(result)

    return json.loads(result)

def main():
    profile = load_profile()
    summary = profile_candidate(profile)

    OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)

    with open(OUTPUT_PATH, "w", encoding="utf-8") as file:
        json.dump(summary, file, indent=4, ensure_ascii=False)

    print("Candidate Profiling Agent completed.")
    print("Candidate:", summary["candidate_name"])
    print("Summary saved to:", OUTPUT_PATH)


if __name__ == "__main__":
    main()
