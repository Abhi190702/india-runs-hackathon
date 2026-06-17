"""Structured JD rubric for RedrobRank V2.

The ranker is intentionally rule-driven and inspectable. These concept groups
encode the Senior AI Engineer founding-team role with a bias toward career proof:
retrieval, ranking, search, recommendation, embeddings, production systems, and
behavioral availability.
"""

REFERENCE_TODAY = "2026-06-01"

EXPERIENCE = {
    "ideal_min": 5.0,
    "ideal_max": 9.0,
    "acceptable_min": 4.0,
    "acceptable_max": 11.0,
    "hard_floor": 2.0,
}

SOURCE_WEIGHTS = {
    "career_description_text": 1.00,
    "current_role_description_text": 1.00,
    "current_title_text": 0.85,
    "past_title_text": 0.70,
    "summary_headline_text": 0.45,
    "skills_text": 0.25,
    "education_text": 0.20,
    "company_industry_text": 0.35,
}

CAREER_BACKED_SOURCES = {
    "career_description_text",
    "current_role_description_text",
    "current_title_text",
    "past_title_text",
}

CORE_RETRIEVAL_RANKING = [
    "embeddings",
    "embedding model",
    "sentence transformers",
    "semantic search",
    "dense retrieval",
    "vector search",
    "hybrid search",
    "information retrieval",
    "FAISS",
    "Qdrant",
    "Milvus",
    "Pinecone",
    "Weaviate",
    "Elasticsearch",
    "OpenSearch",
    "BM25",
    "Lucene",
    "ANN",
    "nearest neighbor",
    "nearest neighbour",
    "reranking",
    "re-rank",
    "LLM reranker",
    "cross encoder",
    "bi encoder",
]

RANKING_RECOMMENDATION = [
    "ranking system",
    "learning to rank",
    "recommendation system",
    "recommender",
    "recommendation engine",
    "feed ranking",
    "personalization",
    "personalisation",
    "search relevance",
    "candidate matching",
    "matching engine",
    "relevance tuning",
    "LambdaMART",
    "RankNet",
    "XGBoost ranker",
    "LightGBM ranker",
]

EVALUATION_FRAMEWORKS = [
    "NDCG",
    "MRR",
    "MAP",
    "mean average precision",
    "precision@",
    "recall@",
    "offline evaluation",
    "online evaluation",
    "A/B testing",
    "AB testing",
    "experiment platform",
    "ranking metrics",
    "relevance judgment",
    "human labels",
    "click feedback",
    "feedback loop",
]

PRODUCTION_AI_SYSTEMS = [
    "production",
    "deployed",
    "deployment",
    "shipped",
    "launched",
    "real users",
    "live system",
    "scalable",
    "monitoring",
    "latency",
    "throughput",
    "model monitoring",
    "index refresh",
    "embedding drift",
    "data pipeline",
    "ML pipeline",
    "inference service",
    "API",
    "FastAPI",
    "microservice",
    "Docker",
    "Kubernetes",
    "MLflow",
    "Airflow",
    "Kafka",
]

PYTHON_ML_CORE = [
    "Python",
    "machine learning",
    "deep learning",
    "NLP",
    "natural language processing",
    "transformers",
    "Hugging Face",
    "PyTorch",
    "TensorFlow",
    "scikit-learn",
    "sklearn",
    "pandas",
    "numpy",
]

LLM_RAG = [
    "RAG",
    "retrieval augmented generation",
    "retrieval-augmented generation",
    "LangChain",
    "LlamaIndex",
    "OpenAI API",
    "chatbot",
    "agent",
    "prompt engineering",
    "fine-tuning",
    "fine tuning",
    "LoRA",
    "QLoRA",
    "PEFT",
]

NEGATIVE_WRONG_DOMAIN = [
    "HR Manager",
    "Marketing Manager",
    "Sales Executive",
    "Content Writer",
    "Graphic Designer",
    "Accountant",
    "Customer Support",
    "Operations Manager",
    "Mechanical Engineer",
    "Civil Engineer",
    "Business Analyst",
]

WEAK_OR_ADJACENT_DOMAIN = [
    "computer vision",
    "image classification",
    "object detection",
    "robotics",
    "SLAM",
    "lidar",
    "speech recognition",
    "ASR",
    "OCR",
]

ACTION_VERBS = [
    "built",
    "ship",
    "shipped",
    "owned",
    "designed",
    "implemented",
    "deployed",
    "scaled",
    "optimized",
    "optimised",
    "evaluated",
    "monitored",
    "launched",
    "maintained",
    "architected",
]

PRODUCT_STARTUP_TERMS = [
    "product",
    "saas",
    "fintech",
    "e-commerce",
    "ecommerce",
    "marketplace",
    "hr-tech",
    "hr tech",
    "recruiting",
    "talent",
    "startup",
    "founding",
    "small team",
    "search",
    "recommendation",
]

SERVICES_COMPANIES = {
    "tcs",
    "tata consultancy",
    "infosys",
    "wipro",
    "accenture",
    "cognizant",
    "capgemini",
    "hcl",
    "tech mahindra",
    "mindtree",
    "ltimindtree",
    "mphasis",
    "deloitte",
    "ibm global services",
    "dxc",
    "larsen",
    "l&t infotech",
    "persistent systems",
    "hexaware",
    "birlasoft",
    "coforge",
    "zensar",
}

SENIOR_AI_TITLES = [
    "senior ai engineer",
    "ai engineer",
    "machine learning engineer",
    "ml engineer",
    "applied scientist",
    "search engineer",
    "ranking engineer",
    "recommendation systems engineer",
    "recommendation engineer",
    "nlp engineer",
    "mlops engineer",
    "ai platform engineer",
    "staff machine learning",
    "senior machine learning",
]

ADJACENT_TITLES = [
    "data scientist",
    "data engineer",
    "backend engineer",
    "software engineer",
    "research engineer",
]

MANAGER_ONLY_TITLES = [
    "engineering manager",
    "director",
    "vp ",
    "head of",
    "program manager",
    "product manager",
    "architect",
]

LOCATION = {
    "preferred": ["pune", "noida"],
    "welcome": [
        "hyderabad",
        "mumbai",
        "delhi",
        "ncr",
        "gurgaon",
        "gurugram",
        "ghaziabad",
        "faridabad",
        "bangalore",
        "bengaluru",
    ],
    "country_ok": "india",
}

BEHAVIORAL = {
    "preferred_notice_days": 30,
    "max_reasonable_notice_days": 90,
    "active_recent_days": 45,
    "stale_days": 180,
}

CONCEPT_GROUPS = {
    "core_retrieval_ranking": {
        "label": "retrieval/search",
        "weight": 1.00,
        "phrases": CORE_RETRIEVAL_RANKING,
    },
    "ranking_recommendation": {
        "label": "ranking/recommendation",
        "weight": 1.00,
        "phrases": RANKING_RECOMMENDATION,
    },
    "evaluation_frameworks": {
        "label": "ranking evaluation",
        "weight": 0.78,
        "phrases": EVALUATION_FRAMEWORKS,
    },
    "production_ai_systems": {
        "label": "production ML systems",
        "weight": 0.86,
        "phrases": PRODUCTION_AI_SYSTEMS,
    },
    "python_ml_core": {
        "label": "Python/ML core",
        "weight": 0.64,
        "phrases": PYTHON_ML_CORE,
    },
    "llm_rag": {
        "label": "LLM/RAG",
        "weight": 0.48,
        "phrases": LLM_RAG,
    },
    "negative_wrong_domain": {
        "label": "wrong-domain role",
        "weight": -1.00,
        "phrases": NEGATIVE_WRONG_DOMAIN,
    },
    "weak_or_adjacent_domain": {
        "label": "adjacent AI domain",
        "weight": -0.35,
        "phrases": WEAK_OR_ADJACENT_DOMAIN,
    },
}

# Backward-compatible aliases for older helper scripts.
MUST_HAVE = {
    "embeddings_retrieval": {"weight": 3.0, "phrases": CORE_RETRIEVAL_RANKING},
    "ranking_recsys_search": {"weight": 3.0, "phrases": RANKING_RECOMMENDATION},
    "evaluation_frameworks": {"weight": 2.0, "phrases": EVALUATION_FRAMEWORKS},
    "strong_python_production": {"weight": 1.5, "phrases": PRODUCTION_AI_SYSTEMS + PYTHON_ML_CORE},
}
NICE_TO_HAVE = {
    "llm_rag": {"weight": 0.8, "phrases": LLM_RAG},
    "hr_marketplace_tech": {"weight": 0.6, "phrases": ["hr-tech", "recruiting", "marketplace", "talent"]},
}
WRONG_DOMAIN = {"weight": 1.2, "phrases": WEAK_OR_ADJACENT_DOMAIN}
FRAMEWORK_ENTHUSIAST = {"phrases": ["langchain", "llamaindex", "prompt engineering"]}
PURE_RESEARCH = {"phrases": ["research scientist", "phd researcher", "postdoc", "university"]}
TITLE_CHASE_MAX_AVG_TENURE_MONTHS = 20
TITLE_CHASE_MIN_JOBS = 3
STALE_IC_TITLES = set(MANAGER_ONLY_TITLES)
CODING_RECENCY_MONTHS = 18


def positive_concept_names():
    return [
        name
        for name, spec in CONCEPT_GROUPS.items()
        if spec.get("weight", 0.0) > 0
    ]


def concept_labels(names):
    return [CONCEPT_GROUPS.get(name, {}).get("label", name) for name in names]
