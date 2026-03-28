import json
import hashlib
import zlib
import os
import sys
import random

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


# ---------------------------------------------------------------------------
# File I/O helpers
# ---------------------------------------------------------------------------

def load_questions():
    try:
        with open(QUESTIONS_FILE, "r") as f:
            data = json.load(f)
            return data["questions"]
    except (FileNotFoundError, json.JSONDecodeError, KeyError):
        print("Oops, can't find the questions file!")
        sys.exit(1)


def load_tips():
    try:
        with open(TIPS_FILE, "r") as f:
            return json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        return {}


def _load_dat(filepath):
    """Load a zlib-compressed JSON file. Safe alternative to pickle."""
    try:
        with open(filepath, "rb") as f:
            return json.loads(zlib.decompress(f.read()).decode())
    except (FileNotFoundError, EOFError):
        return {}
    except (zlib.error, json.JSONDecodeError):
        return {}


def _save_dat(filepath, data):
    """Save data as zlib-compressed JSON. Non-human-readable but safe."""
    with open(filepath, "wb") as f:
        f.write(zlib.compress(json.dumps(data).encode()))


def load_users():
    return _load_dat(USERS_FILE)


def save_users(users):
    _save_dat(USERS_FILE, users)


def load_scores():
    return _load_dat(SCORES_FILE)


def save_scores(scores):
    _save_dat(SCORES_FILE, scores)


def load_feedback():
    try:
        with open(FEEDBACK_FILE, "r") as f:
            return json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        return {}


def save_feedback(feedback):
    with open(FEEDBACK_FILE, "w") as f:
        json.dump(feedback, f, indent=2)


# ---------------------------------------------------------------------------
# Utility helpers
# ---------------------------------------------------------------------------

def hash_password(password, salt=None):
    """Hash with PBKDF2-HMAC-SHA256 and a random 16-byte salt."""
    if salt is None:
        salt = os.urandom(16)
    hashed = hashlib.pbkdf2_hmac("sha256", password.encode(), salt, 100_000)
    return salt.hex() + ":" + hashed.hex()


def verify_password(password, stored):
    """Support both new salted format and legacy unsalted SHA-256."""
    if ":" not in stored:
        return hashlib.sha256(password.encode()).hexdigest() == stored
    salt_hex, hash_hex = stored.split(":", 1)
    salt = bytes.fromhex(salt_hex)
    hashed = hashlib.pbkdf2_hmac("sha256", password.encode(), salt, 100_000)
    return hashed.hex() == hash_hex


def get_int_input(prompt, min_val=None, max_val=None):
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

def create_account(users):
    print("\n--- Create Account ---")
    name = input("  Enter your name: ").strip()
    if not name:
        print("  Name cannot be empty.")
        return None

    email = input("  Enter your email: ").strip()
    if not email:
        print("  Email cannot be empty.")
        return None

    if email in users:
        print("  An account with this email already exists.")
        return None

    password = input("  Create a password: ").strip()
    if not password:
        print("  Password cannot be empty.")
        return None

    print("\n  Select your MBTI type:")
    for i, mbti in enumerate(MBTI_TYPES, 1):
        print(f"    {i:>2}. {mbti}")

    choice = get_int_input("  Choose an option: ", 1, 16)
    mbti_type = MBTI_TYPES[choice - 1]

    users[email] = {
        "name": name,
        "email": email,
        "password": hash_password(password),
        "mbti": mbti_type,
    }
    save_users(users)
    print(f"\n  Account created successfully! Welcome, {name} ({mbti_type}).")
    return email


def login(users):
    print("\n--- Login ---")
    email = input("  Enter your email: ").strip()

    if email not in users:
        print("  Email not found. Please try again.")
        return None

    for attempt in range(MAX_LOGIN_ATTEMPTS):
        password = input("  Enter your password: ").strip()
        if verify_password(password, users[email]["password"]):
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

def show_dashboard(user, scores_data, email):
    print(f"\n{'=' * 50}")
    print(f"  Welcome, {user['name']} ({user['mbti']})")
    print(f"{'=' * 50}")

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

    print(f"{'=' * 50}")


# ---------------------------------------------------------------------------
# Quiz engine
# ---------------------------------------------------------------------------

def run_quiz(questions, section, user_mbti, tips):
    section_questions = [q for q in questions if q["category"] == section]
    if not section_questions:
        print(f"  No questions found for '{section}'.")
        return None, None

    print(f"\n{'=' * 50}")
    print(f"  Quiz: {section}")
    print(f"{'=' * 50}")

    correct = 0
    total = len(section_questions)
    missed = []

    for i, q in enumerate(section_questions, 1):
        print(f"\n  Question {i}/{total} [{section}]")
        print(f"  {q['question']}")

        if q["type"] == "multiple_choice":
            for j, opt in enumerate(q["options"], 1):
                print(f"    {j}. {opt}")
            choice = get_int_input("  Your answer (number): ", 1, len(q["options"]))
            user_answer = q["options"][choice - 1]
            if user_answer == q["answer"]:
                correct += 1
            else:
                missed.append((q["question"], q["answer"], user_answer))

        elif q["type"] == "true_false":
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
            if answer == q["answer"].lower():
                correct += 1
            else:
                missed.append((q["question"], q["answer"], answer))

        elif q["type"] == "short_answer":
            answer = input("  Your answer: ").strip()
            if answer.lower() == q["answer"].lower():
                correct += 1
            else:
                missed.append((q["question"], q["answer"], answer))

    pct = round(correct / total * 100) if total > 0 else 0

    print(f"\n{'=' * 50}")
    print(f"  Section Complete: {section}")
    print(f"  You scored {correct}/{total} ({pct}%)")
    print(f"{'=' * 50}")

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

    return correct, total


def update_score(scores_data, email, section, correct, total):
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


def rate_section(section, feedback, email):
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

def next_section(scores_data, email):
    user_scores = scores_data.get(email, {})
    for section in SECTION_ORDER:
        if section not in user_scores:
            return section
    return None


# ---------------------------------------------------------------------------
# Browse all quizzes
# ---------------------------------------------------------------------------

def browse_quizzes(questions, scores_data, email, user_mbti, tips, feedback):
    print(f"\n{'=' * 50}")
    print("  Browse All Quizzes")
    print(f"{'=' * 50}")

    user_scores = scores_data.get(email, {})

    for i, section in enumerate(SECTION_ORDER, 1):
        if section in user_scores:
            s = user_scores[section]
            pct = round(s["correct"] / s["total"] * 100) if s["total"] > 0 else 0
            print(f"  {i}. [DONE] {section} - {s['correct']}/{s['total']} ({pct}%)")
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

def review_quiz(questions, scores_data, email, user_mbti, tips, feedback):
    """Mixed review quiz where highly-rated sections contribute more questions."""
    user_scores = scores_data.get(email, {})
    user_feedback = feedback.get(email, {})

    completed = [s for s in SECTION_ORDER if s in user_scores]
    if not completed:
        print("\n  Complete at least one section before using Review Mode.")
        return

    weighted_pool = []
    for section in completed:
        rating = user_feedback.get(section, 3)
        section_qs = [q for q in questions if q["category"] == section]
        for _ in range(rating):
            weighted_pool.extend(section_qs)

    unique_qs = list({q["question"]: q for q in weighted_pool}.values())
    review_size = min(5, len(unique_qs))

    weights = []
    for q in unique_qs:
        rating = user_feedback.get(q["category"], 3)
        weights.append(rating)

    selected = []
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

    print(f"\n{'=' * 50}")
    print("  Review Quiz (mixed sections, feedback-weighted)")
    print(f"{'=' * 50}")

    correct = 0
    total = len(selected)
    missed = []

    for i, q in enumerate(selected, 1):
        print(f"\n  Question {i}/{total} [{q['category']}]")
        print(f"  {q['question']}")

        if q["type"] == "multiple_choice":
            for j, opt in enumerate(q["options"], 1):
                print(f"    {j}. {opt}")
            choice = get_int_input("  Your answer (number): ", 1, len(q["options"]))
            user_answer = q["options"][choice - 1]
            if user_answer == q["answer"]:
                correct += 1
            else:
                missed.append((q["question"], q["answer"], user_answer))

        elif q["type"] == "true_false":
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
            if answer == q["answer"].lower():
                correct += 1
            else:
                missed.append((q["question"], q["answer"], answer))

        elif q["type"] == "short_answer":
            answer = input("  Your answer: ").strip()
            if answer.lower() == q["answer"].lower():
                correct += 1
            else:
                missed.append((q["question"], q["answer"], answer))

    pct = round(correct / total * 100) if total > 0 else 0

    print(f"\n{'=' * 50}")
    print("  Review Complete!")
    print(f"  You scored {correct}/{total} ({pct}%)")
    print(f"{'=' * 50}")

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
# Category-based filtering (extension feature)
# ---------------------------------------------------------------------------

def filtered_quiz(questions, user_mbti, tips):
    """Let the user pick one or more categories, then quiz on those questions."""
    print(f"\n{'=' * 50}")
    print("  Filter Quiz by Category")
    print(f"{'=' * 50}")

    for i, section in enumerate(SECTION_ORDER, 1):
        print(f"  {i}. {section}")

    print(f"\n  Enter category numbers separated by commas (e.g. 1,3,5)")
    print(f"  Or type 'all' for all categories.")

    while True:
        raw = input("\n  Your selection: ").strip().lower()
        if raw == "all":
            chosen = list(SECTION_ORDER)
            break

        try:
            indices = [int(x.strip()) for x in raw.split(",")]
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

    print(f"\n{'=' * 50}")
    print(f"  Filtered Quiz: {', '.join(chosen)}")
    print(f"{'=' * 50}")

    correct = 0
    total = len(selected_qs)
    missed = []

    for i, q in enumerate(selected_qs, 1):
        print(f"\n  Question {i}/{total} [{q['category']}]")
        print(f"  {q['question']}")

        if q["type"] == "multiple_choice":
            for j, opt in enumerate(q["options"], 1):
                print(f"    {j}. {opt}")
            choice = get_int_input("  Your answer (number): ", 1, len(q["options"]))
            user_answer = q["options"][choice - 1]
            if user_answer == q["answer"]:
                correct += 1
            else:
                missed.append((q["question"], q["answer"], user_answer))

        elif q["type"] == "true_false":
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
            if answer == q["answer"].lower():
                correct += 1
            else:
                missed.append((q["question"], q["answer"], answer))

        elif q["type"] == "short_answer":
            answer = input("  Your answer: ").strip()
            if answer.lower() == q["answer"].lower():
                correct += 1
            else:
                missed.append((q["question"], q["answer"], answer))

    pct = round(correct / total * 100) if total > 0 else 0

    print(f"\n{'=' * 50}")
    print(f"  Filtered Quiz Complete!")
    print(f"  You scored {correct}/{total} ({pct}%)")
    print(f"{'=' * 50}")

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
# Main menu (logged-in)
# ---------------------------------------------------------------------------

def main_menu(email, users, questions, tips):
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

def main():
    questions = load_questions()
    tips = load_tips()

    print(f"\n{'=' * 50}")
    print("  Welcome to MBTI Theory Quiz!")
    print(f"{'=' * 50}")

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
