from jinja2 import Template

STUDY_QA_TEMPLATE = """
You are a friendly and knowledgeable AI tutor helping a student learn.
Context history:
{% for msg in history %}
{{ "Student" if msg.role == "user" else "Tutor" }}: {{ msg.content }}
{% endfor %}

Student: {{ question }}
Tutor: 
"""

def render_study_prompt(history: list, question: str) -> str:
    template = Template(STUDY_QA_TEMPLATE)
    return template.render(history=history, question=question)
