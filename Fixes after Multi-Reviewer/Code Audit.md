# Code Audit: The Senior Code Stylist

**Reviewer role:** Senior Python Developer — Code Quality, Readability & Pythonic Best Practices  
**Scope:** Naming conventions, DRY compliance, function length, PEP 8, maintainability, architecture  
**File under review:** `quiz.py` (701 lines)

---

## Findings

### DRY (Don't Repeat Yourself)

**1. [FAIL] Question-asking logic is copy-pasted three times — `quiz.py` lines 274–305, 460–491, 564–595**

The if/elif block that handles `multiple_choice`, `true_false`, and `short_answer` input is duplicated verbatim across `run_quiz()`, `review_quiz()`, and `filtered_quiz()`. This is roughly 30 lines repeated 3 times (≈90 lines of redundancy). Any bug fix or new question type must be applied in three places. This should be extracted into a single helper function, e.g.:

```python
def ask_question(q):
    """Prompt the user for one question and return (is_correct, user_answer)."""
```

**2. [FAIL] Results display block is copy-pasted three times — `quiz.py` lines 307–325, 493–511, 597–615**

The end-of-quiz output (score line, missed-question listing, and tip display) is nearly identical across the same three functions. This should be a single helper, e.g.:

```python
def show_results(section_name, correct, total, missed, user_mbti, tips):
```

**3. [WARN] `weighted_pool` in `review_quiz()` does redundant work — `quiz.py` lines 420–433**

Lines 420–425 build a pool by repeating each question `rating` times, then line 427 de-duplicates by question text, then lines 430–433 rebuild the weights from scratch. The intermediate pool with duplicated questions serves no purpose — the de-duplication immediately discards the repetitions. The weight list could be built directly from the completed sections without the intermediate pool:

```python
unique_qs = [q for q in questions if q["category"] in completed]
weights = [user_feedback.get(q["category"], 3) for q in unique_qs]
```

---

### Function Length & Complexity

**4. [FAIL] `review_quiz()` is 102 lines long — `quiz.py` lines 410–511**

This function handles guard checks, weighted-random selection, question iteration (with 3 question-type branches), score tallying, result display, and tip display. It has at least 4 distinct responsibilities. After extracting the question-asking and results-display helpers (findings #1 and #2), this function would shrink to roughly 30 lines focused purely on the weighted selection logic.

**5. [FAIL] `filtered_quiz()` is 98 lines long — `quiz.py` lines 518–615**

Same issue. Category selection UI, question loop, scoring, and results are all in one function. With the shared helpers extracted, this would reduce to roughly 25 lines of category-filtering logic.

**6. [PASS] `run_quiz()` is 72 lines — `quiz.py` lines 256–327**

Moderate length, and currently the "original" version of the quiz loop. Acceptable on its own, though it would still benefit from the extracted helpers.

**7. [PASS] All other functions are under 40 lines**

`create_account()` (37 lines), `show_dashboard()` (34 lines), `main_menu()` (39 lines), `login()` (20 lines), and all I/O helpers are appropriately sized.

---

### Naming Conventions

**8. [PASS] Module-level constants follow `UPPER_SNAKE_CASE` — `quiz.py` lines 8–38**

`BASE_DIR`, `QUESTIONS_FILE`, `SECTION_ORDER`, `MBTI_TYPES`, `SKILL_MAP`, `MAX_LOGIN_ATTEMPTS` — all correctly named per PEP 8.

**9. [PASS] Functions and variables use `lower_snake_case` throughout**

`load_questions`, `hash_password`, `verify_password`, `get_int_input`, `create_account`, `scores_data`, `user_mbti`, `section_questions`, etc. — consistently correct.

**10. [PASS] Private helper convention used correctly — `quiz.py` lines 63, 74**

`_load_dat()` and `_save_dat()` use the single-underscore prefix to signal internal-use helpers. Public-facing wrappers (`load_users`, `save_users`, etc.) delegate to them.

**11. [WARN] Single-letter variable `s` is unclear — `quiz.py` line 385**

Inside `browse_quizzes()`, `s = user_scores[section]` uses `s` to hold a score dictionary. A name like `score` or `section_score` would be clearer without adding verbosity.

**12. [WARN] Variable name `raw` is vague — `quiz.py` line 531**

In `filtered_quiz()`, `raw = input(...)` could be `selection` or `user_input` to better describe its purpose.

---

### PEP 8 Compliance

**13. [PASS] Line length is within limits — entire file**

No line exceeds 88 characters. The project comfortably stays within PEP 8's 79-character recommendation and the commonly-accepted 88-character alternative.

**14. [PASS] Blank line conventions are correct — entire file**

Two blank lines separate top-level functions (PEP 8 §E303). No extraneous blank lines inside function bodies.

**15. [PASS] Import grouping is correct — `quiz.py` lines 1–6**

All imports are from the standard library, grouped in a single block. No third-party or local imports exist, so no further separation is needed.

**16. [PASS] Consistent string quoting — entire file**

Double quotes are used throughout for all strings. No mixing of single/double quote styles.

**17. [PASS] Trailing commas used in multi-line collections — `quiz.py` lines 21, 28, 36, 184**

`SECTION_ORDER`, `MBTI_TYPES`, `SKILL_MAP`, and the user dict all use trailing commas, which keeps diffs clean when appending items.

---

### Magic Numbers & Strings

**18. [WARN] Hardcoded `16` instead of `len(MBTI_TYPES)` — `quiz.py` line 176**

`get_int_input("  Choose an option: ", 1, 16)` uses the literal `16`. If `MBTI_TYPES` were ever modified, this would silently become wrong. Should be `len(MBTI_TYPES)`.

**19. [WARN] PBKDF2 iteration count `100_000` is duplicated — `quiz.py` lines 117, 127**

The iteration count appears in both `hash_password()` and `verify_password()`. If it ever needs changing, both must be updated in sync. Should be a module-level constant:

```python
PBKDF2_ITERATIONS = 100_000
```

**20. [WARN] Separator width `50` is repeated 20+ times — `quiz.py` lines 217, 219, 262, 264, etc.**

`'=' * 50` appears in nearly every UI function. A constant like `SEPARATOR = '=' * 50` would make the width trivially adjustable and remove visual noise from every function.

**21. [WARN] Default rating `3` is a magic number — `quiz.py` lines 422, 432**

The fallback rating for unrated sections is hardcoded as `3` in two places inside `review_quiz()`. A constant like `DEFAULT_RATING = 3` would document the intent.

**22. [WARN] Review quiz size `5` is a magic number — `quiz.py` line 428**

`min(5, len(unique_qs))` uses an unexplained `5`. A constant like `REVIEW_QUIZ_SIZE = 5` makes the design decision visible.

---

### Docstrings & Type Hints

**23. [WARN] 11 of 19 functions lack docstrings — `quiz.py`**

The following functions have no docstring: `load_questions()`, `load_tips()`, `load_users()`, `save_users()`, `load_scores()`, `save_scores()`, `load_feedback()`, `save_feedback()`, `create_account()`, `login()`, `show_dashboard()`, `run_quiz()`, `next_section()`, `browse_quizzes()`, `main_menu()`, `main()`. Some are self-explanatory by name (e.g., `load_users`), but the more complex ones like `run_quiz`, `browse_quizzes`, and `main_menu` would benefit from a one-liner explaining parameters and return values.

**24. [WARN] No type hints anywhere in the file — `quiz.py`**

Not a single function uses type annotations. For a 700-line file with multiple data structures (dicts of dicts, lists of dicts, tuples), type hints would significantly improve readability and enable static analysis:

```python
def run_quiz(questions: list[dict], section: str, user_mbti: str, tips: dict) -> tuple[int | None, int | None]:
```

This is not required by PEP 8 but is considered best practice for any non-trivial Python project.

---

### Code Structure & Architecture

**25. [PASS] Single-file architecture is appropriate for the project scope**

At 701 lines with a clear section-comment structure, the single-file layout is reasonable for a homework project. The file is organized in logical blocks: constants → I/O → utilities → account management → dashboard → quiz engine → menus → entry point. No function is "lost."

**26. [PASS] `main()` function with `if __name__ == "__main__"` guard — `quiz.py` lines 667–700**

Proper entry-point pattern that allows importing the module without side effects.

**27. [PASS] Configuration is centralized at the top of the file — `quiz.py` lines 8–38**

All file paths, constants, and mappings are defined as module-level constants before any function. Easy to find and modify.

**28. [WARN] `email` is stored redundantly inside the user dict — `quiz.py` line 181**

`users[email] = { "email": email, ... }` stores the email both as the dict key and as a value inside the dict. This is minor, but redundant data can lead to inconsistencies if one is updated without the other.

---

### Pythonic Idioms

**29. [PASS] List comprehensions used appropriately — throughout**

Filtering questions by category (`[q for q in questions if q["category"] == section]`), building skill lists, and collecting completed sections all use idiomatic comprehensions.

**30. [PASS] `.get()` with defaults used for safe dict access — `quiz.py` lines 221, 365, 381, 412, 413, 422, 432**

All dictionary lookups for potentially-missing keys use `.get(key, default)` rather than try/except `KeyError`. Consistent and Pythonic.

**31. [PASS] `enumerate()` used for all indexed loops — throughout**

Every loop that needs an index uses `enumerate(collection, 1)` rather than manual counter variables.

**32. [WARN] Unnecessary f-string without interpolation — `quiz.py` line 528**

`print(f"  Or type 'all' for all categories.")` — the `f` prefix is unnecessary since the string contains no `{}` expressions. Should be a plain string.

**33. [PASS] Tuple unpacking in `for` loops — `quiz.py` lines 316, 502, 606**

`for question_text, correct_ans, user_ans in missed:` cleanly unpacks the 3-tuples. Clear and readable.

---

### Error Handling Style

**34. [PASS] Exception groups are appropriately scoped — `quiz.py` lines 50, 59, 68–71, 100**

Each `except` clause catches only the specific exceptions that can arise from the corresponding `try` block. No bare `except:` or overly broad `except Exception:` anywhere.

**35. [WARN] Two separate `except` blocks return the same value — `quiz.py` lines 68–71**

In `_load_dat()`, both `except (FileNotFoundError, EOFError)` and `except (zlib.error, json.JSONDecodeError)` return `{}`. These could be combined into a single `except` clause for conciseness, though separating them does document the two failure categories:

```python
except (FileNotFoundError, EOFError, zlib.error, json.JSONDecodeError):
    return {}
```

---

## Summary

| Verdict | Count | Area |
|---------|-------|------|
| **PASS**  | **18**  | Naming, PEP 8 formatting, imports, constants placement, idioms, error handling, architecture |
| **WARN**  | **13**  | Magic numbers (×5), missing docstrings, no type hints, vague variable names (×2), redundant data, unnecessary f-string, collapsible except blocks |
| **FAIL**  | **4**   | Question-asking code duplicated ×3, results-display code duplicated ×3, two functions over 95 lines each |

### Overall Assessment

The codebase reads well at a surface level — naming is clear, PEP 8 formatting is near-perfect, constants are centralized, and Pythonic idioms (comprehensions, `enumerate`, `.get()`) are used consistently. The critical issue is a **DRY violation**: the question-asking loop and results-display block are copy-pasted across three functions (`run_quiz`, `review_quiz`, `filtered_quiz`), inflating the file by roughly 180 lines and creating a maintenance hazard where any bug fix or new question type must be applied in three places. Extracting two helpers — `ask_question()` and `show_results()` — would eliminate the duplication and bring the two oversized functions well under 40 lines each. The remaining warnings are standard polish items: adding type hints, replacing magic numbers with named constants, and filling in missing docstrings.
