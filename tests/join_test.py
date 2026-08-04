from locust import HttpUser, task, between
import random


class JoinUser(HttpUser):

    wait_time = between(1, 3)

    @task
    def join_quiz(self):

        # Open Join Page
        self.client.get("/join")

        # Generate random student name
        student_name = f"Student_{random.randint(1,100000)}"

        # Submit Join Form
        self.client.post(
            "/join",
            data={
                "student_name": student_name
            },
            allow_redirects=True
        )