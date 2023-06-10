import fastapi
import pytest


@pytest.fixture
def app():
    app = fastapi.FastAPI()

    @app.get("/")
    def hello_world():
        return {"Hello": "World"}

    return app
