import pytest

from incident_ai.ingest import InputFormatError, normalize_input


def test_auto_extracts_messages_from_json_lines() -> None:
    text = (
        '{"MESSAGE":"No space left on device","PRIORITY":"3"}\n'
        '{"message":"Could not resolve host: api.internal","service":"worker"}'
    )

    normalized = normalize_input(text)

    assert normalized == "No space left on device\nCould not resolve host: api.internal"


def test_auto_preserves_mixed_input_as_plain_text() -> None:
    text = '{"message":"Permission denied"}\nplain text line'
    assert normalize_input(text) == text


def test_jsonl_falls_back_to_serialized_record_without_message_key() -> None:
    normalized = normalize_input('{"error":"Permission denied","service":"api"}', "jsonl")
    assert normalized == '{"error":"Permission denied","service":"api"}'


def test_jsonl_rejects_invalid_json() -> None:
    with pytest.raises(InputFormatError, match="invalid JSON on line 2"):
        normalize_input('{"message":"ok"}\nnot-json', "jsonl")


def test_jsonl_rejects_non_object_records() -> None:
    with pytest.raises(InputFormatError, match="must contain an object"):
        normalize_input('["Permission denied"]', "jsonl")
