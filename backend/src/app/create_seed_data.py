from app.db import db_session
from app.models import TodoDAO, UserDAO


def create_seed_data():
    # Seed data
    # create 10 users
    # create a few notes for the first user
    users = []
    for i in range(1, 11):
        name = f"user{i}"
        user = UserDAO(name=name, password="pass")
        users.append(user)

    user1 = users[0]
    todos = [
        TodoDAO(user=user1, title="Note 1", content="My first Note"),
        TodoDAO(user=user1, title="Note 2", content="Edit this Note"),
        TodoDAO(
            user=user1,
            title="Note 3",
            content="So many Notes",
        ),
        TodoDAO(user=user1, title="Note 4", content="Reminder: make more Notes"),
    ]
    with db_session() as session:
        session.add_all(users)
        session.add_all(todos)
