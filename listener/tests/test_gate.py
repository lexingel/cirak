import sys, pathlib
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1]))
from gate import QuestionGate


def test_no_question_without_narration():
    g = QuestionGate(min_interval=300)
    assert not g.should_ask(now=1000)


def test_asks_after_enough_words():
    g = QuestionGate(min_interval=300, min_words=8)
    g.add_text("şimdi giriş ekranındaki butonların hizasını tek tek düzeltiyorum galiba", now=10)
    assert g.should_ask(now=12)


def test_min_interval_between_questions():
    g = QuestionGate(min_interval=300, min_words=1)
    g.add_text("bir iki üç", now=0); g.mark_asked(now=1)
    g.add_text("dört beş altı", now=150)
    assert not g.should_ask(now=200)
    assert g.should_ask(now=302)


def test_ignores_hallucinations_and_short():
    g = QuestionGate(min_words=8)
    g.add_text("Altyazı M.K.", now=1); g.add_text("hmm tamam", now=2); g.add_text("   ", now=3)
    assert not g.should_ask(now=400)


def test_pause_clears_buffer():
    g = QuestionGate(min_words=1)
    g.add_text("uzun bir anlatım burada devam ediyor", now=1)
    g.pause()
    assert not g.should_ask(now=400) and g.context() == ""


def test_level_mapping():
    g = QuestionGate(); g.set_level("high")
    assert g.min_interval == 120


def test_old_text_drops_out_of_window():
    g = QuestionGate(min_words=3)
    g.add_text("bir iki üç dört", now=0)
    assert not g.should_ask(now=400)  # older than 180 s window


def test_short_utterances_do_not_add_up():
    g = QuestionGate(min_words=8)
    for i in range(4):
        g.add_text("hmm tamam", now=i)
    for i in range(8):
        g.add_text("Teşekkürler.", now=10 + i)
    assert not g.should_ask(now=400 - 300)  # within window, interval met from -inf


def test_english_hallucinations_ignored():
    g = QuestionGate(min_words=3)
    g.add_text("Thank you for watching!", now=1)
    g.add_text("Subtitles by the Amara.org community", now=2)
    assert not g.should_ask(now=5)
