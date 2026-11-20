
import json
import re
import requests

from pathlib import Path
from bs4 import BeautifulSoup

BASE_DIR = Path(__file__).resolve().parent.parent

INPUT_PATH = BASE_DIR / "outputs" / "jobs.json"
OUTPUT_PATH = BASE_DIR / "outputs" / "enriched_jobs.json"

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/120.0.0.0 Safari/537.36"
}


def extract_company_from_title(title):
    if not title:
        return None

    match = re.search(
        r"\bat\s+(.+?)(?:\s+[—–]\s+|\s+-\s+|$)",
        title,
        re.IGNORECASE
    )

    if not match:
        return None

    company = match.group(1).strip()

    company = re.sub(
        r"\s+in\s+India$",
        "",
        company,
        flags=re.IGNORECASE
    )

    company = re.sub(
        r"\s+-\s+Jobs$",
        "",
        company,
        flags=re.IGNORECASE
    )

    return company.strip() or None


def extract_company_from_jsonld(soup):
    def find_hiring_organization(data):
        if isinstance(data, dict):
            organization = data.get("hiringOrganization")

            if isinstance(organization, dict):
                name = organization.get("name")
                if name:
                    return name

            for value in data.values():
                result = find_hiring_organization(value)
                if result:
                    return result

        elif isinstance(data, list):
            for item in data:
                result = find_hiring_organization(item)
                if result:
                    return result

        return None

    for script in soup.find_all("script", type="application/ld+json"):
        try:
            data = json.loads(script.string or script.get_text())
            company = find_hiring_organization(data)

            if company:
                return company

        except (json.JSONDecodeError, TypeError):
            continue

    return None


def extract_company_metadata(soup):
    for attribute in ["name", "property"]:
        for key in ["company", "og:company"]:
            tag = soup.find("meta", attrs={attribute: key})

            if tag and tag.get("content"):
                return tag["content"].strip()

    return None


def extract_job_details(url, original_title=None, original_company=None):
    try:
        response = requests.get(
            url,
            headers=HEADERS,
            timeout=15
        )

        response.raise_for_status()

        soup = BeautifulSoup(response.text, "html.parser")

        title = soup.title.get_text(strip=True) if soup.title else None

        description = None

        selectors = [
            '[class*="job-description"]',
            '[class*="description"]',
            '[id*="description"]',
            'article',
            'main'
        ]

        for selector in selectors:
            element = soup.select_one(selector)

            if element:
                text = element.get_text(" ", strip=True)

                if len(text) > 300:
                    description = text
                    break

        # Extract company using multiple sources
        company = extract_company_from_jsonld(soup)
        company_source = "structured_data" if company else None

        if not company:
            company = extract_company_from_title(original_title)
            company_source = "job_title" if company else None

        if not company:
            company = extract_company_metadata(soup)
            company_source = "page_metadata" if company else None

        if not company and original_company:
            company = original_company
            company_source = "original_search_result"

        return {
            "page_title": title,
            "company": company,
            "company_source": company_source,
            "full_description": description,
            "extraction_status": (
                "success" if description else "description_not_found"
            )
        }

    except requests.RequestException as error:
        # Preserve company information even if page scraping fails.
        company = (
            original_company
            or extract_company_from_title(original_title)
        )

        return {
            "page_title": None,
            "company": company,
            "company_source": (
                "original_search_result" if company else None
            ),
            "full_description": None,
            "extraction_status": "failed",
            "error": str(error)
        }


def main():
    with open(INPUT_PATH, "r", encoding="utf-8") as file:
        jobs = json.load(file)

    enriched_jobs = []

    for index, job in enumerate(jobs, start=1):
        print(f"Processing {index}/{len(jobs)}: {job.get('job_title')}")

        details = extract_job_details(
            job["apply_url"],
            job.get("job_title"),
            job.get("company")
        )

        enriched_jobs.append({
            **job,
            **details
        })

        print("Company:", details["company"] or "Not identified")
        print("Company source:", details["company_source"])

    with open(OUTPUT_PATH, "w", encoding="utf-8") as file:
        json.dump(
            enriched_jobs,
            file,
            indent=4,
            ensure_ascii=False
        )

    successful = sum(
        job["extraction_status"] == "success"
        for job in enriched_jobs
    )

    identified = sum(
        bool(job.get("company"))
        for job in enriched_jobs
    )

    print("\nEnrichment completed.")
    print("Total jobs:", len(enriched_jobs))
    print("Descriptions extracted:", successful)
    print("Companies identified:", identified)
    print("Companies missing:", len(enriched_jobs) - identified)
    print("Saved to:", OUTPUT_PATH)


if __name__ == "__main__":
    main()
