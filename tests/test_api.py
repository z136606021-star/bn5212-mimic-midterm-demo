from fastapi.testclient import TestClient
from ml.app.main import app

def test_health_and_tasks():
    with TestClient(app) as c:
        assert c.get('/api/health').status_code==200
        r=c.get('/api/tasks'); assert r.status_code==200 and len(r.json()['tasks'])==4

def test_invalid_prediction_input():
    with TestClient(app) as c:
        assert c.post('/api/demo/predict',json={"task":"mortality"}).status_code==422

def test_summary_is_json_safe():
    with TestClient(app) as c:
        r=c.get("/api/summary"); assert r.status_code==200 and r.json()["cohort"]["stays"]>0
