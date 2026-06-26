def test_create_customer(client, sample_customer):
    assert sample_customer["full_name"] == "Azad Khan"
    assert sample_customer["email"] == "azad@gmail.com"
    assert sample_customer["phone"] == "9999999999"
    assert "id" in sample_customer


def test_create_customer_duplicate_email(client, sample_customer):
    response = client.post(
        "/api/customers",
        json={
            "full_name": "Another User",
            "email": "azad@gmail.com",
            "phone": "8888888888",
        },
    )
    assert response.status_code == 409
    assert response.json()["success"] is False


def test_list_customers_pagination(client, sample_customer):
    response = client.get("/api/customers", params={"page": 1, "limit": 10})
    assert response.status_code == 200
    data = response.json()
    assert data["total"] >= 1
    assert data["page"] == 1
    assert data["limit"] == 10
