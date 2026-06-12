from jwt import decode

from fast_zero.security import SECRET_KEY, create_assess_token


def test_jwt():
    data = {"test": "test"}
    token = create_assess_token(data)

    decoded = decode(token, SECRET_KEY, algorithms=['HS256'])

    assert decoded['test'] == data["test"]
    assert "exp" in decoded
