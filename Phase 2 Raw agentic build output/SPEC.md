Behavior description — walk through the full user flow in the terminal (create account → login → main menu → sequential quiz or browse sections → take quiz → see results and tip → back to menu) Welcome to MBTI Theory Quiz!

Create Account
Login
Choose an option: (options: 16 MBTI types)

Under create account: ask for name, email, set up password, and select your MBTI type.
Under login: email and password.
The app starts with a create account. Where it asks the user to give their name, email, mbti and asks them to create a password. based on their created account there should be a login next to create account. Where they should be able to login to their accounts. This app is basically an MBTI theory quiz where there are sections of quiz: 1. annotations, mbti behaviors, stereotypes, likes, dislikes, traits to look for while guessing someone's MBTI; and based on how many quizzes the users are able to complete it will help the users to guess a random person's MBTI more correctly.
Now as they enter to their homescreen, the users are able to see their stats, how many quizzes they have successfully completed, what skills they have already learnet in "guessing MBTI" course.
The quizzes should be lined up one after the other. But the users still have an option to view all the quizzes in another page tab where they can complete any random quiz if they wish to and so that quiz will be canceled in the main dashboard lineup and the next quiz will come up.
When they start a quiz, the users must be able to complete the full quiz first and then after the section is completed theyll be able to see the correct answers and final score of that quiz portion. Each section score should be added to the user dashboard towards the final score so far.
At the end of each section just show a tip based on their own mbti on how to approach a random mbti, like a conversation tip towards any other mbti peerson they'll find: example: "An INTJ (you) shouldn't start the meeting with a cold stare towards ENFJs in their first meeting, try asking a random question putting up a smile instead."
Quiz sequential order - The sequential order is: 1. MBTI Basics, 2. Cognitive Functions, 3. Stereotypes, 4. MBTI Behaviors, 5. Traits to Look For
Data Format:
The question bank is a JSON file using the following structure:
{
"questions": [
{
"question": "How many types of MBTI are there?",
"type": "multiple_choice",
"options": ["4", "8", "12", "16"],
"answer": "16",
"category": "MBTI Basics"
},
{
"question": "How many types of cognitive functions are there?",
"type": "multiple_choice",
"options": ["4", "8", "12", "16"],
"answer": "8",
"category": "Cognitive Functions"
},
{
"question": "What's the MBTI type most commonly stereotyped as the highly logical, unyielding 'Mastermind' or 'Architect'?",
"type": "short_answer",
"answer": "INTJ",
"category": "Stereotypes"
},
{
"question": "Which MBTI dichotomy best dictates behavioral responses to schedules, deadlines, and external organization?",
"type": "multiple_choice",
"options": [
"Introversion (I) vs. Extraversion (E)",
"Sensing (S) vs. Intuition (N)",
"Thinking (T) vs. Feeling (F)",
"Judging (J) vs. Perceiving (P)"
],
"answer": "Judging (J) vs. Perceiving (P)",
"category": "MBTI Behaviors"
},
{
"question": "True or False: When observing someone's traits, you can confidently identify an 'Extravert' (E) purely by how talkative and socially outgoing they are, regardless of how they recharge their energy.",
"type": "true_false",
"answer": "false",
"category": "Traits to Look For"
}
]
}
Scoring: each question is worth 1 point, track correct vs total per section, calculate a percentage, and keep a cumulative score across all completed sections. After each section, the user sees something like "You scored 7/10 (70%) on MBTI Behaviors. If a user retakes a section, the higher score is kept
Feedback: after completing a section and seeing results, the user rates the section (thumbs up/thumbs down or 1-5 stars). Questions from highly-rated sections get weighted more in any "random quiz" or review mode. This keeps it simple while meeting the requirement.
File Structure:
quiz.py — the main entry point. Run with python quiz.py. Contains all the app logic: login, menus, quiz flow, scoring, displaying tips.
questions.json — the question bank. Human-readable JSON so you can easily edit or add questions. This is the file your sample questions live in. You can create this based on the data structure I mentioned.
users.dat — stores user account info (name, email, MBTI type, hashed password). Non-human-readable format (using pickle or shelve from Python's standard library). The assignment says passwords shouldn't be easily discoverable.
scores.dat — stores score history per user (section scores, cumulative score, completed sections). Also non-human-readable. The assignment requires this to be relatively secure.
feedback.json — stores user ratings for each section (thumbs up/down or star ratings). Can be JSON since there's nothing sensitive here, and it needs to be read to weight future quiz selection.
tips.json - tips.json should look like:
{"INTJ": ["tip1 text here", "tip2 text here"], "ENFP": ["tip1", "tip2"]}
Error handling:

if questions.json is missing or corrupted, the app will just print out a friendly error like 'oops cant find the questions file' and then exit with code 1.

if a user enters an invalid menu option like typing letters instead of a number, the app wont crash, it'll just say 'invalid input' and loop back to ask them to try again.

if someone tries to login with a username that doesn't exist, it tells them username not found and takes them back to the menu.

if the password is wrong, it just says wrong password try again.

if users.dat or scores.dat gets deleted mid-use, the app catches the missing file error and just makes a new empty save file so it doesn't break everything.

Password handling: passwords should be hashed using hashlib and never stored in plain text in the users.dat file.

Case sensitivity: short answer questions should accept both "intj" and "INTJ" (and any other capitalization) as correct by just making the inputs lowercase before checking.

The personalized tip system: the tips will live in a separate JSON file called tips.json so they aren't hardcoded in the python file. The app just looks at the user's MBTI from their profile and matches it to the right MBTI tip in that file.

Quiz flow details:
Let's say there are 5 questions per section.
During each question, the user will see what question number they are on, the category, the question itself, and how to answer (like type true or false).
At the end of a section, it exactly shows: the final score, a list of what the right answers were for the ones they missed, and then the personalized tip.
Users can retake a completed section if they want to.
For the "browse all quizzes" option, the terminal basically just prints a list of all the sections numbered 1 through whatever, and if they already did one, it says [DONE] next to it. Marking a quiz complete here just means the sequential lineup skips it next time. The sequential lineup is just a fixed order of the categories playing one after another.

Feedback details: the rating prompt appears exactly right after they finish a section and see their score. It just asks "rate this section 1-5 stars" in the terminal. This rating is stored in feedback.json.

Extension Feature: Category-based filtering

Acceptance criteria:

A new user can create an account and log in successfully

Running the app with a missing questions.json prints an error and exits with code 1

A user entering a string instead of an int on the menu gets asked to try again, instead of the app crashing

Passwords are hashed using hashlib and are not readable in the users.dat file

Typing "intj" or "INTJ" both work for short answer questions

Taking a quiz out of order in the browse section successfully updates the score and removes it from the main sequential lineup

At the end of a completed section, a personalized MBTI tip is displayed that matches the user's MBTI type from their profile
