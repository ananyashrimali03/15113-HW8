from __future__ import annotations

import getpass
import hashlib
import json
import os
import random
import sys
import tempfile
import zlib

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
QUESTIONS_FILE = os.path.join(BASE_DIR, "questions.json")
USERS_FILE = os.path.join(BASE_DIR, "users.dat")
SCORES_FILE = os.path.join(BASE_DIR, "scores.dat")
FEEDBACK_FILE = os.path.join(BASE_DIR, "feedback.json")
TIPS_FILE = os.path.join(BASE_DIR, "tips.json")

SECTION_ORDER = [
    "MBTI Basics",
    "Cognitive Functions",
    "Stereotypes",
    "MBTI Behaviors",
    "Traits to Look For",
]

MBTI_TYPES = [
    "INTJ", "INTP", "ENTJ", "ENTP",
    "INFJ", "INFP", "ENFJ", "ENFP",
    "ISTJ", "ISTP", "ESTJ", "ESTP",
    "ISFJ", "ISFP", "ESFJ", "ESFP",
]

SKILL_MAP = {
    "MBTI Basics": "MBTI Fundamentals",
    "Cognitive Functions": "Function Stacks",
    "Stereotypes": "Stereotype Awareness",
    "MBTI Behaviors": "Behavior Analysis",
    "Traits to Look For": "Trait Observation",
}

MAX_LOGIN_ATTEMPTS = 3
PBKDF2_ITERATIONS = 100_000
SEPARATOR = "=" * 50
DEFAULT_RATING = 3
REVIEW_QUIZ_SIZE = 5
MAX_INPUT_LENGTH = 200


# ---------------------------------------------------------------------------
# File I/O helpers
# ---------------------------------------------------------------------------

def load_questions() -> list[dict]:
    """Load the question bank from questions.json, or exit on failure."""
    try:
        with open(QUESTIONS_FILE, "r") as f:
            data = json.load(f)
            return data["questions"]
    except (FileNotFoundError, json.JSONDecodeError, KeyError):
        print("Oops, can't find the questions file!")
        sys.exit(1)


def load_tips() -> dict[str, list[str]]:
    """Load MBTI tips, returning an empty dict on failure."""
    try:
        with open(TIPS_FILE, "r") as f:
            return json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        return {}


def _load_dat(filepath: str) -> dict:
    """Load a zlib-compressed JSON file. Safe alternative to pickle."""
    try:
        with open(filepath, "rb") as f:
            return json.loads(zlib.decompress(f.read()).decode())
    except (FileNotFoundError, EOFError, zlib.error, json.JSONDecodeError):
        return {}


def _save_dat(filepath: str, data: dict) -> None:
    """Save data as zlib-compressed JSON via atomic temp-file write."""
    content = zlib.compress(json.dumps(data).encode())
    dir_name = os.path.dirname(filepath)
    fd, tmp_path = tempfile.mkstemp(dir=dir_name)
    try:
        with os.fdopen(fd, "wb") as tmp_f:
            tmp_f.write(content)
        os.replace(tmp_path, filepath)
    except BaseException:
        try:
            os.unlink(tmp_path)
        except OSError:
            pass
        raise


def load_users() -> dict:
    """Load user accounts from users.dat."""
    return _load_dat(USERS_FILE)


def save_users(users: dict) -> None:
    """Persist user accounts to users.dat."""
    _save_dat(USERS_FILE, users)


def load_scores() -> dict:
    """Load score history from scores.dat."""
    return _load_dat(SCORES_FILE)


def save_scores(scores: dict) -> None:
    """Persist score history to scores.dat."""
    _save_dat(SCORES_FILE, scores)


def load_feedback() -> dict:
    """Load section ratings from feedback.json."""
    try:
        with open(FEEDBACK_FILE, "r") as f:
            return json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        return {}


def save_feedback(feedback: dict) -> None:
    """Save section ratings to feedback.json via atomic temp-file write."""
    content = json.dumps(feedback, indent=2)
    dir_name = os.path.dirname(FEEDBACK_FILE)
    fd, tmp_path = tempfile.mkstemp(dir=dir_name, suffix=".json")
    try:
        with os.fdopen(fd, "w") as tmp_f:
            tmp_f.write(content)
        os.replace(tmp_path, FEEDBACK_FILE)
    except BaseException:
        try:
            os.unlink(tmp_path)
        except OSError:
            pass
        raise


# ---------------------------------------------------------------------------
# Utility helpers
# ---------------------------------------------------------------------------

def hash_password(password: str, salt: bytes | None = None) -> str:
    """Hash with PBKDF2-HMAC-SHA256 and a random 16-byte salt."""
    if salt is None:
        salt = os.urandom(16)
    hashed = hashlib.pbkdf2_hmac(
        "sha256", password.encode(), salt, PBKDF2_ITERATIONS,
    )
    return salt.hex() + ":" + hashed.hex()


def _is_legacy_hash(stored: str) -> bool:
    """Return True if the stored hash uses the old unsalted SHA-256 format."""
    return ":" not in stored


def verify_password(password: str, stored: str) -> bool:
    """Verify a password against its stored hash (salted or legacy)."""
    if _is_legacy_hash(stored):
        return hashlib.sha256(password.encode()).hexdigest() == stored
    salt_hex, hash_hex = stored.split(":", 1)
    salt = bytes.fromhex(salt_hex)
    hashed = hashlib.pbkdf2_hmac(
        "sha256", password.encode(), salt, PBKDF2_ITERATIONS,
    )
    return hashed.hex() == hash_hex


def get_int_input(
    prompt: str, min_val: int | None = None, max_val: int | None = None,
) -> int:
    """Keep asking until the user enters a valid integer in range."""
    while True:
        try:
            value = int(input(prompt))
            if min_val is not None and value < min_val:
                print(f"  Please enter a number >= {min_val}.")
                continue
            if max_val is not None and value > max_val:
                print(f"  Please enter a number <= {max_val}.")
                continue
            return value
        except ValueError:
            print("  Invalid input. Please enter a number.")


# ---------------------------------------------------------------------------
# Account management
# ---------------------------------------------------------------------------

def create_account(users: dict) -> str | None:
    """Walk the user through account creation and persist the result."""
    print("\n--- Create Account ---")
    name = input("  Enter your name: ").strip()
    if not name:
        print("  Name cannot be empty.")
        return None
    if len(name) > MAX_INPUT_LENGTH:
        print(f"  Name must be {MAX_INPUT_LENGTH} characters or fewer.")
        return None

    email = input("  Enter your email: ").strip()
    if not email:
        print("  Email cannot be empty.")
        return None
    if "@" not in email or "." not in email.split("@")[-1]:
        print("  Please enter a valid email address.")
        return None
    if len(email) > MAX_INPUT_LENGTH:
        print(f"  Email must be {MAX_INPUT_LENGTH} characters or fewer.")
        return None

    if email in users:
        print("  An account with this email already exists.")
        return None

    password = getpass.getpass("  Create a password: ").strip()
    if not password:
        print("  Password cannot be empty.")
        return None
    if len(password) > MAX_INPUT_LENGTH:
        print(f"  Password must be {MAX_INPUT_LENGTH} characters or fewer.")
        return None

    print("\n  Select your MBTI type:")
    for i, mbti in enumerate(MBTI_TYPES, 1):
        print(f"    {i:>2}. {mbti}")

    choice = get_int_input("  Choose an option: ", 1, len(MBTI_TYPES))
    mbti_type = MBTI_TYPES[choice - 1]

    users[email] = {
        "name": name,
        "password": hash_password(password),
        "mbti": mbti_type,
    }
    save_users(users)
    print(f"\n  Account created successfully! Welcome, {name} ({mbti_type}).")
    return email


def login(users: dict) -> str | None:
    """Authenticate user, migrating legacy password hashes on success."""
    print("\n--- Login ---")
    email = input("  Enter your email: ").strip()

    if email not in users:
        print("  Email not found. Please try again.")
        return None

    for attempt in range(MAX_LOGIN_ATTEMPTS):
        password = getpass.getpass("  Enter your password: ").strip()
        if verify_password(password, users[email]["password"]):
            if _is_legacy_hash(users[email]["password"]):
                users[email]["password"] = hash_password(password)
                save_users(users)
            print(f"\n  Welcome back, {users[email]['name']}!")
            return email
        remaining = MAX_LOGIN_ATTEMPTS - 1 - attempt
        if remaining > 0:
            print(f"  Wrong password. {remaining} attempt(s) remaining.")
        else:
            print("  Too many failed attempts. Returning to menu.")

    return None


# ---------------------------------------------------------------------------
# Dashboard
# ---------------------------------------------------------------------------

def show_dashboard(user: dict, scores_data: dict, email: str) -> None:
    """Print the user's progress dashboard."""
    print(f"\n{SEPARATOR}")
    print(f"  Welcome, {user['name']} ({user['mbti']})")
    print(SEPARATOR)

    user_scores = scores_data.get(email, {})
    completed = []
    total_correct = 0
    total_questions = 0

    for section in SECTION_ORDER:
        if section in user_scores:
            correct = user_scores[section]["correct"]
            total = user_scores[section]["total"]
            pct = round(correct / total * 100) if total > 0 else 0
            completed.append(section)
            total_correct += correct
            total_questions += total
            print(f"  [DONE] {section}: {correct}/{total} ({pct}%)")
        else:
            print(f"  [    ] {section}")

    if total_questions > 0:
        overall = round(total_correct / total_questions * 100)
        print(f"\n  Cumulative Score: {total_correct}/{total_questions} ({overall}%)")
        print(f"  Sections Completed: {len(completed)}/{len(SECTION_ORDER)}")
    else:
        print("\n  No quizzes completed yet.")

    skills = [SKILL_MAP[s] for s in completed if s in SKILL_MAP]
    if skills:
        print(f"  Skills Learned: {', '.join(skills)}")

    print(SEPARATOR)


# ---------------------------------------------------------------------------
# Quiz engine — shared helpers
# ---------------------------------------------------------------------------

def _ask_question(q: dict) -> tuple[bool, str]:
    """Prompt the user for one question. Return (is_correct, user_answer)."""
    if q["type"] == "multiple_choice":
        for j, opt in enumerate(q["options"], 1):
            print(f"    {j}. {opt}")
        choice = get_int_input("  Your answer (number): ", 1, len(q["options"]))
        user_answer = q["options"][choice - 1]
        return user_answer == q["answer"], user_answer

    if q["type"] == "true_false":
        print("    Type 'true' or 'false' (or 't'/'f')")
        while True:
            answer = input("  Your answer: ").strip().lower()
            if answer in ("t", "true"):
                answer = "true"
                break
            if answer in ("f", "false"):
                answer = "false"
                break
            print("  Invalid input. Please type 'true' or 'false' (or 't'/'f').")
        return answer == q["answer"].lower(), answer

    answer = input("  Your answer: ").strip()
    return answer.lower() == q["answer"].lower(), answer


def _run_question_loop(
    question_list: list[dict],
) -> tuple[int, int, list[tuple[str, str, str]]]:
    """Iterate through questions, collecting score and missed answers."""
    correct = 0
    total = len(question_list)
    missed: list[tuple[str, str, str]] = []

    for i, q in enumerate(question_list, 1):
        print(f"\n  Question {i}/{total} [{q['category']}]")
        print(f"  {q['question']}")
        is_correct, user_answer = _ask_question(q)
        if is_correct:
            correct += 1
        else:
            missed.append((q["question"], q["answer"], user_answer))

    return correct, total, missed


def _show_results(
    title: str,
    correct: int,
    total: int,
    missed: list[tuple[str, str, str]],
    user_mbti: str,
    tips: dict,
) -> None:
    """Display score, missed questions, and a personalized tip."""
    pct = round(correct / total * 100) if total > 0 else 0

    print(f"\n{SEPARATOR}")
    print(f"  {title}")
    print(f"  You scored {correct}/{total} ({pct}%)")
    print(SEPARATOR)

    if missed:
        print("\n  Questions you missed:")
        for question_text, correct_ans, user_ans in missed:
            print(f"    Q: {question_text}")
            print(f"       Your answer: {user_ans}")
            print(f"       Correct answer: {correct_ans}")
    else:
        print("\n  Perfect score! Great job!")

    if user_mbti in tips and tips[user_mbti]:
        tip = random.choice(tips[user_mbti])
        print(f"\n  Tip for {user_mbti}: {tip}")


# ---------------------------------------------------------------------------
# Quiz engine
# ---------------------------------------------------------------------------

def run_quiz(
    questions: list[dict], section: str, user_mbti: str, tips: dict,
) -> tuple[int | None, int | None]:
    """Run a single-section quiz and display results."""
    section_questions = [q for q in questions if q["category"] == section]
    if not section_questions:
        print(f"  No questions found for '{section}'.")
        return None, None

    print(f"\n{SEPARATOR}")
    print(f"  Quiz: {section}")
    print(SEPARATOR)

    correct, total, missed = _run_question_loop(section_questions)
    _show_results(
        f"Section Complete: {section}", correct, total, missed, user_mbti, tips,
    )
    return correct, total


def update_score(
    scores_data: dict, email: str, section: str, correct: int, total: int,
) -> None:
    """Store the score, keeping the higher result if retaking."""
    if email not in scores_data:
        scores_data[email] = {}

    if section in scores_data[email]:
        old_correct = scores_data[email][section]["correct"]
        if correct > old_correct:
            scores_data[email][section] = {"correct": correct, "total": total}
            print("  New high score! Updated.")
        else:
            print(f"  Previous score was higher ({old_correct}/{total}). Keeping it.")
    else:
        scores_data[email][section] = {"correct": correct, "total": total}

    save_scores(scores_data)


def rate_section(section: str, feedback: dict, email: str) -> None:
    """Prompt the user to rate a section 1-5 stars."""
    print("\n  Rate this section (1-5 stars):")
    rating = get_int_input("  Your rating: ", 1, 5)

    if email not in feedback:
        feedback[email] = {}
    feedback[email][section] = rating
    save_feedback(feedback)
    print(f"  Thanks! You rated '{section}' {'*' * rating} ({rating}/5 stars).")


# ---------------------------------------------------------------------------
# Next sequential section
# ---------------------------------------------------------------------------

def next_section(scores_data: dict, email: str) -> str | None:
    """Return the first uncompleted section, or None if all are done."""
    user_scores = scores_data.get(email, {})
    for section in SECTION_ORDER:
        if section not in user_scores:
            return section
    return None


# ---------------------------------------------------------------------------
# Browse all quizzes
# ---------------------------------------------------------------------------

def browse_quizzes(
    questions: list[dict],
    scores_data: dict,
    email: str,
    user_mbti: str,
    tips: dict,
    feedback: dict,
) -> None:
    """Show all sections with completion status and let the user pick one."""
    print(f"\n{SEPARATOR}")
    print("  Browse All Quizzes")
    print(SEPARATOR)

    user_scores = scores_data.get(email, {})

    for i, section in enumerate(SECTION_ORDER, 1):
        if section in user_scores:
            score = user_scores[section]
            pct = round(score["correct"] / score["total"] * 100) if score["total"] > 0 else 0
            print(f"  {i}. [DONE] {section} - {score['correct']}/{score['total']} ({pct}%)")
        else:
            print(f"  {i}. [    ] {section}")

    print(f"  {len(SECTION_ORDER) + 1}. Back to Main Menu")

    choice = get_int_input("\n  Select a quiz: ", 1, len(SECTION_ORDER) + 1)

    if choice == len(SECTION_ORDER) + 1:
        return

    section = SECTION_ORDER[choice - 1]
    correct, total = run_quiz(questions, section, user_mbti, tips)

    if correct is not None:
        update_score(scores_data, email, section, correct, total)
        rate_section(section, feedback, email)


# ---------------------------------------------------------------------------
# Review mode (feedback-weighted random quiz)
# ---------------------------------------------------------------------------

def review_quiz(
    questions: list[dict],
    scores_data: dict,
    email: str,
    user_mbti: str,
    tips: dict,
    feedback: dict,
) -> None:
    """Mixed review quiz where highly-rated sections contribute more questions."""
    user_scores = scores_data.get(email, {})
    user_feedback = feedback.get(email, {})

    completed = [s for s in SECTION_ORDER if s in user_scores]
    if not completed:
        print("\n  Complete at least one section before using Review Mode.")
        return

    unique_qs = [q for q in questions if q["category"] in completed]
    weights = [user_feedback.get(q["category"], DEFAULT_RATING) for q in unique_qs]

    review_size = min(REVIEW_QUIZ_SIZE, len(unique_qs))
    selected: list[dict] = []
    pool = list(enumerate(weights))

    for _ in range(review_size):
        total_w = sum(w for _, w in pool)
        pick = random.uniform(0, total_w)
        cumulative = 0
        for idx, (orig_i, w) in enumerate(pool):
            cumulative += w
            if cumulative >= pick:
                selected.append(unique_qs[orig_i])
                pool.pop(idx)
                break

    print(f"\n{SEPARATOR}")
    print("  Review Quiz (mixed sections, feedback-weighted)")
    print(SEPARATOR)

    correct, total, missed = _run_question_loop(selected)
    _show_results("Review Complete!", correct, total, missed, user_mbti, tips)


# ---------------------------------------------------------------------------
# Category-based filtering (extension feature)
# ---------------------------------------------------------------------------

def filtered_quiz(
    questions: list[dict], user_mbti: str, tips: dict,
) -> None:
    """Let the user pick one or more categories, then quiz on those questions."""
    print(f"\n{SEPARATOR}")
    print("  Filter Quiz by Category")
    print(SEPARATOR)

    for i, section in enumerate(SECTION_ORDER, 1):
        print(f"  {i}. {section}")

    print("\n  Enter category numbers separated by commas (e.g. 1,3,5)")
    print("  Or type 'all' for all categories.")

    while True:
        selection = input("\n  Your selection: ").strip().lower()
        if selection == "all":
            chosen = list(SECTION_ORDER)
            break

        try:
            indices = [int(x.strip()) for x in selection.split(",")]
            if all(1 <= idx <= len(SECTION_ORDER) for idx in indices) and indices:
                chosen = [SECTION_ORDER[idx - 1] for idx in indices]
                break
            print(f"  Numbers must be between 1 and {len(SECTION_ORDER)}.")
        except ValueError:
            print("  Invalid input. Enter numbers separated by commas, or 'all'.")

    selected_qs = [q for q in questions if q["category"] in chosen]
    if not selected_qs:
        print("  No questions found for the selected categories.")
        return

    random.shuffle(selected_qs)

    print(f"\n{SEPARATOR}")
    print(f"  Filtered Quiz: {', '.join(chosen)}")
    print(SEPARATOR)

    correct, total, missed = _run_question_loop(selected_qs)
    _show_results("Filtered Quiz Complete!", correct, total, missed, user_mbti, tips)


# ---------------------------------------------------------------------------
# Main menu (logged-in)
# ---------------------------------------------------------------------------

def main_menu(
    email: str, users: dict, questions: list[dict], tips: dict,
) -> None:
    """Post-login menu loop: dashboard, quizzes, review, filter, logout."""
    scores_data = load_scores()
    feedback = load_feedback()
    user = users[email]

    while True:
        show_dashboard(user, scores_data, email)

        print("\n  1. Start Next Quiz")
        print("  2. Browse All Quizzes")
        print("  3. Review Quiz")
        print("  4. Filter by Category")
        print("  5. Logout")

        choice = get_int_input("\n  Choose an option: ", 1, 5)

        if choice == 1:
            section = next_section(scores_data, email)
            if section is None:
                print("\n  You've completed all sections! Use 'Browse All Quizzes' to retake any.")
                continue

            correct, total = run_quiz(questions, section, user["mbti"], tips)
            if correct is not None:
                update_score(scores_data, email, section, correct, total)
                rate_section(section, feedback, email)

        elif choice == 2:
            browse_quizzes(questions, scores_data, email, user["mbti"], tips, feedback)

        elif choice == 3:
            review_quiz(questions, scores_data, email, user["mbti"], tips, feedback)

        elif choice == 4:
            filtered_quiz(questions, user["mbti"], tips)

        elif choice == 5:
            print("\n  Goodbye!\n")
            break


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------

def main() -> None:
    """Load data and run the welcome / login loop."""
    questions = load_questions()
    tips = load_tips()

    print(f"\n{SEPARATOR}")
    print("  Welcome to MBTI Theory Quiz!")
    print(SEPARATOR)

    while True:
        print("\n  1. Create Account")
        print("  2. Login")
        print("  3. Exit")

        choice = get_int_input("\n  Choose an option: ", 1, 3)

        users = load_users()

        if choice == 1:
            email = create_account(users)
            if email:
                main_menu(email, users, questions, tips)

        elif choice == 2:
            email = login(users)
            if email:
                main_menu(email, users, questions, tips)

        elif choice == 3:
            print("\n  Goodbye!\n")
            break


if __name__ == "__main__":
    main()
