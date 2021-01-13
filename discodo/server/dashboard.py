import os.path

from sanic import Blueprint, response

__directory__ = os.path.dirname(os.path.realpath(__file__))

app = Blueprint(__name__)

app.static("/static", os.path.join(__directory__, "static"))


class Templates:
    __dirname = os.path.join(__directory__, "templates")

    with open(os.path.join(__dirname, "login.html"), "r") as fp:
        Login = fp.read()

    with open(os.path.join(__dirname, "board.html"), "r") as fp:
        Board = fp.read()


@app.get("/dashboard")
async def dashboard(request):
    return response.html(Templates.Board)
