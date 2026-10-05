import math

# FIX: These four functions used to live in app.py, mixed in with the Streamlit UI.
# Refactored into this module with Claude Code (agent mode) so pytest can test the
# game rules without starting the app.


def get_range_for_difficulty(difficulty: str):
    """Return (low, high) inclusive range for a given difficulty."""
    if difficulty == "Easy":
        return 1, 20
    if difficulty == "Normal":
        return 1, 100
    if difficulty == "Hard":
        # FIX: Hard was 1-50, narrower than Normal. Claude Code laid out three options
        # (keep 1-50, 1-200, or 1-200 with more attempts) and I chose 1-200.
        return 1, 200
    return 1, 100


def parse_guess(raw: str, low=None, high=None):
    """
    Parse user input into an int guess.

    When low and high are given, the guess must fall inside that inclusive range.

    Returns: (ok: bool, guess_int: int | None, error_message: str | None)
    """
    if raw is None or raw.strip() == "":
        return False, None, "Enter a guess."

    try:
        number = float(raw)
    except ValueError:
        return False, None, "That is not a number."

    # float() also accepts "nan" and "inf", which are not guesses.
    if not math.isfinite(number):
        return False, None, "That is not a number."

    # FIX: 50.9 used to be cut down to 50 without telling the player, so it could
    # win the game. Claude Code suggested rejecting decimals; "50.0" still counts.
    if not number.is_integer():
        return False, None, "Enter a whole number."

    value = int(number)

    # FIX: I noticed the game accepted -2 without any out-of-range message. Claude
    # Code added the optional low/high check so app.py can pass in the real range.
    if low is not None and high is not None and not low <= value <= high:
        return False, None, f"Enter a number between {low} and {high}."

    return True, value, None


def check_guess(guess, secret):
    """
    Compare guess to secret and return (outcome, message).

    outcome examples: "Win", "Too High", "Too Low"
    """
    if guess == secret:
        return "Win", "🎉 Correct!"

    # FIX: The messages were swapped, so a guess that was too high said "Go HIGHER!".
    # I hit this in my first game (secret 77, told to go lower); Claude Code traced
    # it to these two lines. The try/except that compared the numbers as text is
    # gone too, because app.py now always passes the secret as an int.
    if guess > secret:
        return "Too High", "📉 Go LOWER!"
    return "Too Low", "📈 Go HIGHER!"


def update_score(current_score: int, outcome: str, attempt_number: int):
    """Update score based on outcome and attempt number."""
    if outcome == "Win":
        # FIX: Was 100 - 10 * (attempt_number + 1), so a first-try win could never
        # score 100. Claude Code spotted the off-by-one; attempt 1 now pays 100.
        points = 100 - 10 * (attempt_number - 1)
        if points < 10:
            points = 10
        return current_score + points

    # FIX: "Too High" used to add 5 points on even attempts. Found by Claude Code
    # while replaying the game; every wrong guess now costs 5.
    if outcome in ("Too High", "Too Low"):
        return current_score - 5

    return current_score
