import pytest
import os
from core.database import DatabaseManager

@pytest.fixture
def db():
    db_path = 'data/test_lpr.db'
    if os.path.exists(db_path):
        os.remove(db_path)
    manager = DatabaseManager(db_path=db_path)
    yield manager
    if os.path.exists(db_path):
        os.remove(db_path)

def test_add_get_plate(db):
    assert db.add_plate("34ABC123", "Allowed")
    assert db.get_plate_status("34ABC123") == "Allowed"
    
def test_guest_plate(db):
    assert db.get_plate_status("UNKNOWN") == "Guest"

def test_delete_plate(db):
    db.add_plate("34XYZ789", "Banned")
    assert db.get_plate_status("34XYZ789") == "Banned"
    assert db.delete_plate("34XYZ789")
    assert db.get_plate_status("34XYZ789") == "Guest"

def test_log_detection(db):
    assert db.log_detection("34ABC123", "Allowed")
    logs = db.get_recent_logs()
    assert len(logs) > 0
    assert logs[0][0] == "34ABC123"
