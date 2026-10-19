"""Functional tests for the original Flask application (templates, upload form, history)."""

import io

import pytest


@pytest.fixture()
def fclient(sandbox, flask_module):
    flask_module.app.config["TESTING"] = True
    return flask_module.app.test_client()


def test_home_page_has_upload_form(fclient):
    r = fclient.get("/")
    assert r.status_code == 200 and b"xray_image" in r.data


def test_about_page(fclient):
    assert fclient.get("/about").status_code == 200


def test_empty_history_page(fclient):
    assert fclient.get("/history").status_code == 200


def test_unknown_result_redirects_home(fclient):
    r = fclient.get("/result/999")
    assert r.status_code == 302 and r.headers["Location"].endswith("/")


def test_post_without_file_redirects_with_message(fclient):
    r = fclient.post("/predict", follow_redirects=True)
    assert r.status_code == 200 and b"No file part" in r.data


def test_unsupported_type_is_rejected(fclient, sample_bytes):
    r = fclient.post("/predict", data={"xray_image": (io.BytesIO(sample_bytes()), "scan.gif")},
                     content_type="multipart/form-data", follow_redirects=True)
    assert b"Unsupported file type" in r.data


def test_upload_flows_through_to_result_and_history(fclient, sample_bytes):
    r = fclient.post("/predict", data={"xray_image": (io.BytesIO(sample_bytes("viral")), "case.jpg")},
                     content_type="multipart/form-data")
    assert r.status_code == 302 and "/result/1" in r.headers["Location"]
    page = fclient.get("/result/1")
    assert page.status_code == 200 and b"Prediction:" in page.data and b"Grad-CAM" in page.data
    assert b"case.jpg" in fclient.get("/history").data


def test_oversize_body_is_refused(fclient):
    r = fclient.post("/predict", data={"xray_image": (io.BytesIO(b"0" * (8 * 1024 * 1024 + 100)), "big.jpg")},
                     content_type="multipart/form-data")
    assert r.status_code == 413
