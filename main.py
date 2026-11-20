
from pathlib import Path
import yaml

PROFILE_PATH = Path("candidate/candidate_profile.yaml")

def load_candidate_profile():
    with open(PROFILE_PATH, "r", encoding="utf-8") as file:
        profile = yaml.safe_load(file)

    return profile


if __name__ == "__main__":
    profile = load_candidate_profile()

    print("Candidate Profile Loaded Successfully")
    print("Candidate:", profile["candidate"]["full_name"])
    print("Target Roles:", profile["job_preferences"]["target_roles"])
