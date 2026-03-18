import pytest
from unittest.mock import patch, MagicMock
import os
import sys

sys.path.insert(0, os.path.abspath("lambda/retrieve"))

from retrieve import handler


@patch.dict(os.environ, {"BUCKET_NAME": "test-bucket"})
@patch("retrieve.requests.get")
@patch("retrieve.s3.put_object")
def test_success(mock_put, mock_get):
    mock_get.return_value = MagicMock(
        status_code=200,
        content=b"data"
    )

    result = handler({}, {})

    assert result["status"] == "success"
    mock_get.assert_called_once()
    mock_put.assert_called_once()


@patch.dict(os.environ, {"BUCKET_NAME": "test-bucket"})
@patch("retrieve.requests.get")
def test_http_failure(mock_get):
    mock_get.return_value = MagicMock(status_code=404)

    with pytest.raises(Exception):
        handler({}, {})


@patch.dict(os.environ, {"BUCKET_NAME": "test-bucket"})
@patch("retrieve.requests.get")
@patch("retrieve.s3.put_object")
def test_s3_failure(mock_put, mock_get):
    mock_get.return_value = MagicMock(status_code=200, content=b"data")
    mock_put.side_effect = Exception("S3 error")

    with pytest.raises(Exception):
        handler({}, {})


def test_missing_env():
    with patch.dict(os.environ, {}, clear=True):
        with pytest.raises(Exception):
            handler({}, {})