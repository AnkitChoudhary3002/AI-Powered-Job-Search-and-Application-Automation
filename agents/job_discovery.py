
import os
import json
import requests

from pathlib import Path
from datetime import datetime, timezone
from dotenv import load_dotenv

load_dotenv()

BASE_DIR = Path(__file__).resolve().parent.parent
OUTPUT_PATH = BASE_DIR / "outputs" / "jobs.json"

API_KEY = os.getenv("SERPER_API_KEY")

SEARCH_QUERIES = [
    'site:linkedin.com/jobs/view Data Scientist India',
    'site:linkedin.com/jobs/view Machine Learning Engineer India',
    'site:linkedin.com/jobs/view AI Engineer India',
    'site:linkedin.com/jobs/view Python Developer India',
    'site:linkedin.com/jobs/view Data Science Intern India',
    'site:linkedin.com/jobs/view Machine Learning Intern "6 months" India',
    'Data Scientist OR Machine Learning Engineer remote India careers',
    'AI Engineer OR Python Developer jobs India company careers'
]


def search_google(query):
    url = "https://google.serper.dev/search"

    headers = {
        "X-API-KEY": API_KEY,
        "Content-Type": "application/json"
    }

    payload = {
    "q": query,
    "gl": "in",
    "hl": "en",
    "num": 10,
    "tbs": "qdr:d"
    }

    response = requests.post(
        url,
        headers=headers,
        json=payload,
        timeout=30
    )

    response.raise_for_status()

    return response.json().get("organic", [])


def discover_jobs():
    if not API_KEY:
        raise ValueError("SERPER_API_KEY missing from .env")

    jobs = []
    seen_urls = set()

    for query in SEARCH_QUERIES:
        print(f"\nSearching: {query}")

        results = search_google(query)

        for item in results:
            job_url = item.get("link")

            if not job_url or job_url in seen_urls:
                continue

            seen_urls.add(job_url)

            jobs.append({
                "job_title": item.get("title"),
                "company": None,
                "location": None,
                "description": item.get("snippet"),
                "apply_url": job_url,
                "source": "Google Search",
                "search_query": query,
                "employment_type": None,
                "internship_duration_months": None,
                "posted_date": item.get("date"),
                "recency_filter": "past_24_hours",
                "discovered_at": datetime.now(
                    timezone.utc
                ).isoformat(),
                "status": "needs_review"
            })

        print(f"Results collected: {len(results)}")

    return jobs


def main():
    jobs = discover_jobs()

    OUTPUT_PATH.parent.mkdir(
        parents=True,
        exist_ok=True
    )

    with open(OUTPUT_PATH, "w", encoding="utf-8") as file:
        json.dump(jobs, file, indent=4, ensure_ascii=False)

    print("\nJob discovery completed.")
    print("Total unique listings:", len(jobs))
    print("Saved to:", OUTPUT_PATH)


if __name__ == "__main__":
    main()
