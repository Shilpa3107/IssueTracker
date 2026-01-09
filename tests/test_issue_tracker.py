import pytest

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

    # Create a user (using the new endpoint)
    res_user = client.post("/users/", json={"name": "Tester", "email": "tester@example.com"})
    assert res_user.status_code == 201
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
# BULK UPDATE
# ----------------------
def test_bulk_status_update(client):
    # Create two issues
    i1 = client.post("/issues/", json={"title": "Issue 1"}).json()["id"]
    i2 = client.post("/issues/", json={"title": "Issue 2"}).json()["id"]

    # Bulk update
    updates = [
        {"issue_id": i1, "status": "IN_PROGRESS"},
        {"issue_id": i2, "status": "DONE"}
    ]
    res = client.post("/issues/bulk-status", json=updates)
    assert res.status_code == 200
    
    # Verify
    assert client.get(f"/issues/{i1}").json()["status"] == "IN_PROGRESS"
    assert client.get(f"/issues/{i2}").json()["status"] == "DONE"

# ----------------------
# CSV IMPORT
# ----------------------
def test_csv_import(client):
    csv_content = "title,description,assignee_email\nCSV Issue 1,Desc 1,\nCSV Issue 2,Desc 2,\n"
    files = {"file": ("issues.csv", csv_content, "text/csv")}
    res = client.post("/issues/import", files=files)
    assert res.status_code == 200
    data = res.json()
    assert data["success"] == 2

# ----------------------
# BONUS: TIMELINE
# ----------------------
def test_timeline(client):
    # Create issue
    res = client.post("/issues/", json={"title": "Timeline Issue"})
    issue_id = res.json()["id"]

    # Update status
    client.patch(f"/issues/{issue_id}", json={"status": "DONE", "version": 1})

    # Get timeline
    res_timeline = client.get(f"/issues/{issue_id}/timeline")
    assert res_timeline.status_code == 200
    events = res_timeline.json()
    assert len(events) >= 2
    assert "Issue created" in events[0]["action"]
    assert "Status changed" in events[1]["action"]

# ----------------------
# FILTERING
# ----------------------
def test_filtering(client):
    # Create issues with different statuses
    client.post("/issues/", json={"title": "Open Issue"})
    i2 = client.post("/issues/", json={"title": "Done Issue"})
    client.patch(f"/issues/{i2.json()['id']}", json={"status": "DONE", "version": 1})

    # Filter for DONE
    res = client.get("/issues/?status=DONE")
    assert res.status_code == 200
    issues = res.json()
    assert all(i["status"] == "DONE" for i in issues)
    assert len(issues) >= 1
