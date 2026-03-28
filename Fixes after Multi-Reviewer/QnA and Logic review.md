# QA & Logic Review: MBTI Theory Quiz

Strict functional review of `quiz.py` against `SPEC.md`. Focus: logic errors, app flow, and functional bugs.

---

## Account & Authentication Flow

**1. [PASS] A new user can create an account and log in successfully**
`create_account()` (quiz.py lines 151–187) collects name, email, password, and MBTI type in the correct order. `login()` (lines 190–209) checks email then password. After account creation, the user flows directly into `main_menu()` (line 687). Users are freshly loaded from disk each iteration of the welcome loop (line 682), so newly created accounts are always findable.

**2. [PASS] Passwords are hashed using hashlib and are not readable in `users.dat`**
`hash_password()` (lines 113–118) uses `hashlib.pbkdf2_hmac("sha256", ...)` with a random 16-byte salt. The hash+salt are stored as hex strings. `users.dat` is saved as zlib-compressed JSON (line 77), making it non-human-readable. Plaintext passwords are never persisted.

**3. [PASS] Login with non-existent email returns to menu**
Line 194: `if email not in users:` prints `"Email not found. Please try again."` and returns `None`, sending the user back to the welcome menu (line 690–691). Matches spec.

**4. [PASS] Wrong password says "wrong password, try again"**
Lines 203–205: On failed password, prints `"Wrong password. {remaining} attempt(s) remaining."` Correctly loops up to 3 attempts before returning to menu.

**5. [WARN] Login attempt limit of 3 is not specified in `SPEC.md` — quiz.py line 38**
`MAX_LOGIN_ATTEMPTS = 3` adds a lockout mechanism. The spec says only `"if the password is wrong, it just says wrong password try again"` — implying unlimited retries. The implementation adds a hard cap of 3 attempts. Not a crash or logic error, but a deviation from spec behavior.

**6. [PASS] Empty-field validation on account creation**
Lines 154–170: Name, email, and password are all validated for empty strings with `.strip()`, and the function returns `None` (back to menu) if any are blank.

---

## Invalid Input / Error Handling

**7. [PASS] String instead of int on menu does not crash**
`get_int_input()` (lines 131–144) wraps `int(input(...))` in `try/except ValueError` and loops with `"Invalid input. Please enter a number."`. Every menu and quiz choice uses this helper. Verified at lines 176, 277, 351, 393, 463, 567, 636, 680.

**8. [PASS] Missing or corrupted `questions.json` prints error and exits code 1**
`load_questions()` (lines 46–52) catches `FileNotFoundError`, `json.JSONDecodeError`, and `KeyError`, prints `"Oops, can't find the questions file!"`, and calls `sys.exit(1)`. Matches spec exactly.

**9. [PASS] Mid-use deletion of `users.dat` or `scores.dat` is handled gracefully**
`_load_dat()` (lines 63–71) catches `FileNotFoundError`, `EOFError`, `zlib.error`, and `json.JSONDecodeError`, returning `{}`. `_save_dat()` (lines 74–77) writes with `"wb"` mode, recreating the file if absent. The app won't crash.

**10. [WARN] `_save_dat()` has no error handling for write failures — quiz.py lines 74–77**
If a disk-full or permission error occurs during `_save_dat()`, the unhandled `OSError` would crash the app. The spec says the app should recover from missing files, but write-path errors are unguarded.

---

## Sequential Quiz Flow

**11. [PASS] Sequential order matches spec exactly**
`SECTION_ORDER` (lines 15–21) is `["MBTI Basics", "Cognitive Functions", "Stereotypes", "MBTI Behaviors", "Traits to Look For"]`. Matches SPEC.md line 14 word-for-word.

**12. [PASS] Sequential quiz skips completed sections**
`next_section()` (lines 364–369) iterates `SECTION_ORDER` and returns the first section NOT present in `scores_data[email]`. Any section completed via browse or sequential play is in `scores_data`, so it gets skipped.

**13. [PASS] Completing all sections shows appropriate message**
Line 641: When `next_section()` returns `None`, the app prints `"You've completed all sections! Use 'Browse All Quizzes' to retake any."` and loops back to the menu. No crash.

**14. [WARN] If a section has zero questions in `questions.json`, the user gets permanently stuck — quiz.py lines 258–260**
`run_quiz()` returns `(None, None)` when no questions match the section. The `if correct is not None` guard (line 645) prevents score update, so the section is never marked done. `next_section()` would return this same empty section on every "Start Next Quiz" call forever, trapping the user in an infinite loop of empty quizzes. Not a bug with the current `questions.json` (which has 5 per section), but a latent logic flaw if the data file is edited.

---

## Quiz Engine & Answering

**15. [PASS] Case-insensitive short answer — both "intj" and "INTJ" accepted**
Line 302: `if answer.lower() == q["answer"].lower():` — both user input and stored answer are lowercased before comparison. Verified in all three quiz functions (`run_quiz` line 302, `review_quiz` line 488, `filtered_quiz` line 592). Matches spec.

**16. [PASS] True/false answers handled case-insensitively with shortcuts**
Lines 286–295: Input is lowered, then matched against `("t", "true", "f", "false")`. Comparison against stored answer also uses `.lower()`.

**17. [WARN] True/false and short-answer input loops have no exit or skip path — quiz.py lines 286–294**
The `while True` loop for true/false questions only breaks on valid input. There is no way to skip a question or abort the quiz mid-section. If the user is stuck, their only option is to kill the process. The spec says the quiz must be "completed first" before seeing results, so forcing completion is arguably intended, but there is no "quit quiz" escape hatch anywhere.

**18. [PASS] Multiple-choice input validation is bounded correctly**
Line 277: `get_int_input("Your answer (number): ", 1, len(q["options"]))` — bounds are dynamic based on the actual number of options. Out-of-range or non-numeric input loops with a message.

**19. [PASS] Question display shows number, category, question, and answering instructions**
Lines 271–277 (multiple choice), 284–285 (true/false), 300–301 (short answer): Each question shows `Question {i}/{total} [{section}]`, the question text, and either numbered options, a `"Type 'true' or 'false'"` hint, or a plain `"Your answer:"` prompt. Matches spec requirement: "the user will see what question number they are on, the category, the question itself, and how to answer."

---

## Scoring & Retakes

**20. [PASS] Score tracking: correct vs total per section with percentage**
`run_quiz()` lines 266–267 track `correct` and `total`. Line 307: `pct = round(correct / total * 100)`. `update_score()` (lines 330–345) stores `{"correct": ..., "total": ...}` per section per user. Matches spec.

**21. [PASS] Cumulative score across all completed sections**
`show_dashboard()` lines 223–240 sum `total_correct` and `total_questions` across all completed sections and display an overall percentage. Matches spec.

**22. [PASS] Retaking a section keeps the higher score**
`update_score()` line 337: `if correct > old_correct:` — only overwrites if the new score is strictly higher. Otherwise prints `"Previous score was higher ... Keeping it."` Matches spec: "the higher score is kept."

**23. [WARN] Retake score comparison uses raw count, not percentage — quiz.py line 337**
`if correct > old_correct:` compares absolute correct counts. If `questions.json` were edited between attempts (changing the number of questions per section), a user could score 3/3 (100%) on a retake but have it rejected because their old score of 4/5 has a higher raw count. With the current static data file this cannot happen, but the comparison should ideally use `correct/total` ratio for correctness.

---

## Post-Section Results & Tips

**24. [PASS] End-of-section display shows score, missed answers, and tip in correct order**
Lines 309–325: After the quiz loop, the code prints (1) the final score, (2) iterates `missed` to show each wrong answer with the correct one, then (3) displays a personalized tip. Order matches spec: "the final score, a list of what the right answers were for the ones they missed, and then the personalized tip."

**25. [PASS] Personalized tip matches user's MBTI from profile**
Line 323: `if user_mbti in tips and tips[user_mbti]:` — looks up the user's MBTI type (passed from `user["mbti"]`) in `tips.json`. Line 324: `random.choice(tips[user_mbti])` picks a random tip from the list. `tips.json` covers all 16 types with 6 tips each.

**26. [PASS] Tips loaded from separate `tips.json`, not hardcoded**
`load_tips()` (lines 55–60) reads from `tips.json`. No tips are hardcoded in `quiz.py`. Matches spec: "the tips will live in a separate JSON file."

**27. [PASS] Missing `tips.json` degrades gracefully (no crash)**
`load_tips()` line 60: Returns `{}` on `FileNotFoundError` or `json.JSONDecodeError`. The tip display guard (line 323) prevents errors when the dict is empty. The app runs without tips instead of crashing.

---

## Feedback System

**28. [PASS] Rating prompt appears right after section score**
`rate_section()` (lines 348–357) is called immediately after `update_score()` in both the sequential path (line 647) and browse path (line 403). It prompts `"Rate this section (1-5 stars):"` and saves to `feedback.json`. Matches spec.

**29. [PASS] Feedback ratings are used for weighting in review mode**
`review_quiz()` (lines 410–511) reads `user_feedback` (line 413), uses ratings as weights (lines 430–431), and performs weighted random selection (lines 436–446). Questions from higher-rated sections are more likely to appear. Matches spec: "Questions from highly-rated sections get weighted more in any 'random quiz' or review mode."

**30. [WARN] `review_quiz` builds a redundant `weighted_pool` then discards it — quiz.py lines 420–427**
Lines 420–425 construct `weighted_pool` by repeating questions proportional to their rating. Then line 427 deduplicates into `unique_qs` via a dict comprehension, completely discarding the repetition-based weighting. The actual weighting is re-applied separately at lines 430–431 using a different mechanism. The `weighted_pool` construction (5 lines of code) does nothing useful. Not a correctness bug, but dead/misleading logic.

---

## Browse Quizzes

**31. [PASS] Browse shows all sections with [DONE] marker and scores**
`browse_quizzes()` lines 383–389: Iterates `SECTION_ORDER`, prints `[DONE]` with score/percentage for completed sections and `[    ]` for incomplete ones. Matches spec.

**32. [PASS] Taking a quiz out of order via browse updates score and removes it from sequential lineup**
`browse_quizzes()` line 402: `update_score()` saves the result. `next_section()` (line 366) checks `scores_data` and skips completed sections. Since browse writes to the same `scores_data` dict, the sequential lineup correctly skips any section done out of order.

**33. [PASS] Browse allows retaking completed sections**
The browse menu lists all sections regardless of completion status. A user can select a `[DONE]` section and retake it. `update_score()` handles the higher-score logic. Matches spec: "Users can retake a completed section if they want to."

---

## Dashboard

**34. [PASS] Dashboard shows stats, completed sections, scores, and skills learned**
`show_dashboard()` (lines 216–249): Shows `[DONE]` or `[    ]` per section, individual scores with percentages, cumulative score, sections completed count, and skill names via `SKILL_MAP`. Matches spec: "users are able to see their stats, how many quizzes they have successfully completed, what skills they have already learned."

---

## Extension Feature

**35. [PASS] Category-based filtering is implemented**
`filtered_quiz()` (lines 518–615) lets the user pick one or more categories by number (comma-separated) or type `"all"`, then runs a shuffled quiz on matching questions. This is menu option 4 ("Filter by Category") and satisfies SPEC.md line 96: "Extension Feature: Category-based filtering."

**36. [WARN] `filtered_quiz()` does not save scores or prompt for feedback — quiz.py lines 518–615**
Unlike the sequential and browse quiz paths, `filtered_quiz()` does not call `update_score()` or `rate_section()`. Scores from filtered quizzes are displayed but never persisted. If a user takes a filtered quiz, their results vanish after viewing. The spec doesn't explicitly require it, but it is inconsistent with all other quiz paths.

---

## Data Format & File Structure

**37. [PASS] `questions.json` format matches spec**
Each question has `question`, `type`, `options` (for MC), `answer`, and `category`. All three types (`multiple_choice`, `true_false`, `short_answer`) are represented. 25 questions across 5 categories, 5 per section. Matches spec.

**38. [PASS] `tips.json` format matches spec**
Structure is `{"INTJ": [...], "INTP": [...], ...}` with all 16 MBTI types covered. Matches SPEC.md line 68.

**39. [PASS] File structure matches spec**
Project contains `quiz.py`, `questions.json`, `users.dat`, `scores.dat`, `feedback.json`, `tips.json` as required.

**40. [WARN] `users.dat`/`scores.dat` use zlib+JSON instead of pickle/shelve — quiz.py lines 63–77**
SPEC.md line 64 says `"Non-human-readable format (using pickle or shelve from Python's standard library)"`. The code uses `zlib.compress(json.dumps(...))` instead. This is arguably a better design (avoids pickle deserialization attacks), and the files are indeed non-human-readable, but it technically deviates from the spec's explicit "pickle or shelve" instruction.

---

## Edge Cases & Robustness

**41. [PASS] `review_quiz` requires at least one completed section**
Lines 416–417: `if not completed: print(...); return`. Prevents running a review quiz with an empty pool.

**42. [PASS] `review_quiz` guards against division by zero**
Line 493: `pct = round(correct / total * 100) if total > 0 else 0`. If the selected pool is somehow empty, no crash occurs.

**43. [WARN] `review_quiz` can produce 0 review questions silently — quiz.py lines 428, 456**
If all completed sections have had their questions removed from `questions.json`, `unique_qs` would be empty and `review_size = min(5, 0) = 0`. The code would print `"Review Complete! You scored 0/0 (0%)"` — functional but confusing with no explanation of why zero questions appeared.

**44. [WARN] Keyboard interrupt (Ctrl+C) and EOF (Ctrl+D) are unhandled throughout**
Every `input()` call will raise `KeyboardInterrupt` or `EOFError` if the user presses Ctrl+C or Ctrl+D. These are uncaught, producing a raw Python traceback. The spec only mentions "typing letters instead of a number" as the invalid input case, so this is technically out of scope, but it is a common robustness concern for terminal apps.

---

## Summary

| Verdict | Count |
|---------|-------|
| PASS    | 28    |
| FAIL    | 0     |
| WARN    | 10    |

The code correctly implements all 7 explicit acceptance criteria from SPEC.md:

1. Account creation and login work correctly.
2. Missing `questions.json` prints a friendly error and exits with code 1.
3. Non-numeric menu input does not crash the app.
4. Passwords are hashed with `hashlib` and not readable in `users.dat`.
5. Both `"intj"` and `"INTJ"` are accepted for short-answer questions.
6. Taking a quiz out of order via browse updates the score and removes it from the sequential lineup.
7. A personalized MBTI tip is displayed at the end of each completed section.

The 10 WARN items break down as:

- **Spec deviations** (not bugs): Login attempt cap (#5), zlib instead of pickle (#40).
- **Latent edge cases** (only triggered by editing data files): Empty section infinite loop (#14), raw-count score comparison (#23), silent zero-question review (#43).
- **Missing persistence**: Filtered quiz scores not saved (#36).
- **Dead logic**: Redundant weighted pool construction (#30).
- **Robustness gaps**: No write-error handling (#10), no Ctrl+C handling (#44), no mid-quiz exit path (#17).

No outright logic errors or functional bugs were found in the core quiz flow under normal usage conditions.
