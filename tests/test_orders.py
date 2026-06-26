def test_create_order(client, sample_product, sample_customer):
    response = client.post(
        "/api/orders",
        json={
            "customer_id": sample_customer["id"],
            "items": [
                {"product_id": sample_product["id"], "quantity": 2},
            ],
        },
    )
    assert response.status_code == 201
    data = response.json()
    assert data["status"] == "pending"
    assert float(data["total_amount"]) == 159998.0
    assert len(data["items"]) == 1
    assert data["customer"]["email"] == "azad@gmail.com"

    product_response = client.get(f"/api/products/{sample_product['id']}")
    assert product_response.json()["stock_quantity"] == 48


def test_create_order_insufficient_inventory(client, sample_product, sample_customer):
    response = client.post(
        "/api/orders",
        json={
            "customer_id": sample_customer["id"],
            "items": [
                {"product_id": sample_product["id"], "quantity": 100},
            ],
        },
    )
    assert response.status_code == 400
    assert "Insufficient inventory" in response.json()["message"]


def test_cancel_order_restores_inventory(client, sample_product, sample_customer):
    create_response = client.post(
        "/api/orders",
        json={
            "customer_id": sample_customer["id"],
            "items": [
                {"product_id": sample_product["id"], "quantity": 5},
            ],
        },
    )
    order_id = create_response.json()["id"]

    product_before = client.get(f"/api/products/{sample_product['id']}")
    assert product_before.json()["stock_quantity"] == 45

    cancel_response = client.delete(f"/api/orders/{order_id}")
    assert cancel_response.status_code == 200
    assert cancel_response.json()["status"] == "cancelled"

    product_after = client.get(f"/api/products/{sample_product['id']}")
    assert product_after.json()["stock_quantity"] == 50


def test_create_order_invalid_customer(client, sample_product):
    import uuid

    response = client.post(
        "/api/orders",
        json={
            "customer_id": str(uuid.uuid4()),
            "items": [
                {"product_id": sample_product["id"], "quantity": 1},
            ],
        },
    )
    assert response.status_code == 404
