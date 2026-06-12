from http import HTTPStatus

from fast_zero.schemas import UserPublic


def test_root_dever(client):
    response = client.get('/')
    assert response.status_code == HTTPStatus.OK
    assert response.json() == {'message': 'Olá Mundo!'}


def test_my_try(client):
    response = client.get('/test')
    assert response.status_code == HTTPStatus.OK


def test_create_user(client):
    response = client.post(
        '/create_user',
        json={
            'username': 'alice',
            'email': 'test@example.com',
            'password': '123456',
        },
    )

    assert response.status_code == HTTPStatus.CREATED
    assert response.json() == {
        'id': 1,
        'username': 'alice',
        'email': 'test@example.com',
    }


def test_read_users(client):
    response = client.get(
        "/users",
    )

    assert response.status_code == HTTPStatus.OK
    assert response.json() == {"users": []}


def test_read_users_with_users(client, user):
    user_schema = UserPublic.model_validate(user).model_dump()
    response = client.get("/users/")
    assert response.json() == {"users": [user_schema]}


# 测试更新的唯一存在错误
def test_update_error(client, user):
    client.post(
        "/create_user",
        json={
            "username": "fausto",
            "email": "bob@example.com",
            "password": "12345678"
        }
    )

    response_update = client.put(
        f"/users/{user.id}",
        json={
            "username": "fausto",
            "email": "bob@example.com",
            "password": "bobpassword"
        }
    )

    assert response_update.status_code == HTTPStatus.CONFLICT
    assert response_update.json() == {
        "detail": "Username or Email already exists"
    }


def test_put_user(client, user):
    response = client.put(
        "/users/1",
        json={
            "username": "bob",
            "email": "bob@example.com",
            "password": "bobpassword"
        }
    )

    assert response.status_code == HTTPStatus.OK
    assert response.json() == {
        "username": "bob",
        "email": "bob@example.com",
        "id": 1,
    }


def test_delete_user(client, user):
    response = client.delete("/users/1")
    assert response.status_code == HTTPStatus.OK
    assert response.json() == {
        "message": "User has deleted"
    }
