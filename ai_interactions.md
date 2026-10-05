# AI Interactions Log

> **Stretch features only.** Only fill in the sections that apply to stretch features you attempted. If you did not attempt a stretch feature, leave its section blank or delete it. This file is not required for the core project.

---

## Agent Workflow (SF8)

> Document your experience using an AI agent (e.g., Cursor Agent, Claude, Copilot) to make multi-step changes autonomously.

**What task did you give the agent?**

I used Claude Code (the VS Code extension) in agent mode. I pasted in the full project instructions and asked it to do the project and make sure the game works well. While it worked I sent it two more messages: a screenshot and description of my own first game (the hints said "Go LOWER!" all the way down to `-2`, nothing said I was out of range, and the secret turned out to be 77), and an instruction to fix the code first and fill in `reflection.md` afterwards.

**What did the agent do?**

1. Read `app.py`, `logic_utils.py`, the starter tests, `README.md` and `reflection.md`.
2. Replayed the original game headlessly with Streamlit's `AppTest`, pinning the secret to 50 so each bug could be repeated, and ran the starter tests (3 failed with `NotImplementedError`).
3. Stopped and asked me four questions before editing anything: whether to fix the starter tests or change `check_guess`, what to do about Hard mode's range, whether to push to GitHub, and whether to do stretch work.
4. Added `# FIXME` comments at each suspected bug location in `app.py` and committed them.
5. Moved the four logic functions into `logic_utils.py`, fixed them, and reworked the state handling in `app.py` (one `start_new_game()` helper, placeholders for the banner and debug panel). Committed.
6. Wrote `tests/test_game_logic.py` and `tests/test_app_flow.py`, added `pytest.ini`, and ran the suite against both the fixed code and a copy of the original code.
7. Opened the running app in Chrome and submitted `-2` to check the live game.
8. Had a second reviewer agent read the diff for remaining bugs. It found that `float()` rounded `49.99999999999999999` up to 50, that the hint and final score disappeared on the next click, and that five behaviours in `app.py` had no test. Claude Code fixed the two bugs, added the missing tests, and committed.
9. Wrote `reflection.md`, `README.md` and this log, then committed and pushed.

**What did you have to verify or fix manually?**

- The course command `python3 -m venv .venv` failed on my Windows machine with "Python was not found". Claude Code switched to `py -m venv .venv`, which worked.
- Claude Code started a second `pip install` while my own was still running, and it failed with `[WinError 32] The process cannot access the file because it is being used by another process`. I had to let my install finish.
- Its first banner test passed on the buggy code as well, because the off-by-one counter and the stale banner cancelled each other out. That only showed up when the tests were run against the original code, and the test was rewritten.
- Plain `pytest` failed with `ModuleNotFoundError: No module named 'logic_utils'` even though `python -m pytest` passed, so `pytest.ini` was added.
- The browser check only got as far as the first screen and one guess, because the Chrome window was resized partway through. Playing a full game in the live app was left to me.
- The design decisions were mine: keep `check_guess` returning `(outcome, message)` and fix the tests, and widen Hard to 1-200.

---

## Test Generation (SF7)

> Document how you used AI to help generate or improve tests.

I did not write a separate prompt for each test. Claude Code asked whether I wanted extra tests for odd inputs (decimals, negatives, text, out-of-range) and I picked that option. The out-of-range tests came from my own bug report.

| Edge Case | Prompt Used | AI-Suggested Test | Did It Pass? | Your Reasoning |
|-----------|-------------|-------------------|--------------|----------------|
| Negative and out-of-range numbers (`-2`, `0`, `101`, `5000`) | "even when i was in the negatives it never showed something like out of range" (my bug report) | `test_parse_rejects_guess_outside_range`: `parse_guess(raw, 1, 100)` returns `(False, None, "Enter a number between 1 and 100.")` | Yes. Fails on the original code | This is the glitch from my first game, where `-2` was accepted and cost me an attempt |
| Decimals (`50.9`, `0.5`, `-3.14`) | Chose the "Edge-case tests" option Claude Code offered | `test_parse_rejects_decimals`: returns `(False, None, "Enter a whole number.")` | Yes. Fails on the original code | The original cut `50.9` down to 50, so a decimal could win the game |
| Extremely large numbers (400 and 5000 digits) | Same option | `test_parse_rejects_extremely_large_number`: `parse_guess("9" * digits, 1, 100)` returns the out-of-range message | Yes. Fails on the original code | A huge number should get a normal error message and must not crash or hang the game |
| Decimal that rounds to a whole number (`49.99999999999999999`) | Came from the reviewer agent's report | `test_parse_rejects_decimal_that_float_would_round_to_50`: returns "Enter a whole number." | Yes. Failed on the first version of the fix | `float()` turns this into exactly 50.0, so the first fix let it win. Switching to `Decimal` closed the gap |
| Text and non-numbers (`abc`, `12abc`, `nan`, `inf`) | Same option | `test_parse_rejects_non_numbers` | Yes | `float()` accepts `nan` and `inf`, so I wanted proof they are rejected |
| Empty or whitespace-only input | Same option | `test_parse_empty_input`: returns "Enter a guess." | Yes. The whitespace case fails on the original code | Pressing Submit with nothing typed should ask for a guess |
| Both ends of the range (`1`, `100`) | Same option | `test_parse_accepts_both_ends_of_range` | Yes | A range check is easy to get off by one, so the edges need their own test |
| Same guess twice in a row (secret 50, guess `9`) | Came out of Claude Code replaying the game | `test_same_guess_gets_the_same_hint_twice` in `tests/test_app_flow.py` | Yes. Fails on the original code | It is the only way to catch the secret changing type between attempts, which the logic tests cannot see |
