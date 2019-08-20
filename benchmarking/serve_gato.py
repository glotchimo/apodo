from gato import Gato, Request

app = Gato("Test Server")


@app.view("/")
async def hello(request: Request):
    """ Returns a "Hello world!" response. """
    return "Hello world!"


if __name__ == "__main__":
    app.serve()
