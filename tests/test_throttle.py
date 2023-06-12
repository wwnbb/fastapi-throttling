def test_throttle_by_ip(client, flush_redis):
    for i in range(5):
        response = client.get(
            "/items/foo",
            headers={
                "X-Token": "coneofsilence",
                "x-forwarded-for": "211.98.250.118",
            },
        )
        assert response.status_code == 200
        assert response.json() == {
            "id": "foo",
            "title": "Foo",
            "description": "There goes my hero",
        }

    response = client.get(
        "/items/foo",
        headers={
            "X-Token": "coneofsilence",
            "x-forwarded-for": "211.98.250.118",
        },
    )
    assert response.status_code == 429
    assert response.json() == {'detail': 'Too Many Requests'}

    for i in range(5):
        response = client.get(
            "/items/foo",
            headers={
                "X-Token": "coneofsilence",
                "x-forwarded-for": "211.98.250.119",
            },
        )
        assert response.status_code == 200
        assert response.json() == {
            "id": "foo",
            "title": "Foo",
            "description": "There goes my hero",
        }


def test_throttle_by_authorization(client, flush_redis):
    for i in range(5):
        response = client.get(
            "/items/foo",
            headers={
                "X-Token": "coneofsilence",
                "x-forwarded-for": "211.98.250.118",
                "Authorization": "c226da0d0517a73dc4b82e5b43344f59",
            },
        )
        assert response.status_code == 200
        assert response.json() == {
            "id": "foo",
            "title": "Foo",
            "description": "There goes my hero",
        }

    response = client.get(
        "/items/foo",
        headers={
            "X-Token": "coneofsilence",
            "x-forwarded-for": "211.98.250.119",
            "Authorization": "c226da0d0517a73dc4b82e5b43344f59",
        },
    )
    assert response.status_code == 429
    assert response.json() == {'detail': 'Too Many Requests'}
