"""Play app.py headlessly with Streamlit's AppTest.

These cover the session-state bugs (attempt counter, New Game, stale banner,
difficulty switching, disappearing messages) that the logic_utils tests cannot see.
"""
from pathlib import Path

import pytest
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


# --- Bug: the attempt counter started at 1 ---

def test_fresh_game_shows_every_allowed_attempt():
    # Normal used to show 7 instead of 8
    at = start_app()
    assert "Attempts left: 8" in banner(at)
    assert at.session_state["attempts"] == 0


@pytest.mark.parametrize("difficulty, limit", [("Easy", 6), ("Normal", 8), ("Hard", 5)])
def test_each_difficulty_shows_its_attempt_limit(difficulty, limit):
    at = start_app(difficulty=difficulty)
    assert f"Attempts left: {limit}" in banner(at)


def test_player_gets_all_eight_attempts_on_normal():
    at = start_app(secret=50)
    for _ in range(7):
        submit_guess(at, "1")
    assert at.session_state["status"] == "playing"
    submit_guess(at, "1")
    assert at.session_state["status"] == "lost"
    assert "Attempts left: 0" in banner(at)


def test_correct_guess_on_the_last_attempt_is_a_win():
    at = start_app(secret=7, difficulty="Hard")
    for _ in range(4):
        submit_guess(at, "1")
    submit_guess(at, "7")
    assert at.session_state["status"] == "won"


# --- Bug: the banner was one click behind ---

def test_banner_updates_right_after_a_guess():
    # The banner used to be drawn before the guess was processed, so it was one
    # click behind the real attempt count in session state
    at = start_app(secret=50)
    submit_guess(at, "10")
    assert at.session_state["attempts"] == 1
    assert "Attempts left: 7" in banner(at)
    # The debug panel had the same problem
    assert "Attempts: `1`" in [m.value for m in at.expander[0].markdown]
    submit_guess(at, "20")
    assert at.session_state["attempts"] == 2
    assert "Attempts left: 6" in banner(at)


# --- Bug: the secret turned into a string on every other attempt ---

def test_same_guess_gets_the_same_hint_twice():
    at = start_app(secret=50)
    submit_guess(at, "9")
    first_hint = at.warning[0].value
    submit_guess(at, "9")
    second_hint = at.warning[0].value
    assert "HIGHER" in first_hint
    assert first_hint == second_hint


# --- Bug: bad input used up attempts ---

def test_invalid_guesses_do_not_use_attempts():
    at = start_app(secret=50)
    for bad in ("abc", "-2", "5000", "50.9", "49.99999999999999999", ""):
        submit_guess(at, bad)
        assert len(at.error) == 1
    assert at.session_state["attempts"] == 0
    assert at.session_state["history"] == []


def test_guess_is_checked_against_the_current_difficulty_range():
    at = start_app(difficulty="Easy")
    submit_guess(at, "50")
    assert "between 1 and 20" in at.error[0].value
    assert at.session_state["attempts"] == 0

    at = start_app(difficulty="Hard")
    submit_guess(at, "150")
    assert len(at.error) == 0
    assert at.session_state["attempts"] == 1


# --- Bug: scoring ---

def test_first_try_win_scores_100_and_ends_the_game():
    at = start_app(secret=50)
    submit_guess(at, "50")
    assert at.session_state["status"] == "won"
    assert at.session_state["score"] == 100

    # Submitting again after the win changes nothing
    submit_guess(at, "60")
    assert at.session_state["status"] == "won"
    assert at.session_state["attempts"] == 1
    assert at.session_state["score"] == 100


def test_score_never_goes_negative_during_a_game():
    # Wrong guesses used to push the score below zero
    at = start_app(secret=50)
    submit_guess(at, "60")
    assert at.session_state["score"] == 0
    submit_guess(at, "40")
    assert at.session_state["score"] == 0
    submit_guess(at, "50")
    # A win on the third attempt is worth 80
    assert at.session_state["score"] == 80
    assert "Final score: 80" in at.success[0].value


def test_lost_game_ends_with_a_score_of_zero():
    # My first game ended with "Score: -35"
    at = start_app(secret=50)
    for _ in range(8):
        submit_guess(at, "1")
        assert at.session_state["score"] == 0
    assert at.session_state["status"] == "lost"
    assert "Score: 0." in at.error[0].value
    # The loss message stays on screen after another click
    at.checkbox[0].uncheck().run()
    assert "Score: 0." in at.error[0].value


def test_win_on_the_last_attempt_shows_a_positive_final_score():
    # Seven wrong guesses and then a win used to show "Final score: -5"
    at = start_app(secret=50)
    for _ in range(7):
        submit_guess(at, "1")
    submit_guess(at, "50")
    assert at.session_state["status"] == "won"
    assert at.session_state["score"] == 30
    assert "Final score: 30" in at.success[0].value


# --- Bug: the hint and final score disappeared on the next click ---

def test_final_score_stays_on_screen_after_another_click():
    at = start_app(secret=50)
    submit_guess(at, "50")
    at.checkbox[0].uncheck().run()
    assert "Final score: 100" in at.success[0].value


def test_show_hint_checkbox_hides_and_shows_the_last_hint():
    at = start_app(secret=50)
    submit_guess(at, "60")
    assert "LOWER" in at.warning[0].value
    at.checkbox[0].uncheck().run()
    assert len(at.warning) == 0
    at.checkbox[0].check().run()
    assert "LOWER" in at.warning[0].value
    # An invalid guess does not wipe the last hint
    submit_guess(at, "abc")
    assert "LOWER" in at.warning[0].value


# --- Bug: New Game did not start a new game ---

def test_new_game_after_a_loss_resets_everything():
    # New Game used to leave the game stuck on "Game over"
    at = start_app(secret=50)
    for _ in range(8):
        submit_guess(at, "1")
    assert at.session_state["status"] == "lost"
    assert "Out of attempts" in at.error[0].value

    click_new_game(at)
    assert at.session_state["status"] == "playing"
    assert at.session_state["attempts"] == 0
    assert at.session_state["score"] == 0
    assert at.session_state["history"] == []
    assert "Attempts left: 8" in banner(at)
    assert len(at.warning) == 0
    assert len(at.error) == 0

    at.session_state["secret"] = 50
    submit_guess(at, "60")
    assert "LOWER" in at.warning[0].value

    # Win this second game, then start a third: the 90 points must not carry over
    submit_guess(at, "50")
    assert at.session_state["score"] == 90
    click_new_game(at)
    assert at.session_state["score"] == 0


# --- Bug: difficulty was ignored ---

def test_easy_mode_uses_its_own_range():
    # The banner said "1 and 100" and New Game picked secrets up to 100
    at = start_app(difficulty="Easy")
    assert "between 1 and 20" in banner(at)
    for _ in range(30):
        click_new_game(at)
        assert 1 <= at.session_state["secret"] <= 20


def test_switching_difficulty_starts_a_new_game():
    # The old secret (possibly out of range) and a finished game used to carry over
    at = start_app(secret=87)
    for _ in range(8):
        submit_guess(at, "10")
    assert at.session_state["status"] == "lost"

    at.sidebar.selectbox[0].set_value("Easy").run()
    assert 1 <= at.session_state["secret"] <= 20
    assert at.session_state["status"] == "playing"
    assert at.session_state["attempts"] == 0
    assert at.session_state["score"] == 0
    assert at.session_state["history"] == []
    assert "Attempts left: 6" in banner(at)

    # Win on Easy, then switch again: the 100 points must not carry over
    at.session_state["secret"] = 7
    submit_guess(at, "7")
    assert at.session_state["score"] == 100
    at.sidebar.selectbox[0].set_value("Hard").run()
    assert at.session_state["score"] == 0
