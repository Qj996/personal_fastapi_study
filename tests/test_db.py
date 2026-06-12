from dataclasses import asdict

from sqlalchemy import select

from fast_zero.models import User


def test_user_db(session, mock_db_time):

    with mock_db_time(model=User) as time:
        new_user = User(
            username="alice",
            email="test111@example.com",
            password="123456")
        session.add(new_user)
        session.commit()
    user = session.scalar(select(User).where(User.username == "alice"))
    assert asdict(user) == {
        "id": 1,
        "username": user.username,
        "password": user.password,
        "email": user.email,
        "created_at": time
    }
