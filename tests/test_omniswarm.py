import pytest
from src.llm.gemini_synthesizer import GeminiRecruiterSynthesizer
from src.core.stealth_engine import InvisibleDotsStealth

def test_gemini_synthesizer_initialization():
    synth = GeminiRecruiterSynthesizer()
    assert synth is not None
    ans = synth.synthesize_answer("Why do you want to work here?", "Forward Deployed Engineer", "Test Company")
    assert isinstance(ans, str)
    assert len(ans) > 10

def test_stealth_bezier_curve():
    points = InvisibleDotsStealth.bezier_curve(p0=(0, 0), p1=(30, 80), p2=(70, 20), p3=(100, 100), num_points=10)
    assert len(points) >= 10
    assert points[0] == (0, 0)
    assert points[-1] == (100, 100)
