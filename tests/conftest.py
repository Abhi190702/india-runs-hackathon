import copy
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))


def make_candidate():
    return {
        "candidate_id": "CAND_0000001",
        "profile": {
            "anonymized_name": "Demo",
            "headline": "Senior ML Engineer",
            "summary": "Builds production semantic search and ranking systems.",
            "location": "Pune",
            "country": "India",
            "years_of_experience": 7.0,
            "current_title": "Senior ML Engineer",
            "current_company": "Talent AI",
            "current_company_size": "51-200",
            "current_industry": "HR-tech SaaS",
        },
        "career_history": [
            {
                "company": "Talent AI",
                "title": "Senior ML Engineer",
                "start_date": "2019-01-01",
                "end_date": None,
                "duration_months": 89,
                "is_current": True,
                "industry": "HR-tech SaaS",
                "company_size": "51-200",
                "description": "Built and deployed FAISS semantic search, candidate matching, reranking, NDCG evaluation, and production API monitoring.",
            }
        ],
        "education": [
            {
                "institution": "Demo Institute",
                "degree": "B.Tech",
                "field_of_study": "Computer Science",
                "start_year": 2014,
                "end_year": 2018,
                "tier": "tier_2",
            }
        ],
        "skills": [
            {"name": "Python", "proficiency": "expert", "endorsements": 30, "duration_months": 72},
            {"name": "FAISS", "proficiency": "advanced", "endorsements": 12, "duration_months": 24},
        ],
        "redrob_signals": {
            "profile_completeness_score": 95,
            "signup_date": "2025-01-01",
            "last_active_date": "2026-05-20",
            "open_to_work_flag": True,
            "profile_views_received_30d": 12,
            "applications_submitted_30d": 1,
            "recruiter_response_rate": 0.8,
            "avg_response_time_hours": 12,
            "skill_assessment_scores": {"Python": 90, "FAISS": 80},
            "connection_count": 100,
            "endorsements_received": 50,
            "notice_period_days": 30,
            "expected_salary_range_inr_lpa": {"min": 40, "max": 55},
            "preferred_work_mode": "hybrid",
            "willing_to_relocate": True,
            "github_activity_score": 70,
            "search_appearance_30d": 10,
            "saved_by_recruiters_30d": 3,
            "interview_completion_rate": 0.9,
            "offer_acceptance_rate": 0.7,
            "verified_email": True,
            "verified_phone": True,
            "linkedin_connected": True,
        },
    }


def clone_candidate(**changes):
    candidate = copy.deepcopy(make_candidate())
    for key, value in changes.items():
        candidate[key] = value
    return candidate
