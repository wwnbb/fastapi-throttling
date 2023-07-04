async def test_read_item(client, flush_redis):
    response = await client.get(
        "/items/foo", headers={"X-Token": "coneofsilence"}
    )
    assert response.status_code == 200
    assert response.json() == {
        "id": "foo",
        "title": "Foo",
        "description": "There goes my hero",
    }

    response = await client.get("/items/foo", headers={"X-Token": "hailhydra"})
    assert response.status_code == 400
    assert response.json() == {"detail": "Invalid X-Token header"}


async def test_read_limit(client, flush_redis):
    for i in range(5):
        response = await client.get(
            "/items/foo", headers={"X-Token": "coneofsilence"}
        )
        assert response.status_code == 200
        assert response.json() == {
            "id": "foo",
            "title": "Foo",
            "description": "There goes my hero",
        }


async def test_read_inexistent_item(client, flush_redis):
    response = await client.get(
        "/items/baz", headers={"X-Token": "coneofsilence"}
    )
    assert response.status_code == 404
    assert response.json() == {"detail": "Item not found"}


async def test_create_item(client, flush_redis):
    response = await client.post(
        "/items/",
        headers={"X-Token": "coneofsilence"},
        json={
            "id": "foobar",
            "title": "Foo Bar",
            "description": "The Foo Barters",
        },
    )
    assert response.status_code == 200
    assert response.json() == {
        "id": "foobar",
        "title": "Foo Bar",
        "description": "The Foo Barters",
    }


async def test_create_item_bad_token(client, flush_redis):
    response = await client.post(
        "/items/",
        headers={"X-Token": "hailhydra"},
        json={"id": "bazz", "title": "Bazz", "description": "Drop the bazz"},
    )
    assert response.status_code == 400
    assert response.json() == {"detail": "Invalid X-Token header"}


async def test_create_existing_item(client, flush_redis):
    response = await client.post(
        "/items/",
        headers={"X-Token": "coneofsilence"},
        json={
            "id": "foo",
            "title": "The Foo ID Stealers",
            "description": "There goes my stealer",
        },
    )
    assert response.status_code == 400
    assert response.json() == {"detail": "Item already exists"}
