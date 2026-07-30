import requests
import csv
import random
import html

url = https://opentdb.com/api.php?amount=50&category=18&difficulty=medium&type=multiple
response = requests.get(url)
data = response.json()

with open("data/quizzes/General Knowledge.csv", "w", newline="", encoding="utf-8") as file:

    writer = csv.writer(file)

    writer.writerow([
        "Question",
        "Option A",
        "Option B",
        "Option C",
        "Option D",
        "Correct Answer"
    ])

    for question in data["results"]:

        options = question["incorrect_answers"] + [question["correct_answer"]]
        random.shuffle(options)

        writer.writerow([
            html.unescape(question["question"]),
            html.unescape(options[0]),
            html.unescape(options[1]),
            html.unescape(options[2]),
            html.unescape(options[3]),
            html.unescape(question["correct_answer"])
        ])

print("Quiz saved successfully!")