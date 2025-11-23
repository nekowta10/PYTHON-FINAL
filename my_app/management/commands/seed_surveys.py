from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from django.db import transaction

from my_app.models import Choice, Question, Section, Survey


LIKERT_SCALE = [
    "Strongly disagree",
    "Disagree",
    "Neutral",
    "Agree",
    "Strongly agree",
]


SURVEY_SETS = {
    "multiple_choice": [
        {
            "title": "Cybersecurity Fundamentals Quiz",
            "description": "Quick pulse on core security concepts for first-year IT students.",
            "questions": [
                {
                    "text": "Which protocol is used to secure HTTP traffic on the web?",
                    "type": "mcq",
                    "choices": ["HTTP", "FTP", "HTTPS", "SMTP"],
                    "correct": "HTTPS",
                },
                {
                    "text": "What does the principle of least privilege aim to reduce?",
                    "type": "mcq",
                    "choices": [
                        "System performance",
                        "Attack surface",
                        "Encryption strength",
                        "Network latency",
                    ],
                    "correct": "Attack surface",
                },
                {
                    "text": "Which malware encrypts files and demands payment?",
                    "type": "mcq",
                    "choices": ["Spyware", "Ransomware", "Adware", "Worm"],
                    "correct": "Ransomware",
                },
            ],
        },
        {
            "title": "Networking Essentials Check",
            "description": "Assess foundational networking knowledge for help desk trainees.",
            "questions": [
                {
                    "text": "What device creates separate broadcast domains?",
                    "type": "mcq",
                    "choices": ["Switch", "Router", "Hub", "Repeater"],
                    "correct": "Router",
                },
                {
                    "text": "Which IPv4 class provides up to 254 hosts per network?",
                    "type": "mcq",
                    "choices": ["Class A", "Class B", "Class C", "Class D"],
                    "correct": "Class C",
                },
                {
                    "text": "What layer of the OSI model handles reliable delivery?",
                    "type": "mcq",
                    "choices": ["Network", "Transport", "Session", "Application"],
                    "correct": "Transport",
                },
            ],
        },
        {
            "title": "Cloud Computing Basics",
            "description": "Gauge understanding of cloud service and deployment models.",
            "questions": [
                {
                    "text": "Which model lets customers deploy and manage apps without managing infrastructure?",
                    "type": "mcq",
                    "choices": ["IaaS", "PaaS", "SaaS", "On-prem"],
                    "correct": "PaaS",
                },
                {
                    "text": "Which deployment model is exclusive to one organization?",
                    "type": "mcq",
                    "choices": ["Public cloud", "Private cloud", "Community cloud", "Hybrid cloud"],
                    "correct": "Private cloud",
                },
                {
                    "text": "Which AWS service primarily provides object storage?",
                    "type": "mcq",
                    "choices": ["EC2", "Lambda", "S3", "RDS"],
                    "correct": "S3",
                },
            ],
        },
        {
            "title": "Programming Concepts Assessment",
            "description": "Short quiz on core programming principles used in CS1.",
            "questions": [
                {
                    "text": "What is the purpose of a loop in programming?",
                    "type": "mcq",
                    "choices": [
                        "To store data permanently",
                        "To repeat a block of code",
                        "To compile source files",
                        "To display output",
                    ],
                    "correct": "To repeat a block of code",
                },
                {
                    "text": "Which data structure uses FIFO ordering?",
                    "type": "mcq",
                    "choices": ["Stack", "Queue", "Tree", "Graph"],
                    "correct": "Queue",
                },
                {
                    "text": "What keyword defines a function in Python?",
                    "type": "mcq",
                    "choices": ["func", "def", "lambda", "function"],
                    "correct": "def",
                },
            ],
        },
        {
            "title": "Database Design Principles",
            "description": "Validate knowledge of relational modeling best practices.",
            "questions": [
                {
                    "text": "What does normalization help eliminate?",
                    "type": "mcq",
                    "choices": ["Indexes", "Redundant data", "Transactions", "Primary keys"],
                    "correct": "Redundant data",
                },
                {
                    "text": "What type of key uniquely identifies a row?",
                    "type": "mcq",
                    "choices": ["Foreign key", "Primary key", "Composite key", "Candidate key"],
                    "correct": "Primary key",
                },
                {
                    "text": "Which SQL clause filters rows returned by SELECT?",
                    "type": "mcq",
                    "choices": ["WHERE", "GROUP BY", "ORDER BY", "FROM"],
                    "correct": "WHERE",
                },
            ],
        },
    ],
    "short_answer": [
        {
            "title": "DevOps Retrospective Prompts",
            "description": "Capture reflections after the latest CI/CD sprint.",
            "questions": [
                {
                    "text": "Describe the most impactful automation we shipped this iteration.",
                    "type": "text",
                },
                {
                    "text": "Which deployment pain point should we prioritize next sprint?",
                    "type": "text",
                },
                {
                    "text": "List any monitoring gaps you observed in production.",
                    "type": "text",
                },
            ],
        },
        {
            "title": "AI Ethics Feedback",
            "description": "Collect qualitative feedback on responsible AI training.",
            "questions": [
                {
                    "text": "How would you explain model transparency to a stakeholder?",
                    "type": "text",
                },
                {
                    "text": "What safeguards should we add before shipping the next AI feature?",
                    "type": "text",
                },
                {
                    "text": "Share an example of bias mitigation you’ve used successfully.",
                    "type": "text",
                },
            ],
        },
        {
            "title": "UI/UX Research Debrief",
            "description": "Document findings from the latest usability study.",
            "questions": [
                {
                    "text": "Summarize the top usability win from this round of testing.",
                    "type": "text",
                },
                {
                    "text": "Which user journey still needs refinement and why?",
                    "type": "text",
                },
                {
                    "text": "What metric should we track to validate the next UI iteration?",
                    "type": "text",
                },
            ],
        },
        {
            "title": "Mobile App Release Retro",
            "description": "Capture lessons learned from the mobile release cycle.",
            "questions": [
                {
                    "text": "Which device-specific bug caused the most churn and why?",
                    "type": "text",
                },
                {
                    "text": "How can we shorten beta testing for the next version?",
                    "type": "text",
                },
                {
                    "text": "Identify a cross-functional partner who helped unblock the release.",
                    "type": "text",
                },
            ],
        },
        {
            "title": "IT Support Process Review",
            "description": "Understand how the support desk can improve workflows.",
            "questions": [
                {
                    "text": "What recurring ticket type needs better self-service content?",
                    "type": "text",
                },
                {
                    "text": "Suggest one automation that would speed up triage.",
                    "type": "text",
                },
                {
                    "text": "How should we escalate security-related incidents differently?",
                    "type": "text",
                },
            ],
        },
    ],
    "likert": [
        {
            "title": "Team Collaboration Sentiment",
            "description": "Measure how the engineering team feels about collaboration practices.",
            "questions": [
                {
                    "text": "Daily stand-ups help me stay aligned with my squad.",
                    "type": "likert",
                },
                {
                    "text": "Code reviews are constructive and timely.",
                    "type": "likert",
                },
                {
                    "text": "I can access the right stakeholders when blockers occur.",
                    "type": "likert",
                },
            ],
        },
        {
            "title": "Remote Tooling Satisfaction",
            "description": "Gauge satisfaction with the remote developer toolkit.",
            "questions": [
                {
                    "text": "Our VPN performance meets my daily needs.",
                    "type": "likert",
                },
                {
                    "text": "The virtual whiteboarding tools make collaboration easy.",
                    "type": "likert",
                },
                {
                    "text": "I rarely encounter issues with our communication stack.",
                    "type": "likert",
                },
            ],
        },
        {
            "title": "Learning Platform Evaluation",
            "description": "Understand how useful the internal LMS is for engineers.",
            "questions": [
                {
                    "text": "Course recommendations feel relevant to my growth goals.",
                    "type": "likert",
                },
                {
                    "text": "The LMS interface is intuitive to navigate.",
                    "type": "likert",
                },
                {
                    "text": "I regularly apply lessons from the platform to real projects.",
                    "type": "likert",
                },
            ],
        },
        {
            "title": "Security Awareness Confidence",
            "description": "Pulse check on how confident staff feel about security responsibilities.",
            "questions": [
                {
                    "text": "I understand how to report a potential phishing email.",
                    "type": "likert",
                },
                {
                    "text": "I know the data classification levels we use.",
                    "type": "likert",
                },
                {
                    "text": "I feel prepared to respond to a suspected breach.",
                    "type": "likert",
                },
            ],
        },
        {
            "title": "IT Service Desk Performance",
            "description": "Employee sentiment regarding responsiveness of IT support.",
            "questions": [
                {
                    "text": "IT resolves my tickets within the expected SLA.",
                    "type": "likert",
                },
                {
                    "text": "Technicians communicate clearly during troubleshooting.",
                    "type": "likert",
                },
                {
                    "text": "Handoffs between support tiers are seamless.",
                    "type": "likert",
                },
            ],
        },
    ],
}


def get_or_create_teacher():
    User = get_user_model()
    teacher, created = User.objects.get_or_create(
        username="sample_teacher",
        defaults={
            "email": "teacher@example.com",
            "first_name": "Sample",
            "last_name": "Teacher",
        },
    )
    if created:
        teacher.set_password("sample123")
        teacher.save()

    profile = getattr(teacher, "profile", None)
    if profile:
        profile.role = "teacher"
        if profile.section is None:
            section, _ = Section.objects.get_or_create(
                name="IT - Sample Section",
                defaults={"description": "Autogenerated for sample surveys"},
            )
            profile.section = section
        profile.save()

    return teacher


def ensure_likert_choices(question):
    existing = list(question.choices.values_list("text", flat=True))
    if existing:
        return
    Choice.objects.bulk_create(
        [Choice(question=question, text=label) for label in LIKERT_SCALE]
    )


class Command(BaseCommand):
    """Create IT-themed sample surveys across all available types."""

    help = "Seeds 5 example surveys for each survey type with IT-related content."

    def handle(self, *args, **options):
        teacher = get_or_create_teacher()
        created_count = 0

        with transaction.atomic():
            for survey_type, surveys in SURVEY_SETS.items():
                for payload in surveys:
                    survey, created = Survey.objects.get_or_create(
                        title=payload["title"],
                        defaults={
                            "description": payload["description"],
                            "created_by": teacher,
                            "survey_type": survey_type,
                            "is_active": True,
                        },
                    )
                    if not created:
                        continue

                    for question_payload in payload["questions"]:
                        question = Question.objects.create(
                            survey=survey,
                            text=question_payload["text"],
                            question_type=question_payload["type"],
                            required=True,
                        )
                        choices = question_payload.get("choices") or []
                        correct_choice = question_payload.get("correct")
                        for choice_text in choices:
                            Choice.objects.create(
                                question=question,
                                text=choice_text,
                                is_correct=choice_text == correct_choice,
                            )
                        if question.question_type == "likert":
                            ensure_likert_choices(question)

                    created_count += 1

        self.stdout.write(
            self.style.SUCCESS(f"Seeded {created_count} surveys across all types.")
        )

