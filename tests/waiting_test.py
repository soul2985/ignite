from locust import HttpUser, task, between
import random


class WaitingUser(HttpUser):

    wait_time = between(0.8, 1.2)

    def on_start(self):

        self.student_name = f"Student_{random.randint(100000,999999)}"

        # Open join page
        self.client.get("/join")

        # Join only once
        self.client.post(
            "/join",
            data={
                "student_name": self.student_name
            },
            allow_redirects=True
        )

    @task
    def poll_status(self):
        self.client.get("/quiz-status")