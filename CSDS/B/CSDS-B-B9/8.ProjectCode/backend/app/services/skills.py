"""Skill vocabulary and extraction shared by the resume analyser, the recruiter module and training."""
import re

SKILLS = [
    # programming and software
    "python", "java", "c++", "c#", "javascript", "typescript", "sql", "html", "css", "react", "angular", "node.js",
    "django", "flask", "fastapi", "spring", "php", ".net", "ruby", "golang", "kotlin", "swift", "matlab", "scala",
    "git", "linux", "unix", "docker", "kubernetes", "aws", "azure", "gcp", "rest api", "microservices", "agile",
    "scrum", "jira", "devops", "ci/cd", "jenkins", "testing", "selenium", "mysql", "postgresql", "oracle",
    "mongodb", "data structures", "algorithms", "oop", "machine learning", "deep learning", "nlp", "pandas",
    "numpy", "tensorflow", "pytorch", "tableau", "power bi", "excel", "data analysis", "statistics", "etl",
    "networking", "tcp/ip", "cybersecurity", "active directory", "vmware", "sap", "salesforce", "erp", "crm",
    "technical support", "troubleshooting", "system administration", "cloud",
    # engineering and design
    "autocad", "solidworks", "cad", "revit", "photoshop", "illustrator", "indesign", "figma", "ui/ux",
    "graphic design", "adobe creative suite", "video editing", "3d modeling", "quality control", "six sigma",
    "lean", "project management", "pmp", "safety", "osha", "maintenance", "manufacturing", "estimating",
    "blueprints", "scheduling",
    # business and finance
    "accounting", "bookkeeping", "quickbooks", "accounts payable", "accounts receivable", "financial analysis",
    "financial reporting", "budgeting", "forecasting", "auditing", "tax", "gaap", "payroll", "reconciliation",
    "banking", "lending", "underwriting", "risk management", "compliance", "investment", "credit",
    "sales", "business development", "negotiation", "lead generation", "account management", "marketing",
    "digital marketing", "seo", "social media", "content writing", "public relations", "communication",
    "customer service", "call center", "leadership", "team management", "training", "recruiting", "onboarding",
    "employee relations", "hris", "benefits administration", "procurement", "supply chain", "inventory",
    "logistics", "operations", "strategic planning", "consulting", "presentation", "research",
    # domain-specific
    "legal research", "litigation", "contracts", "patient care", "nursing", "cpr", "medical terminology", "ehr",
    "curriculum development", "lesson planning", "classroom management", "teaching", "tutoring",
    "menu development", "food safety", "culinary", "catering", "fitness", "personal training", "nutrition",
    "aviation", "faa", "aircraft maintenance", "flight", "agriculture", "crop", "farm", "fashion", "merchandising",
    "retail", "textile", "automotive", "vehicle", "diagnostics", "event planning", "media relations",
    "photography", "journalism", "editing", "copywriting", "art direction", "music", "painting",
]


def _pattern(skill):
    esc = re.escape(skill)
    return re.compile(r"(?<![a-z0-9+#.])" + esc + r"(?![a-z0-9+#])", re.I)


_PATTERNS = [(s, _pattern(s)) for s in SKILLS]


def extract_skills(text):
    """Return the vocabulary skills that appear in the text (lowercase names, vocabulary order)."""
    t = text or ""
    return [s for s, p in _PATTERNS if p.search(t)]


def normalise(skill):
    return (skill or "").strip().lower()
