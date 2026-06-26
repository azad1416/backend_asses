import uuid


def test_create_product(client, sample_product):
    assert sample_product["name"] == "iPhone 15"
    assert sample_product["sku"] == "IPH15"
    assert float(sample_product["price"]) == 79999.0
    assert sample_product["stock_quantity"] == 50
    assert "id" in sample_product


def test_create_product_duplicate_sku(client, sample_product):
    response = client.post(
        "/api/products",
        json={
            "name": "iPhone 15 Pro",
            "sku": "IPH15",
            "price": 89999,
            "stock_quantity": 30,
        },
    )
    assert response.status_code == 409
    assert response.json()["success"] is False


def test_list_products_with_search(client, sample_product):
    response = client.get("/api/products", params={"search": "iphone"})
    assert response.status_code == 200
    data = response.json()
    assert data["total"] >= 1
    assert any(p["sku"] == "IPH15" for p in data["items"])


def test_get_product_not_found(client):
    response = client.get(f"/api/products/{uuid.uuid4()}")
    assert response.status_code == 404


def test_delete_product(client, sample_product):
    product_id = sample_product["id"]
    response = client.delete(f"/api/products/{product_id}")
    assert response.status_code == 200

    get_response = client.get(f"/api/products/{product_id}")
    assert get_response.status_code == 404

