from app import app
from models import db, User, TaskList, Task, TaskAssignment, Comment, Notification
from datetime import datetime

# Create a Flask app context
with app.app_context():
    # Drop and recreate tables
    db.drop_all()
    db.create_all()

    # Create users
    user1 = User(username="john_doe", email="john@example.com", password="hashedpassword1", role="user", notifications_enabled=True)
    user2 = User(username="jane_smith", email="jane@example.com", password="hashedpassword2", role="user", notifications_enabled=True)

    db.session.add_all([user1, user2])
    db.session.commit()

    # Create task lists
    tasklist1 = TaskList(name="Work Tasks", user_id=user1.id)
    tasklist2 = TaskList(name="Home Tasks", user_id=user2.id)

    db.session.add_all([tasklist1, tasklist2])
    db.session.commit()

    # Create tasks
    task1 = Task(
        title="Finish report", 
        description="Complete the annual report.", 
        due_date=datetime(2025, 3, 1),
        priority="high", 
        status="todo", 
        tasklist_id=tasklist1.id
    )
    task2 = Task(
        title="Buy groceries", 
        description="Milk, eggs, bread.", 
        due_date=datetime(2025, 3, 2),
        priority="low", 
        status="todo", 
        tasklist_id=tasklist2.id
    )

    db.session.add_all([task1, task2])
    db.session.commit()

    # Assign tasks
    assignment1 = TaskAssignment(user_id=user1.id, task_id=task1.id)
    assignment2 = TaskAssignment(user_id=user2.id, task_id=task2.id)

    db.session.add_all([assignment1, assignment2])
    db.session.commit()

    # Add comments
    comment1 = Comment(content="This task is urgent!", task_id=task1.id, user_id=user1.id)
    comment2 = Comment(content="I'll do it tomorrow.", task_id=task2.id, user_id=user2.id)

    db.session.add_all([comment1, comment2])
    db.session.commit()

    # Add notifications
    notification1 = Notification(message="Task assigned to you.", user_id=user1.id, task_id=task1.id)
    notification2 = Notification(message="Task updated.", user_id=user2.id, task_id=task2.id)

    db.session.add_all([notification1, notification2])
    db.session.commit()

    print("Database seeded successfully!")
