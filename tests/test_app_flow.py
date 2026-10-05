"""Play app.py headlessly with Streamlit's AppTest.

These cover the session-state bugs (attempt counter, New Game, stale banner,
difficulty switching) that the logic_utils tests cannot see.
"""
from pathlib import Path

from streamlit.testing.v1 import AppTest

APP_PATH = str(Path(__file__).resolve().parent.parent / "app.py")


def start_app(secret=None, difficulty=None):
    at = AppTest.from_file(APP_PATH, default_timeout=30).run()
    if difficulty is not None:
        at.sidebar.selectbox[0].set_value(difficulty).run()
    if secret is not None:
        at.session_state["secret"] = secret
        at.run()
    return at


def submit_guess(at, text):
    at.text_input[0].set_value(text)
    at.button[0].click()
    at.run()


def click_new_game(at):
    at.button[1].click()
    at.run()


def banner(at):
    return at.info[0].value


def test_app_starts_without_errors():
    at = start_app()
    assert not at.exception


def test_fresh_game_shows_every_allowed_attempt():
    # The counter used to start at 1, so Normal showed 7 instead of 8
    at = start_app()
    assert "Attempts left: 8" in banner(at)
    assert at.session_state["attempts"] == 0


def test_banner_updates_right_after_a_guess():
    # The banner used to be drawn before the guess was processed, so it was one
    # click behind the real attempt count in session state
    at = start_app(secret=50)
    submit_guess(at, "10")
    assert at.session_state["attempts"] == 1
    assert "Attempts left: 7" in banner(at)
    submit_guess(at, "20")
    assert at.session_state["attempts"] == 2
    assert "Attempts left: 6" in banner(at)


def test_same_guess_gets_the_same_hint_twice():
    # The secret used to turn into a string on every other attempt
    at = start_app(secret=50)
    submit_guess(at, "9")
    first_hint = at.warning[0].value
    submit_guess(at, "9")
    second_hint = at.warning[0].value
    assert "HIGHER" in first_hint
    assert first_hint == second_hint


def test_player_gets_all_eight_attempts_on_normal():
    at = start_app(secret=50)
    for _ in range(7):
        submit_guess(at, "1")
    assert at.session_state["status"] == "playing"
    submit_guess(at, "1")
    assert at.session_state["status"] == "lost"
    assert "Attempts left: 0" in banner(at)


def test_invalid_guesses_do_not_use_attempts():
    at = start_app(secret=50)
    for bad in ("abc", "-2", "5000", "50.9", ""):
        submit_guess(at, bad)
        assert len(at.error) == 1
    assert at.session_state["attempts"] == 0
    assert at.session_state["history"] == []


def test_first_try_win_scores_100_and_ends_the_game():
    at = start_app(secret=50)
    submit_guess(at, "50")
    assert at.session_state["status"] == "won"
    assert at.session_state["score"] == 100
    submit_guess(at, "50")
    assert "already won" in at.success[0].value


def test_new_game_after_a_loss_resets_everything():
    # New Game used to leave the game stuck on "Game over"
    at = start_app(secret=50)
    for _ in range(8):
        submit_guess(at, "1")
    assert at.session_state["status"] == "lost"

    click_new_game(at)
    assert at.session_state["status"] == "playing"
    assert at.session_state["attempts"] == 0
    assert at.session_state["score"] == 0
    assert at.session_state["history"] == []
    assert "Attempts left: 8" in banner(at)

    at.session_state["secret"] = 50
    submit_guess(at, "60")
    assert "LOWER" in at.warning[0].value


def test_easy_mode_uses_its_own_range():
    # The banner said "1 and 100" and New Game picked secrets up to 100
    at = start_app(difficulty="Easy")
    assert "between 1 and 20" in banner(at)
    for _ in range(30):
        click_new_game(at)
        assert 1 <= at.session_state["secret"] <= 20


def test_switching_difficulty_starts_a_new_game():
    # The old secret (possibly out of range) used to carry over
    at = start_app(secret=87)
    submit_guess(at, "10")
    at.sidebar.selectbox[0].set_value("Easy").run()
    assert 1 <= at.session_state["secret"] <= 20
    assert at.session_state["attempts"] == 0
    assert "Attempts left: 6" in banner(at)
