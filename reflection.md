# 💭 Reflection: Game Glitch Investigator

Answer each question in 3 to 5 sentences. Be specific and honest about what actually happened while you worked. This is about your process, not trying to sound perfect.

## 1. What was broken when you started?

- What did the game look like the first time you ran it?
- List at least two concrete bugs you noticed at the start  
  (for example: "the hints were backwards").

The first time I ran it, the app loaded without errors and looked like a normal number guessing game: a banner saying "Guess a number between 1 and 100", a text box, Submit and New Game buttons, and a sidebar to pick the difficulty. Nothing crashed, but I could not win by following the hints. The hints kept telling me to "Go LOWER!", so I kept guessing lower until I was typing negative numbers like -2, and the game still said "Go LOWER!" and never told me I was out of range. When I ran out of attempts it revealed the secret was 77, so the hints had been sending me the wrong way the whole game, and my score ended at -35. The banner also still said "Attempts left: 1" right above the "Out of attempts!" message.

After that I had Claude Code read `app.py` and replay the game with the secret pinned to a known value (using Streamlit's `AppTest` harness), which turned up more bugs than I had noticed by hand. These are the concrete bugs. Line numbers are from the starter `app.py`, before any edits.

1. **Hints are backwards.** `check_guess` (lines 37-40) returns the right outcome but the wrong message: a guess that is too high says "📈 Go HIGHER!" and one that is too low says "📉 Go LOWER!".
2. **The secret changes type every other guess.** Lines 158-161 turn the secret into a string on even-numbered attempts. `check_guess` then hits a `TypeError`, swallows it, and falls back to comparing text, where `"9" > "50"`. The same guess can get opposite hints on two submits in a row.
3. **The attempt counter is off by one.** `attempts` starts at 1 (line 96), so Normal shows "Attempts left: 7" on a fresh page and ends the game after 7 guesses, even though the sidebar says 8 are allowed.
4. **New Game does not start a new game.** The handler (lines 134-138) never resets `status` or `history`, so after a win or loss the game stays stuck on "Game over". It also draws the secret from 1-100 no matter the difficulty.
5. **Difficulty is not respected.** The banner hardcodes "between 1 and 100" (line 110), Hard's range (1-50, line 10) is narrower than Normal's (1-100), and switching difficulty keeps the old secret.
6. **Scoring is wrong.** `update_score` adds 5 points for a wrong "Too High" guess on even attempts (lines 57-60), and a win on the first guess pays 70 points instead of the full 100 (line 52 combined with the counter bug).
7. **Bad input is handled badly.** Text like "abc" uses up an attempt (line 148 counts before parsing), `50.9` is silently cut down to 50 (line 23), and out-of-range numbers like -2 or 5000 are accepted.
8. **The banner lags one click behind.** The "Attempts left" banner and the debug panel are drawn (lines 109-119) before the guess is processed (line 147), so they show the previous state.
9. **The starter tests cannot pass.** `logic_utils.py` only raises `NotImplementedError`, and the tests compare `check_guess(...)` to a plain string while the function is documented to return `(outcome, message)`.

**Bug Reproduction Log**

Row 1 is from my own first play-through. The other rows were reproduced with the secret pinned (you can also read the secret in the "Developer Debug Info" panel), so anyone can repeat them.

| Input Used | Expected Behavior | Actual Behavior | Console Error / Output | Suspected Code Location |
|------------|-------------------|-----------------|------------------------|-------------------------|
| Normal, secret 77. Guessed lower and lower following the hints, ending with `-2` | Hint says to go higher; `-2` is rejected as out of range | "📉 Go LOWER!" each time; `-2` accepted and cost an attempt; lost with score -35 | none | `app.py`, `check_guess` lines 37-40 (messages swapped); `parse_guess` has no range check |
| Secret 50, guess `60` | "Too High" outcome with a hint to go lower | "📈 Go HIGHER!" | none | `app.py`, `check_guess` lines 37-40 |
| Secret 50, guess `9` twice in a row | Same hint both times (go higher) | 1st submit: "📈 Go HIGHER!"; 2nd submit: "📉 Go LOWER!" | none (the `TypeError` is swallowed by `try/except`) | `app.py` lines 158-161 (secret cast to `str` on even attempts); `check_guess` lines 41-47 (string comparison) |
| Normal, fresh page, then 7 wrong guesses | Banner starts at "Attempts left: 8"; game ends after the 8th guess | Banner starts at "Attempts left: 7"; "Out of attempts!" after the 7th guess | none | `app.py` line 96 (`attempts = 1`) |
| Lose (or win) a game, click "New Game 🔁", submit a guess | A fresh game with attempts, history and status reset | Still shows "Game over. Start a new game to try again."; history and score kept | none | `app.py` lines 134-138 (`status` and `history` never reset) |
| Switch to Easy (range 1-20), click "New Game 🔁" several times | Banner says 1 to 20; secret is between 1 and 20 | Banner says "between 1 and 100"; secrets such as 97 | none | `app.py` line 110 (hardcoded text); line 136 (`random.randint(1, 100)`) |
| Secret 50, first guess `60`; separately, first guess `50` | Wrong guess never adds points; first-try win gives the top score (100) | Wrong guess: score goes 0 to +5; first-try win: "Final score: 70" | none | `app.py`, `update_score` lines 52 and 57-60 |
| Type `abc` and submit | Error message, no attempt used | "That is not a number." but attempts go from 1 to 2 | none | `app.py` line 148 (increments before `parse_guess`) |
| Secret 50, guess `50.9` | Rejected, a guess must be a whole number | "🎉 Correct!" and the game is won | none | `app.py`, `parse_guess` line 23 (`int(float(raw))`) |
| Run `pytest` | 3 starter tests pass | 3 failed | `NotImplementedError: Refactor this function from app.py into logic_utils.py` | `logic_utils.py` (stubs only); `tests/test_game_logic.py` compares a tuple to a string |

---

## 2. How did you use AI as a teammate?

- Which AI tools did you use on this project (for example: ChatGPT, Gemini, Copilot)?
- Give one example of an AI suggestion that was correct (including what the AI suggested and how you verified the result).
- Give one example of an AI suggestion you did not accept as written (including what the AI suggested, why you rejected or changed it, and how you verified your version). It does not have to be a suggestion that was wrong: over-engineered, out of scope, harder to read, or a poor fit for this codebase all count.

**Tools.** I used Claude Code inside VS Code, in agent mode. I gave it the assignment and it read the code, replayed the game with a pinned secret, edited `app.py` and `logic_utils.py`, wrote the tests and ran `pytest`. I gave it my own play-through (the game telling me to go lower when the secret was 77, and `-2` never being flagged as out of range), and it stopped to ask me before making the design decisions.

**A suggestion that was correct.** Claude Code said my "Go LOWER!" problem had two separate causes: the two hint messages in `check_guess` were swapped, and `app.py` was turning the secret into a string on every other attempt, so the numbers were being compared as text. It suggested swapping the messages, always passing the secret as an int, and deleting the `try/except TypeError` fallback that was hiding the mix-up. This was verified in three ways. `test_hints_from_my_first_game` replays my secret-77 game and now gets "Go HIGHER!". `test_same_guess_gets_the_same_hint_twice` submits 9 twice against a secret of 50 and gets the same hint both times. Both of those tests fail when they are run against the original starter code.

**A suggestion I did not accept as written.** The three starter tests compare `check_guess(60, 50)` to the string `"Too High"`, but the function returns a pair like `("Too High", "📉 Go LOWER!")`, so they fail even when the logic is right. One option Claude Code offered was to change `check_guess` to return only the outcome string, so the starter tests would pass untouched. I did not take that option. The docstring in `logic_utils.py` says the function returns `(outcome, message)` and `app.py` unpacks both values, so that change would have rewritten a documented contract and the app's call site just to satisfy three assertions. I kept the function as documented and had the three tests updated to unpack the pair instead. All 58 tests pass and the game still shows both the outcome and the hint.

---

## 3. Debugging and testing your fixes

- How did you decide whether a bug was really fixed?
- Describe at least one test you ran (manual or using pytest)  
  and what it showed you about your code.
- Did AI help you design or understand any tests? How?

**Deciding a bug was fixed.** I counted a bug as fixed only when a test that fails on the original code passes on the fixed code. Claude Code ran the new test suite against a copy of the starter code, where 30 of the 58 tests failed, and then against the fixed code, where all 58 pass. In the live game, entering `-2` now shows "Enter a number between 1 and 100." and the banner stays at "Attempts left: 8", where my first play-through accepted `-2` and charged me an attempt.

**One test and what it showed.** `test_same_guess_gets_the_same_hint_twice` in `tests/test_app_flow.py` drives the real app with Streamlit's `AppTest`: it pins the secret to 50 and submits `9` twice. On the original code the first submit said "Go HIGHER!" and the second said "Go LOWER!". On the fixed code both say "📈 Go HIGHER!". That showed me the flip-flopping hints came from `app.py` changing the secret's type between attempts, not from the comparison in `check_guess`.

**How AI helped with tests.** Claude Code wrote the tests, and two problems came out of checking them instead of trusting them. Its first version of the banner test passed on the buggy code too, because the off-by-one counter and the one-click-behind banner cancelled each other out and showed the right number by accident. It was rewritten to also check the attempt count in session state. Running plain `pytest`, the way the assignment says to, failed with `ModuleNotFoundError: No module named 'logic_utils'` even though `python -m pytest` worked, which is why the repo now has a `pytest.ini` that puts the project root on the import path.

---

## 4. What did you learn about Streamlit and state?

- How would you explain Streamlit "reruns" and session state to a friend who has never used Streamlit?

Streamlit runs your whole script from top to bottom again every time you click a button or change a widget. Normal variables are wiped on each rerun, so anything the game has to remember, like the secret number, the attempt count and the score, has to be stored in `st.session_state`, which works like a dictionary that survives reruns. This starter already kept the secret in session state, so the number itself never changed. What changed was its type, because the code turned it into a string on every other attempt. The rerun order also explained the stale banner: the banner was drawn near the top of the script, before the button click further down had been handled. The fix was to reserve its spot with `st.empty()` and fill it in at the end of the script, after the state was updated.

---

## 5. Looking ahead: your developer habits

- What is one habit or strategy from this project that you want to reuse in future labs or projects?
  - This could be a testing habit, a prompting strategy, or a way you used Git.
- What is one thing you would do differently next time you work with AI on a coding task?
- In one or two sentences, describe how this project changed the way you think about AI generated code.

**A habit to reuse.** Running new tests against the old, broken code before trusting them. A test that passes on the buggy version proves nothing, and that check is what exposed the weak banner test. I also want to keep making small commits per step (mark the bugs, fix, test, document) so the history shows how the work went.

**What I would do differently.** I would play the game for longer and write my own bug list before handing the code to the AI. I found the backwards hints and the missing range check by hand, and Claude Code found the rest by reading the code, so I can't tell how many of those I would have caught myself. I would also make sure one command has finished before the AI or I start another: during setup Claude Code started a second `pip install` while mine was still running, and it failed on a locked file.

**How this changed my view of AI-generated code.** This game never crashed or printed a single error, and at least nine things in it were still wrong. AI-generated code that runs is a draft to be tested, and the footer claiming it was "production-ready" is the kind of confident claim I now check before believing.
