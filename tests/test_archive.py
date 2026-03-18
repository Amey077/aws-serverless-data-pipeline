import pytest
from unittest.mock import patch, MagicMock
import os
import sys

sys.path.insert(0, os.path.abspath("lambda/archive"))

from archive import handler


def mock_event():
    return {
        "Records": [
            {
                "s3": {
                    "object": {
                        "key": "raw_data/2026-03-18/2m_sales_records.zip"
                    }
                }
            }
        ]
    }


@patch.dict(os.environ, {"BUCKET_NAME": "test-bucket"})
@patch("archive.s3.delete_object")
@patch("archive.s3.copy_object")
def test_success(mock_copy, mock_delete):
    result = handler(mock_event(), {})

    assert result["status"] == "success"
    mock_copy.assert_called_once()
    mock_delete.assert_called_once()


@patch.dict(os.environ, {"BUCKET_NAME": "test-bucket"})
@patch("archive.s3.copy_object")
def test_copy_failure(mock_copy):
    mock_copy.side_effect = Exception("Copy failed")

    with pytest.raises(Exception):
        handler(mock_event(), {})


@patch.dict(os.environ, {"BUCKET_NAME": "test-bucket"})
@patch("archive.s3.delete_object")
@patch("archive.s3.copy_object")
def test_delete_failure(mock_copy, mock_delete):
    mock_copy.return_value = {}
    mock_delete.side_effect = Exception("Delete failed")

    with pytest.raises(Exception):
        handler(mock_event(), {})