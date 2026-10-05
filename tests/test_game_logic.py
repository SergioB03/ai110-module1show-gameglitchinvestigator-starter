import pytest

from logic_utils import (
    check_guess,
    get_range_for_difficulty,
    parse_guess,
    update_score,
)


# --- Starter tests ---
# check_guess returns (outcome, message), so these now unpack the pair instead of
# comparing the whole tuple to a string.

def test_winning_guess():
    # If the secret is 50 and guess is 50, it should be a win
    outcome, _ = check_guess(50, 50)
    assert outcome == "Win"

def test_guess_too_high():
    # If secret is 50 and guess is 60, hint should be "Too High"
    outcome, _ = check_guess(60, 50)
    assert outcome == "Too High"

def test_guess_too_low():
    # If secret is 50 and guess is 40, hint should be "Too Low"
    outcome, _ = check_guess(40, 50)
    assert outcome == "Too Low"


# --- Bug: the hints pointed the wrong way ---

def test_too_high_hint_says_go_lower():
    _, message = check_guess(60, 50)
    assert "LOWER" in message

def test_too_low_hint_says_go_higher():
    _, message = check_guess(40, 50)
    assert "HIGHER" in message

def test_hints_from_my_first_game():
    # My first game: the secret was 77 and every guess below it said "Go LOWER!"
    for guess in (50, 25, 10, 1):
        outcome, message = check_guess(guess, 77)
        assert outcome == "Too Low"
        assert "HIGHER" in message


# --- Bug: the secret was compared as text on every other attempt ---

def test_guess_with_fewer_digits_is_too_low():
    # As text "9" > "50", but as numbers 9 is too low
    outcome, _ = check_guess(9, 50)
    assert outcome == "Too Low"

def test_guess_with_more_digits_is_too_high():
    # As text "100" < "50", but as numbers 100 is too high
    outcome, _ = check_guess(100, 50)
    assert outcome == "Too High"

def test_string_secret_is_not_silently_compared_as_text():
    # The old code caught this TypeError and fell back to comparing strings
    with pytest.raises(TypeError):
        check_guess(9, "50")


# --- Bug: scoring ---

def test_first_try_win_scores_100():
    assert update_score(0, "Win", 1) == 100

def test_win_is_worth_10_less_per_extra_attempt():
    assert update_score(0, "Win", 2) == 90
    assert update_score(0, "Win", 5) == 60

def test_win_points_are_added_to_the_current_score():
    assert update_score(40, "Win", 1) == 140

def test_win_is_never_worth_less_than_10():
    assert update_score(0, "Win", 50) == 10

@pytest.mark.parametrize("outcome", ["Too High", "Too Low"])
@pytest.mark.parametrize("attempt_number", [1, 2, 3, 4])
def test_wrong_guess_always_costs_5(outcome, attempt_number):
    # "Too High" used to ADD 5 points on even attempts
    assert update_score(20, outcome, attempt_number) == 15

@pytest.mark.parametrize("outcome", ["Too High", "Too Low"])
@pytest.mark.parametrize("current_score", [0, 3, 5])
def test_score_never_drops_below_zero(outcome, current_score):
    # My first game ended with a score of -35
    assert update_score(current_score, outcome, 1) == 0

def test_score_stays_at_zero_through_a_whole_losing_game():
    score = 0
    for attempt_number in range(1, 9):
        score = update_score(score, "Too Low", attempt_number)
        assert score == 0

def test_win_after_only_wrong_guesses_is_still_positive():
    # A win on Normal's 8th attempt used to show a final score of -5
    score = 0
    for attempt_number in range(1, 8):
        score = update_score(score, "Too High", attempt_number)
    assert update_score(score, "Win", 8) == 30

def test_unknown_outcome_leaves_score_alone():
    assert update_score(20, "Something else", 1) == 20


# --- Bug: difficulty ranges ---

def test_ranges_for_each_difficulty():
    assert get_range_for_difficulty("Easy") == (1, 20)
    assert get_range_for_difficulty("Normal") == (1, 100)
    assert get_range_for_difficulty("Hard") == (1, 200)

def test_harder_difficulty_has_wider_range():
    _, easy_high = get_range_for_difficulty("Easy")
    _, normal_high = get_range_for_difficulty("Normal")
    _, hard_high = get_range_for_difficulty("Hard")
    assert easy_high < normal_high < hard_high

def test_unknown_difficulty_falls_back_to_normal_range():
    assert get_range_for_difficulty("Impossible") == (1, 100)


# --- Edge cases: parsing the player's input ---

def test_parse_valid_guess():
    assert parse_guess("42") == (True, 42, None)

def test_parse_ignores_surrounding_spaces():
    assert parse_guess("  42  ") == (True, 42, None)

@pytest.mark.parametrize("raw", [None, "", "   "])
def test_parse_empty_input(raw):
    assert parse_guess(raw) == (False, None, "Enter a guess.")

@pytest.mark.parametrize("raw", ["abc", "12abc", "five", "1.2.3", "nan", "inf", "-inf"])
def test_parse_rejects_non_numbers(raw):
    assert parse_guess(raw) == (False, None, "That is not a number.")

@pytest.mark.parametrize("digits", [400, 5000])
def test_parse_rejects_extremely_large_number(digits):
    # A huge number is just out of range; it must not crash or hang
    assert parse_guess("9" * digits, 1, 100) == (False, None, "Enter a number between 1 and 100.")

@pytest.mark.parametrize("raw", ["50.9", "0.5", "-3.14"])
def test_parse_rejects_decimals(raw):
    # 50.9 used to be cut down to 50 and could win the game
    assert parse_guess(raw) == (False, None, "Enter a whole number.")

def test_parse_rejects_decimal_that_float_would_round_to_50():
    # float("49.99999999999999999") == 50.0, so this guess used to count as 50
    assert parse_guess("49.99999999999999999") == (False, None, "Enter a whole number.")

def test_parse_accepts_whole_number_written_as_decimal():
    assert parse_guess("50.0") == (True, 50, None)

def test_parse_without_range_accepts_negative_number():
    assert parse_guess("-5") == (True, -5, None)

@pytest.mark.parametrize("raw", ["-2", "0", "101", "5000"])
def test_parse_rejects_guess_outside_range(raw):
    # In my first game -2 was accepted and used up an attempt
    assert parse_guess(raw, 1, 100) == (False, None, "Enter a number between 1 and 100.")

@pytest.mark.parametrize("raw, expected", [("1", 1), ("100", 100)])
def test_parse_accepts_both_ends_of_range(raw, expected):
    assert parse_guess(raw, 1, 100) == (True, expected, None)
