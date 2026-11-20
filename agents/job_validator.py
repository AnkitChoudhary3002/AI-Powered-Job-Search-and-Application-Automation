
import json
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent

INPUT_PATH = BASE_DIR / "outputs" / "enriched_jobs.json"
OUTPUT_PATH = BASE_DIR / "outputs" / "validated_jobs.json"

INVALID_URL_PATTERNS = [
    "/jobs-in-",
    "/job-search",
    "/jobs/",
    "/careers"
]


def validate_job(job):
    url = (job.get("apply_url") or "").lower()
    title = (job.get("job_title") or "").lower()
    company = job.get("company")

    if not url:
        return "rejected", "Missing application URL"

    if any(pattern in url for pattern in INVALID_URL_PATTERNS):
        return "rejected", "Likely a general jobs or careers page"

    if not company:
        return "manual_review", "Hiring company not identified"

    if not title:
        return "manual_review", "Job title missing"

    return "valid", "Passed basic validation"


def main():
    with open(INPUT_PATH, "r", encoding="utf-8") as file:
        jobs = json.load(file)

    validated_jobs = []

    for job in jobs:
        status, reason = validate_job(job)

        validated_jobs.append({
            **job,
            "validation_status": status,
            "validation_reason": reason
        })

        print(job.get("job_title"), "->", status)

    OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)

    with open(OUTPUT_PATH, "w", encoding="utf-8") as file:
        json.dump(validated_jobs, file, indent=4, ensure_ascii=False)

    valid_count = sum(
        job["validation_status"] == "valid"
        for job in validated_jobs
    )

    review_count = sum(
        job["validation_status"] == "manual_review"
        for job in validated_jobs
    )

    rejected_count = sum(
        job["validation_status"] == "rejected"
        for job in validated_jobs
    )

    print("\nValidation completed.")
    print("Total jobs:", len(validated_jobs))
    print("Valid:", valid_count)
    print("Manual review:", review_count)
    print("Rejected:", rejected_count)
    print("Saved to:", OUTPUT_PATH)


if __name__ == "__main__":
    main()
