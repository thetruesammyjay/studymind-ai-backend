"""Tests for ML prompt template rendering."""

from types import SimpleNamespace

from app.ml.prompt_templates import render_study_prompt


class TestRenderStudyPrompt:
    def test_empty_history(self):
        result = render_study_prompt([], "What is gravity?")
        assert "What is gravity?" in result
        assert "Tutor:" in result

    def test_with_history(self):
        history = [
            SimpleNamespace(role="user", content="Hi"),
            SimpleNamespace(role="assistant", content="Hello! How can I help?"),
        ]
        result = render_study_prompt(history, "Explain photosynthesis")
        assert "Student: Hi" in result
        assert "Tutor: Hello! How can I help?" in result
        assert "Student: Explain photosynthesis" in result

    def test_roles_are_mapped(self):
        history = [
            SimpleNamespace(role="user", content="test message"),
        ]
        result = render_study_prompt(history, "follow up")
        assert "Student: test message" in result
        # The final question should also be "Student:"
        assert "Student: follow up" in result
