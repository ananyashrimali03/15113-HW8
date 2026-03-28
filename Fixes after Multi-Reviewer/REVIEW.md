# Code Review: MBTI Theory Quiz

## Acceptance Criteria

**1. [PASS] A new user can create an account and log in successfully**
`create_account()` (quiz.py lines 120-146) collects name, email, password, and MBTI type, hashes the password, saves via pickle, and returns the email. `login()` (lines 149-164) checks email existence and hashed password. After account creation, the user flows directly into `main_menu()` (line 426). Login re-loads users from disk each iteration (line 421), so freshly created accounts are always found.

**2. [PASS] Running the app with a missing questions.json prints an error and exits with code 1**
`load_questions()` (lines 35-42) catches `FileNotFoundError`, `json.JSONDecodeError`, and `KeyError`, prints `"Oops, can't find the questions file!"`, and calls `sys.exit(1)`.

**3. [PASS] A user entering a string instead of an int on the menu gets asked to try again**
`get_int_input()` (lines 100-113) wraps `int(input(...))` in a try/except `ValueError` and loops with `"Invalid input. Please enter a number."`. Every menu and quiz choice in the app uses this helper.

**4. [PASS] Passwords are hashed using hashlib and are not readable in users.dat**
`hash_password()` (lines 96-97) uses `hashlib.sha256`. The hash is stored in the user dict (line 141), which is serialized with `pickle` to a binary `.dat` file. Plaintext passwords are never persisted.

**5. [PASS] Typing "intj" or "INTJ" both work for short answer questions**
In `run_quiz()`, line 260: `if answer.lower() == q["answer"].lower():` — both sides are lowercased before comparison.

**6. [PASS] Taking a quiz out of order in browse updates score and removes it from sequential lineup**
`browse_quizzes()` (lines 334-362) lets the user pick any section and run it. `update_score()` writes the result into `scores_data[email][section]`. `next_section()` (lines 322-327) iterates `SECTION_ORDER` and skips any section already in `scores_data`, so completed browse-quizzes are removed from the sequential lineup.

**7. [PASS] At the end of a completed section, a personalized MBTI tip is displayed**
`run_quiz()` lines 281-283 check `if user_mbti in tips and tips[user_mbti]` and display a `random.choice(...)` from the matching list. `tips.json` contains entries for all 16 MBTI types.

---

## Additional Spec Requirements

**8. [PASS] Sequential quiz order matches spec**
`SECTION_ORDER` (lines 15-21) is `["MBTI Basics", "Cognitive Functions", "Stereotypes", "MBTI Behaviors", "Traits to Look For"]`, exactly matching the spec.

**9. [PASS] 5 questions per section**
`questions.json` contains exactly 5 questions for each of the 5 categories (25 total), matching the spec's "5 questions per section."

**10. [PASS] Dashboard shows stats, completed sections, and skills learned**
`show_dashboard()` (lines 171-211) prints each section with `[DONE]` or `[    ]`, individual section scores and percentages, cumulative score, sections completed count, and a skill name for each completed section.

**11. [PASS] Retaking a section keeps the higher score**
`update_score()` (lines 288-303) compares `correct > old_correct` and only overwrites if the new score is higher. Otherwise it prints `"Previous score was higher ... Keeping it."`.

**12. [PASS] Feedback/rating prompt after each section**
`rate_section()` (lines 306-315) is called immediately after `update_score()` in both the sequential path (line 391) and browse path (line 361). It prompts for a 1-5 star rating and saves to `feedback.json`.

**13. [PASS] File structure matches spec**
The project contains exactly the files listed: `quiz.py`, `questions.json`, `users.dat`, `scores.dat`, `feedback.json`, `tips.json`.

**14. [PASS] Data format for questions.json matches spec**
Each question object has `question`, `type`, `options` (for MC), `answer`, and `category`. The three question types (`multiple_choice`, `true_false`, `short_answer`) are all represented.

**15. [PASS] tips.json format matches spec**
Structure is `{"INTJ": ["tip1", "tip2", ...], ...}` with all 16 MBTI types covered (3 tips each).

**16. [PASS] Mid-use deletion of users.dat or scores.dat is handled**
`load_users()` and `load_scores()` return `{}` on `FileNotFoundError`. `save_users()` and `save_scores()` open with `"wb"` mode, which creates the file if absent. The app won't crash.

---

## Bugs and Logic Errors

**17. [FAIL] Feedback ratings are collected but never used for weighting — `quiz.py`**
The spec states: *"Questions from highly-rated sections get weighted more in any 'random quiz' or review mode."* `feedback.json` is written to (line 314) but never read back for any logic purpose. There is no random quiz or review mode. The `load_feedback()` return value in `main_menu()` (line 370) is only passed through to `rate_section()` for appending; it is never consumed for quiz selection or question weighting. This is an unimplemented spec requirement.

**18. [WARN] No "random quiz" or review mode exists — `quiz.py`**
The spec describes feedback weighting as part of a "random quiz or review mode." Neither mode is implemented. The only quiz paths are sequential (option 1) and browse (option 2).

**19. [WARN] Extension feature "Category-based filtering" is not clearly implemented — `quiz.py`**
The spec lists *"Extension Feature: Category-based filtering"* (SPEC.md line 96). The browse menu lets users pick a section by category, which could be interpreted as category filtering, but there is no dedicated filtering UI, search, or filter-by-category feature beyond what the basic browse menu already provides.

---

## Missing Error Handling

**20. [WARN] No input validation on account fields — `quiz.py` lines 122-129**
`name`, `email`, and `password` accept any string, including empty strings. A user can create an account with `name=""`, `email=""`, `password=""`. The spec doesn't explicitly require validation, but this leads to confusing behavior (e.g., logging in with an empty email).

**21. [WARN] true/false input loop has no exit path — `quiz.py` lines 248-252**
The `while True` loop for true/false questions only breaks when the user types exactly `"true"` or `"false"`. There is no way to skip or quit. If the user is stuck, their only option is to kill the process. This contrasts with `get_int_input()` which at least has range bounds. Minor usability concern.

---

## Code Quality

**22. [WARN] `skill_map` is hardcoded inside a function — `quiz.py` lines 200-206**
The `skill_map` dictionary inside `show_dashboard()` maps section names to skill names. This should be a module-level constant alongside `SECTION_ORDER` to avoid recreating it on every dashboard render and to keep configuration together.

**23. [WARN] `browse_quizzes` reloads scores redundantly — `quiz.py` line 395**
After `browse_quizzes()` returns, `main_menu()` reloads `scores_data = load_scores()` (line 395). But `browse_quizzes()` already modified `scores_data` in place via `update_score()` and saved it. The reload is safe but unnecessary — the in-memory dict is already up to date.

**24. [PASS] Code is well-structured overall**
Functions are single-purpose, naming is clear (`load_questions`, `run_quiz`, `update_score`, etc.), and the file is organized with section comments. No significant code duplication.

---

## Security Concerns

**25. [WARN] SHA-256 password hashing without salt — `quiz.py` line 97**
`hashlib.sha256(password.encode()).hexdigest()` produces unsalted hashes, making them vulnerable to rainbow-table attacks. Two users with the same password will have identical hashes. The spec only requires *"hashed using hashlib"* (which is met), but best practice is to use `hashlib.pbkdf2_hmac` or `bcrypt` with a per-user salt.

**26. [WARN] `pickle` deserialization is inherently unsafe — `quiz.py` lines 55-57, 67-69**
`pickle.load()` can execute arbitrary code if the `.dat` file is tampered with. The spec explicitly calls for pickle/shelve, so this is by design, but it remains a real attack vector. An alternative like `shelve` or `json` with manual encoding would be safer.

**27. [WARN] No login attempt rate-limiting — `quiz.py` lines 149-164**
A user can attempt login indefinitely with no delay or lockout, making brute-force attacks trivial against the unsalted SHA-256 hashes.

---

## Summary

| Verdict | Count |
|---------|-------|
| PASS    | 16    |
| FAIL    | 1     |
| WARN    | 9     |

The code implements the core acceptance criteria correctly — account creation, login, sequential and browse quiz modes, case-insensitive answers, password hashing, error handling on missing files and bad input, personalized tips, and score retention on retakes all work as specified. The single **FAIL** is the feedback-weighting system: ratings are collected and stored but never actually used to influence quiz selection, which the spec explicitly requires. The **WARN** items are a mix of missing input validation, security best-practice gaps (unsalted hashes, pickle deserialization), and a potentially unimplemented extension feature.
