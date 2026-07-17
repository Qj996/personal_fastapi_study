from http import HTTPStatus

from fast_zero.schemas import UserPublic


def test_create_user(client):
    response = client.post(
        '/users/create_user',
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
        '/users',
    )

    assert response.status_code == HTTPStatus.OK
    assert response.json() == {'users': []}


def test_read_users_with_users(client, user):
    user_schema = UserPublic.model_validate(user).model_dump()
    response = client.get('/users/')
    assert response.json() == {'users': [user_schema]}


# 测试更新的唯一存在错误
def test_update_error(client, user):
    client.post(
        '/users/create_user',
        json={
            'username': 'fausto',
            'email': 'bob@example.com',
            'password': '12345678',
        },
    )

    token_response = client.post(
        '/auth/token',
        data={'username': user.email, 'password': user.clean_password},
    )
    token = token_response.json()['access_token']

    response_update = client.put(
        f'/users/{user.id}',
        json={
            'username': 'fausto',
            'email': 'bob@example.com',
            'password': 'bobpassword',
        },
        headers={'Authorization': f'Bearer {token}'},
    )

    assert response_update.status_code == HTTPStatus.CONFLICT
    assert response_update.json() == {
        'detail': 'Username or Email already exists'
    }


def test_put_user(client, user):
    token_response = client.post(
        'auth/token',
        data={'username': user.email, 'password': user.clean_password},
    )
    token = token_response.json()['access_token']

    response = client.put(
        f'/users/{user.id}',
        json={
            'username': 'bob',
            'email': 'bob@example.com',
            'password': 'bobpassword',
        },
        headers={'Authorization': f'Bearer {token}'},
    )
    print(response.status_code)
    print(response.json())   # 关键：打印错误详情
    assert response.status_code == HTTPStatus.OK
    assert response.json() == {
        'username': 'bob',
        'email': 'bob@example.com',
        'id': user.id,
    }


def test_delete_user(client, user):
    token_response = client.post(
        '/auth/token',
        data={'username': user.email, 'password': user.clean_password},
    )
    token = token_response.json()['access_token']

    response = client.delete(
        f'/users/{user.id}',
        headers={'Authorization': f'Bearer {token}'},
    )
    assert response.status_code == HTTPStatus.OK
    assert response.json() == {'message': 'User has deleted'}
