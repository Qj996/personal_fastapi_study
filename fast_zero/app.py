from http import HTTPStatus

from fastapi import FastAPI
from fastapi.responses import HTMLResponse

from fast_zero.routers import auth, users

app = FastAPI()
app.include_router(users.router)
app.include_router(auth.router)


@app.get('/')
def read_root():
    return {'message': 'Olá Mundo!'}


@app.get('/test', status_code=HTTPStatus.OK, response_class=HTMLResponse)
def my_try():
    return """
    <html>
      <head>
        <title>Hello World !</title>
      </head>
      <body>
        <h1>Hello World</h1>
      </body>
    </html>
    """
