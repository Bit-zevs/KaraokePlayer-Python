import numpy as np

from karaoke_player.services.vocal_scorer import VocalScorer


def test_vocal_scorer_initial_state():
    scorer = VocalScorer()

    assert scorer._score == 0
    assert scorer._total_checks == 0
    assert scorer._voice_checks == 0


def test_vocal_scorer_reset():
    scorer = VocalScorer()

    scorer._score = 80
    scorer._voice_checks = 10
    scorer._total_checks = 12

    scorer.reset()

    assert scorer._score == 0
    assert scorer._voice_checks == 0
    assert scorer._total_checks == 0


def test_detects_voice():
    scorer = VocalScorer()

    scorer._last_audio = np.ones(2048, dtype=np.float32) * 0.05
    scorer._analyze_voice()

    assert scorer._voice_checks > 0
    assert scorer._score > 0


def test_detects_silence():
    scorer = VocalScorer()

    scorer._last_audio = np.zeros(2048, dtype=np.float32)
    scorer._analyze_voice()

    assert scorer._voice_checks == 0