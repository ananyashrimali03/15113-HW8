import json
import hashlib
import pickle
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


def load_users():
    try:
        with open(USERS_FILE, "rb") as f:
            return pickle.load(f)
    except (FileNotFoundError, EOFError, pickle.UnpicklingError):
        return {}


def save_users(users):
    with open(USERS_FILE, "wb") as f:
        pickle.dump(users, f)


def load_scores():
    try:
        with open(SCORES_FILE, "rb") as f:
            return pickle.load(f)
    except (FileNotFoundError, EOFError, pickle.UnpicklingError):
        return {}


def save_scores(scores):
    with open(SCORES_FILE, "wb") as f:
        pickle.dump(scores, f)


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

def hash_password(password):
    return hashlib.sha256(password.encode()).hexdigest()


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
    email = input("  Enter your email: ").strip()

    if email in users:
        print("  An account with this email already exists.")
        return None

    password = input("  Create a password: ").strip()

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

    password = input("  Enter your password: ").strip()

    if hash_password(password) != users[email]["password"]:
        print("  Wrong password. Please try again.")
        return None

    print(f"\n  Welcome back, {users[email]['name']}!")
    return email


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

    skill_map = {
        "MBTI Basics": "MBTI Fundamentals",
        "Cognitive Functions": "Function Stacks",
        "Stereotypes": "Stereotype Awareness",
        "MBTI Behaviors": "Behavior Analysis",
        "Traits to Look For": "Trait Observation",
    }
    skills = [skill_map[s] for s in completed if s in skill_map]
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
            print("    Type 'true' or 'false'")
            while True:
                answer = input("  Your answer: ").strip().lower()
                if answer in ("true", "false"):
                    break
                print("  Invalid input. Please type 'true' or 'false'.")
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
        print("  3. Logout")

        choice = get_int_input("\n  Choose an option: ", 1, 3)

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
            scores_data = load_scores()

        elif choice == 3:
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
