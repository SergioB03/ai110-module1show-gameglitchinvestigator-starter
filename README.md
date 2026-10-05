# 🎮 Game Glitch Investigator: The Impossible Guesser

## 🚨 The Situation

You asked an AI to build a simple "Number Guessing Game" using Streamlit.
It wrote the code, ran away, and now the game is unplayable. 

- You can't win.
- The hints lie to you.
- The secret number seems to have commitment issues.

## 🛠️ Setup

1. Create and activate a virtual environment (on Windows use `py -m venv .venv`, then `.\.venv\Scripts\Activate.ps1`).
2. Install dependencies: `pip install -r requirements.txt`
3. Run the app: `python -m streamlit run app.py`
4. Run the tests: `pytest`

## 🕵️‍♂️ Your Mission

1. **Play the game.** Open the "Developer Debug Info" tab in the app to see the secret number. Try to win.
2. **Find the State Bug.** Why does the secret number change every time you click "Submit"? Ask ChatGPT: *"How do I keep a variable from resetting in Streamlit when I click a button?"*
3. **Fix the Logic.** The hints ("Higher/Lower") are wrong. Fix them.
4. **Refactor & Test.** - Move the logic into `logic_utils.py`.
   - Run `pytest` in your terminal.
   - Keep fixing until all tests pass!

## 📝 Document Your Experience

- [x] Describe the game's purpose.
- [x] Detail which bugs you found.
- [x] Explain what fixes you applied.

### The game's purpose

A number guessing game built with Streamlit. The app picks a secret whole number, you type guesses, and after each guess the game tells you whether to go higher or lower. You win by hitting the secret before you run out of attempts.

| Difficulty | Range | Attempts |
|------------|-------|----------|
| Easy | 1 to 20 | 6 |
| Normal | 1 to 100 | 8 |
| Hard | 1 to 200 | 5 |

A win is worth 100 points minus 10 for every extra attempt (never less than 10). Each wrong guess costs 5 points, but the score never drops below 0. Because every game starts at 0, the score stays at 0 until you win.

### Bugs I found

The starter game never crashed, but it could not be played fairly. The full reproduction log is in [reflection.md](reflection.md).

| # | Bug | Where it was in the starter code |
|---|-----|----------------------------------|
| 1 | Hints were backwards: a guess that was too high said "Go HIGHER!" | `check_guess` in `app.py` |
| 2 | The secret was turned into a string on every other attempt, so guesses were compared as text and the same guess could get opposite hints | submit handler in `app.py` |
| 3 | The attempt counter started at 1, so the player got one guess fewer than the sidebar promised | session state setup in `app.py` |
| 4 | New Game did not reset the status, history or score, so a finished game stayed stuck on "Game over" or "You already won" | New Game handler in `app.py` |
| 5 | Difficulty was ignored: the banner always said "1 and 100", New Game always picked from 1-100, and switching difficulty kept the old secret | `app.py` |
| 6 | Hard used the range 1-50, narrower than Normal | `get_range_for_difficulty` |
| 7 | A wrong "Too High" guess added 5 points on even attempts, a first-try win could not score 100, and the score could go negative (a lost game ended at -35, and a win on the last guess showed "Final score: -20") | `update_score` |
| 8 | Invalid input used up an attempt, `50.9` was silently cut down to 50, and out-of-range guesses like `-2` were accepted | `parse_guess` and the submit handler |
| 9 | The "Attempts left" banner was drawn before the guess was processed, so it was always one click behind | `app.py` |
| 10 | The hint and the "You won" message with the final score were only drawn right after Submit, so they disappeared on the next click | submit handler in `app.py` |
| 11 | The starter tests could not pass: `logic_utils.py` was only stubs, and a plain `pytest` could not import it | `logic_utils.py`, `tests/` |

### Fixes I applied

- **Refactor.** Moved `get_range_for_difficulty`, `parse_guess`, `check_guess` and `update_score` out of `app.py` into `logic_utils.py`, so `app.py` only handles the Streamlit UI and session state and the rules can be tested on their own.
- **Hints.** Swapped the two messages in `check_guess` and removed the `try/except` that compared numbers as text. `app.py` now always passes the secret as an int.
- **Attempts.** The counter starts at 0 and only goes up when a guess is valid.
- **New Game.** One `start_new_game()` helper resets the secret, attempts, score, status and history, and picks the secret from the current difficulty's range. Changing the difficulty starts a new game too.
- **Banner.** The banner and debug panel are placeholders that get filled in at the end of the script, after the guess has been processed. The range in the banner comes from the difficulty.
- **Scoring.** Every wrong guess costs 5 points, a first-try win is worth 100, and the score never drops below 0.
- **Input.** `parse_guess` rejects text, decimals and numbers outside the range, each with its own message, and none of them cost an attempt. It reads the number with `Decimal`, so `49.99999999999999999` is not rounded up to 50.
- **Messages.** The last hint and the win or loss message are kept in session state and drawn on every rerun, so the final score stays on screen until you start a new game.
- **Hard mode.** The range is now 1 to 200.
- **Tests.** Updated the three starter tests to unpack the `(outcome, message)` pair, added tests for every fix, and added `pytest.ini` so `pytest` finds `logic_utils`.

## 📸 Demo Walkthrough

One sample game on Normal difficulty. The secret in this run was 42 (you can see it under "Developer Debug Info").

1. The page loads. The sidebar shows "Range: 1 to 100" and "Attempts allowed: 8", and the banner says "Guess a number between 1 and 100. Attempts left: 8".
2. User enters a guess of 50. The game shows "📉 Go LOWER!" and the banner drops to "Attempts left: 7". The score stays at 0, because it never drops below zero.
3. User enters a guess of 25. The game shows "📈 Go HIGHER!" and the banner shows "Attempts left: 6". The score is still 0.
4. User types `abc`. The game shows "That is not a number." and the banner stays at "Attempts left: 6". The last hint, "📈 Go HIGHER!", stays on screen.
5. User types `-2`. The game shows "Enter a number between 1 and 100." and no attempt is used.
6. User types `42.5`. The game shows "Enter a whole number." and no attempt is used.
7. User enters a guess of 42. The game shows "🎉 Correct!", balloons, and "You won! The secret was 42. Final score: 80. Start a new game to play again." A win on the third attempt is worth 80: 100 minus 10 for each of the two extra attempts.
8. User clicks Submit again. Nothing changes: the win message and the final score stay on screen, and no attempt is used.
9. User clicks "New Game 🔁". The game shows "New game started.", the banner goes back to "Attempts left: 8", and the score and history are cleared.
10. User switches the difficulty to Hard. A new game starts on its own, and the banner says "Guess a number between 1 and 200. Attempts left: 5".

## 🧪 Test Results

```
$ pytest
============================= test session starts =============================
platform win32 -- Python 3.12.5, pytest-9.1.1, pluggy-1.6.0
rootdir: C:\Users\sergi\ai110-module1show-gameglitchinvestigator-starter
configfile: pytest.ini
testpaths: tests
plugins: anyio-4.15.1
collected 79 items

tests\test_app_flow.py ....................                              [ 25%]
tests\test_game_logic.py ............................................... [ 84%]
............                                                             [100%]

============================= 79 passed in 3.46s ==============================
```

`tests/test_game_logic.py` tests the rules in `logic_utils.py`. `tests/test_app_flow.py` plays `app.py` headlessly with Streamlit's `AppTest` to cover the session-state bugs. Run against the original starter code, 49 of these 79 tests fail.

## 🚀 Stretch Features

- [x] **Challenge 1: Advanced Edge-Case Testing.** `parse_guess` is tested with empty and whitespace-only input, text (`abc`, `12abc`), `nan` and `inf`, decimals (`50.9`, `-3.14`, and `49.99999999999999999`, which `float()` would round to 50), negative numbers, numbers on both ends of the range and just outside it, and 400-digit and 5000-digit numbers. The output is in Test Results above.
- [x] **AI interactions log.** The agent workflow and test generation notes are in [ai_interactions.md](ai_interactions.md).
- [ ] Challenge 4 (Enhanced UI): not attempted.
