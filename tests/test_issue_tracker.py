import io
import csv

# ----------------------
# ISSUE CREATION
# ----------------------
def test_create_issue(client):
    response = client.post("/issues/", json={"title": "Test Issue", "description": "Test Desc"})
    assert response.status_code == 201
    data = response.json()
    assert data["title"] == "Test Issue"
    assert data["version"] == 1

# ----------------------
# VERSION CONFLICT
# ----------------------
def test_issue_version_conflict(client):
    # First, create an issue
    res = client.post("/issues/", json={"title": "Conflict Issue"})
    issue_id = res.json()["id"]

    # Try to update with wrong version
    res2 = client.patch(f"/issues/{issue_id}", json={"title": "Updated", "version": 999})
    assert res2.status_code == 409  # Version conflict

# ----------------------
# COMMENT CREATION
# ----------------------
def test_add_comment(client):
    # Create an issue
    res = client.post("/issues/", json={"title": "Comment Issue"})
    issue_id = res.json()["id"]

    # Create a user
    res_user = client.post("/users/", json={"name": "Tester", "email": "tester@example.com"})
    user_id = res_user.json()["id"]

    # Add comment
    res_comment = client.post(f"/issues/{issue_id}/comments/", json={"author_id": user_id, "body": "Nice work"})
    assert res_comment.status_code == 201
    assert res_comment.json()["body"] == "Nice work"

# ----------------------
# LABEL REPLACEMENT
# ----------------------
def test_replace_labels(client):
    # Create issue
    res = client.post("/issues/", json={"title": "Label Issue"})
    issue_id = res.json()["id"]

    # Replace labels
    res_labels = client.put(f"/issues/{issue_id}/labels", json=["bug", "urgent"])
    assert res_labels.status_code == 200
    data = res_labels.json()
    labels = [l["name"] for l in data["labels"]]
    assert "bug" in labels
    assert "urgent" in labels

# ----------------------
# CSV IMPORT
# ----------------------
def test_csv_import(client):
    csv_content = "title,description,assignee_email\nCSV Issue,Desc,\n"
    file = {"file": ("issues.csv", csv_content, "text/csv")}
    res = client.post("/issues/import", files=file)
    assert res.status_code == 200
    data = res.json()
    assert data["success"] == 1
