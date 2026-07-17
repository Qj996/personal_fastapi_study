from http import HTTPStatus


def test_root_dever(client):
    response = client.get('/')
    assert response.status_code == HTTPStatus.OK
    assert response.json() == {'message': 'Olá Mundo!'}


def test_my_try(client):
    response = client.get('/test')
    assert response.status_code == HTTPStatus.OK
