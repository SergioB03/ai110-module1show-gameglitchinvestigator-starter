# 💭 Reflection: Game Glitch Investigator

Answer each question in 3 to 5 sentences. Be specific and honest about what actually happened while you worked. This is about your process, not trying to sound perfect.

## 1. What was broken when you started?

- What did the game look like the first time you ran it?
- List at least two concrete bugs you noticed at the start  
  (for example: "the hints were backwards").

**First run.** The app loaded without errors and looked like a normal number guessing game, but I could not win by following the hints. The secret was 77, yet the hints kept saying "Go LOWER!", even when I typed -2, and nothing told me I was out of range. I ran out of attempts with a score of -35. The banner still said "Attempts left: 1" right above the "Out of attempts!" message.

This is what the screen showed at the end of that game (Normal difficulty):

```
Guess a number between 1 and 100. Attempts left: 1
Enter your guess: -2
📉 Go LOWER!
Out of attempts! The secret was 77. Score: -35
```

**Bugs I noticed.** Line numbers are from the starter `app.py`, before any edits.

1. **Backwards hints.** Expected: a guess below the secret gets a hint to go higher. Actual: it said "📉 Go LOWER!". Cause: `check_guess` (lines 37-40) has the two hint messages swapped.
2. **No range check.** Expected: `-2` is rejected as out of range. Actual: it was accepted and cost me an attempt. Cause: `parse_guess` (lines 14-29) never compares the guess with the range.
3. **Hints that flip.** Expected: the same guess gets the same hint. Actual: with a secret of 50, guessing `9` twice gave "Go HIGHER!" and then "Go LOWER!". Cause: lines 158-161 turn the secret into a string on every other attempt, so the numbers are compared as text.

I found the first two by playing. Claude Code found the third and the other bugs in the log below. The [README](README.md) lists every bug and its fix.

**Bug Reproduction Log**

Row 1 is my own first game. The other rows use a known secret (it is shown in the "Developer Debug Info" panel), so anyone can repeat them.

| Input Used | Expected Behavior | Actual Behavior | Console Error / Output | Suspected Code Location |
|------------|-------------------|-----------------|------------------------|-------------------------|
| My first game: Normal, secret 77, guesses going lower, ending with `-2` | Hint says go higher; `-2` rejected as out of range | "📉 Go LOWER!" each time; `-2` accepted; lost with score -35 | none | `check_guess` lines 37-40 (messages swapped); `parse_guess` lines 14-29 (no range check) |
| Secret 50, guess `60` | Hint to go lower | "📈 Go HIGHER!" | none | `check_guess` lines 37-40 |
| Secret 50, guess `9` twice | Same hint both times | "📈 Go HIGHER!", then "📉 Go LOWER!" | none (the `TypeError` is swallowed by `try/except`) | lines 158-161 (secret cast to `str` on even attempts); `check_guess` lines 41-47 |
| Normal, fresh page, then 7 wrong guesses | "Attempts left: 8" at the start; game over after the 8th guess | "Attempts left: 7" at the start; game over after the 7th guess | none | line 96 (`attempts = 1`) |
| Finish a game, click "New Game 🔁", submit a guess | A fresh game | Stuck on "Game over" (or "You already won"); history and score kept | none | lines 134-138 (`status` and `history` never reset) |
| Easy (range 1-20), click "New Game 🔁" a few times | Banner says 1 to 20; secret between 1 and 20 | Banner says "between 1 and 100"; secrets such as 97 | none | line 110 (hardcoded text); line 136 (`random.randint(1, 100)`) |
| Secret 50: first guess `60`; separately, first guess `50` | A wrong guess never adds points; a first-try win scores 100 | Wrong guess: score goes from 0 to +5; first-try win: "Final score: 70" | none | `update_score` lines 52 and 57-60 |
| Normal, secret 50: guess `1` six times, then `50` | The score never goes below zero | Score falls to -30, then "You won! The secret was 50. Final score: -20" | none | `update_score` lines 60 and 63 (no lower limit) |
| Type `abc` and submit | Error message, no attempt used | "That is not a number.", but attempts go from 1 to 2 | none | line 148 (counts the attempt before `parse_guess`) |
| Secret 50, guess `50.9` | Rejected, because it is not a whole number | "🎉 Correct!" and the game is won | none | `parse_guess` line 23 (`int(float(raw))`) |
| Win a game, then untick "Show hint" | The win message and final score stay on screen | Replaced by "You already won. Start a new game to play again." | none | lines 140-145 and 174-180 (drawn only on the Submit rerun) |
| Run `python -m pytest` | 3 starter tests pass | 3 failed (plain `pytest` fails earlier, on import) | `NotImplementedError: Refactor this function from app.py into logic_utils.py`. Plain `pytest`: `ModuleNotFoundError: No module named 'logic_utils'` | `logic_utils.py` (stubs only); the tests compare a tuple to a string; no `pytest.ini` |

---

## 2. How did you use AI as a teammate?

- Which AI tools did you use on this project (for example: ChatGPT, Gemini, Copilot)?
- Give one example of an AI suggestion that was correct (including what the AI suggested and how you verified the result).
- Give one example of an AI suggestion you did not accept as written (including what the AI suggested, why you rejected or changed it, and how you verified your version). It does not have to be a suggestion that was wrong: over-engineered, out of scope, harder to read, or a poor fit for this codebase all count.

**Tools.** I used Claude Code inside VS Code, in agent mode. It read the code, replayed the game with a known secret, edited `app.py` and `logic_utils.py`, wrote the tests and ran `pytest`. I gave it my own play-through and made the design decisions it stopped to ask me about, such as the range for Hard mode.

**A suggestion that was correct**

- *What the AI suggested:* Claude Code explained that my "Go LOWER!" problem had two causes: the two hint messages in `check_guess` were swapped, and `app.py` turned the secret into a string on every other attempt. It suggested swapping the messages and always comparing the secret as an int.
- *Why it was correct:* Both causes were real. With only the messages swapped, a guess of `9` against a secret of 50 would still get the wrong hint on every other attempt.
- *How I verified it:* `test_hints_from_my_first_game` replays my secret-77 game and gets "Go HIGHER!", and `test_same_guess_gets_the_same_hint_twice` gets the same hint for `9` twice. Both tests fail on the starter code and pass on the fixed code.

**A suggestion I did not accept as written**

- *What the AI suggested:* Claude Code's first scoring fix made every wrong guess cost 5 points with no lower limit. It told me a win on the last attempt could then show a negative final score (-5 on Normal), and it had left that as it was.
- *Why I changed it:* My own first game had ended at -35 and I did not want the score to go below zero, so I asked for it to stop at 0.
- *How I verified my version:* For a wrong guess, `update_score` now returns `max(0, current_score - 5)`. `test_lost_game_ends_with_a_score_of_zero` and `test_win_on_the_last_attempt_shows_a_positive_final_score` fail on the earlier version and pass now: a lost game ends at 0, and a last-attempt win shows "Final score: 30".

---

## 3. Debugging and testing your fixes

- How did you decide whether a bug was really fixed?
- Describe at least one test you ran (manual or using pytest)  
  and what it showed you about your code.
- Did AI help you design or understand any tests? How?

**How I decided a bug was fixed.** A bug counted as fixed only when a test that fails on the starter code passes on the fixed code. Run against the starter code, 49 of the 79 tests fail. On the fixed code all 79 pass. In the live game, `-2` now shows "Enter a number between 1 and 100." and no attempt is used.

**One test and what it showed.** `test_same_guess_gets_the_same_hint_twice` in `tests/test_app_flow.py` sets the secret to 50 and submits `9` twice through Streamlit's `AppTest`. The starter code answered "Go HIGHER!" and then "Go LOWER!". The fixed app says "📈 Go HIGHER!" both times. That showed me the flipping hints came from `app.py` changing the secret's type between attempts, not from the comparison in `check_guess`.

**How AI helped with tests.** Claude Code wrote the tests, and checking them mattered more than trusting them. Its first test of the "Attempts left" banner also passed on the starter code, because two bugs cancelled out: the attempt counter started one too high, and the stale banner showed the count from before the click. It was rewritten to check the attempt count in session state as well. A review by a second Claude agent then found two bugs the first round of fixes had missed: `49.99999999999999999` was rounded up to 50, and the final score vanished on the next click. Each one got a fix and a test.

---

## 4. What did you learn about Streamlit and state?

- How would you explain Streamlit "reruns" and session state to a friend who has never used Streamlit?

Streamlit runs your whole script again, from top to bottom, every time you click a button or change a widget. Ordinary variables are reset on each rerun, so anything the game has to remember (the secret, the attempt count, the score) must be stored in `st.session_state`, which works like a dictionary that survives reruns. In this game the secret was already in session state, so the number never changed. The bug was that the code turned it into a string on every other attempt. The rerun order also caused the stale banner: it was drawn near the top of the script, before the button click further down was handled, so it is now filled in at the end.

---

## 5. Looking ahead: your developer habits

- What is one habit or strategy from this project that you want to reuse in future labs or projects?
  - This could be a testing habit, a prompting strategy, or a way you used Git.
- What is one thing you would do differently next time you work with AI on a coding task?
- In one or two sentences, describe how this project changed the way you think about AI generated code.

**A habit to reuse.** Run new tests against the old, broken code before trusting them. A test that also passes on the buggy version proves nothing, and that check is what exposed the weak banner test. I will also keep making one small commit per step (mark the bugs, fix, test, document).

**What I would do differently.** I would play the game for longer and write my own bug list before handing the code to the AI. I found the backwards hints and the missing range check by hand and Claude Code found the rest, so I cannot tell how many I would have caught myself. I would also let my command finish before the AI starts another: during setup Claude Code started a second `pip install` while mine was still running, and it failed on a locked file.

**How this changed my view of AI-generated code.** This game never crashed or printed an error, and at least ten things in it were still wrong. AI-generated code that runs is a draft that still has to be tested.
