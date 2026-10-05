import random
import streamlit as st

# FIX: The game rules moved to logic_utils.py (refactored with Claude Code in agent
# mode). app.py now only handles the Streamlit UI and session state.
from logic_utils import (
    check_guess,
    get_range_for_difficulty,
    parse_guess,
    update_score,
)


def start_new_game(difficulty: str, low: int, high: int):
    # FIX: New Game used to reset only the secret and attempts, so a finished game
    # stayed stuck on "Game over", and the secret always came from 1-100. Claude Code
    # suggested one helper that resets everything using the current difficulty's range.
    st.session_state.secret = random.randint(low, high)
    st.session_state.attempts = 0
    st.session_state.score = 0
    st.session_state.status = "playing"
    st.session_state.history = []
    st.session_state.difficulty = difficulty


st.set_page_config(page_title="Glitchy Guesser", page_icon="🎮")

st.title("🎮 Game Glitch Investigator")
st.caption("An AI-generated guessing game. Something is off.")

st.sidebar.header("Settings")

difficulty = st.sidebar.selectbox(
    "Difficulty",
    ["Easy", "Normal", "Hard"],
    index=1,
)

attempt_limit_map = {
    "Easy": 6,
    "Normal": 8,
    "Hard": 5,
}
attempt_limit = attempt_limit_map[difficulty]

low, high = get_range_for_difficulty(difficulty)

st.sidebar.caption(f"Range: {low} to {high}")
st.sidebar.caption(f"Attempts allowed: {attempt_limit}")

# FIX: Attempts used to start at 1, which cost the player a guess. Starting a game
# through start_new_game() sets it to 0. Switching difficulty also starts a new
# game now, so the secret is always inside the range shown in the sidebar.
if (
    "secret" not in st.session_state
    or st.session_state.get("difficulty") != difficulty
):
    start_new_game(difficulty, low, high)

st.subheader("Make a guess")

# FIX: The banner and debug panel used to be drawn here, before the guess was
# processed, so they were always one click behind (my first game showed "Attempts
# left: 1" next to "Out of attempts!"). Claude Code changed them to placeholders that
# are filled in at the bottom of the script, after the state has been updated.
status_banner = st.empty()
debug_panel = st.expander("Developer Debug Info")

raw_guess = st.text_input(
    "Enter your guess:",
    key=f"guess_input_{difficulty}"
)

col1, col2, col3 = st.columns(3)
with col1:
    submit = st.button("Submit Guess 🚀")
with col2:
    new_game = st.button("New Game 🔁")
with col3:
    show_hint = st.checkbox("Show hint", value=True)

if new_game:
    start_new_game(difficulty, low, high)
    st.success("New game started.")
elif st.session_state.status != "playing":
    if st.session_state.status == "won":
        st.success("You already won. Start a new game to play again.")
    else:
        st.error("Game over. Start a new game to try again.")
elif submit:
    ok, guess_int, err = parse_guess(raw_guess, low, high)

    if not ok:
        # FIX: An invalid guess used to use up an attempt. The attempt is now
        # counted only after parse_guess accepts the input.
        st.error(err)
    else:
        st.session_state.attempts += 1
        st.session_state.history.append(guess_int)

        # FIX: The secret used to be turned into a string on every other attempt,
        # which made the same guess get different hints. Claude Code found it by
        # replaying one guess twice; the secret is now always compared as an int.
        outcome, message = check_guess(guess_int, st.session_state.secret)

        if show_hint:
            st.warning(message)

        st.session_state.score = update_score(
            current_score=st.session_state.score,
            outcome=outcome,
            attempt_number=st.session_state.attempts,
        )

        if outcome == "Win":
            st.balloons()
            st.session_state.status = "won"
            st.success(
                f"You won! The secret was {st.session_state.secret}. "
                f"Final score: {st.session_state.score}"
            )
        elif st.session_state.attempts >= attempt_limit:
            st.session_state.status = "lost"
            st.error(
                f"Out of attempts! "
                f"The secret was {st.session_state.secret}. "
                f"Score: {st.session_state.score}"
            )

# FIX: The range text was hardcoded as "1 and 100"; it now uses the real range.
status_banner.info(
    f"Guess a number between {low} and {high}. "
    f"Attempts left: {attempt_limit - st.session_state.attempts}"
)

with debug_panel:
    st.write("Secret:", st.session_state.secret)
    st.write("Attempts:", st.session_state.attempts)
    st.write("Score:", st.session_state.score)
    st.write("Difficulty:", difficulty)
    st.write("History:", st.session_state.history)

st.divider()
st.caption("Built by an AI that claims this code is production-ready.")
