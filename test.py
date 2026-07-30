from pathlib import Path

path = Path("data") / "quizzes" / "test.csv"

print(path)
print(path.parent.exists())

with path.open("w", encoding="utf-8") as f:
    f.write("Hello!")

print("Success!")