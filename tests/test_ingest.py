import pytest

from incident_ai.ingest import InputFormatError, normalize_grouped_input, normalize_input


def test_auto_extracts_messages_from_json_lines() -> None:
    text = (
        '{"MESSAGE":"No space left on device","PRIORITY":"3"}\n'
        '{"message":"Could not resolve host: api.internal","service":"worker"}'
    )

    normalized = normalize_input(text)

    assert normalized == "No space left on device\nCould not resolve host: api.internal"


def test_auto_can_preserve_structured_source_context() -> None:
    text = (
        '{"MESSAGE":"No space left on device","_HOSTNAME":"web-01","_SYSTEMD_UNIT":"worker.service","_PID":"42"}\n'
        '{"message":"Could not resolve host: api.internal","service":"api","container_name":"api-1"}'
    )

    normalized = normalize_input(text, include_context=True)

    assert normalized == (
        "[host=web-01 unit=worker.service pid=42] No space left on device\n"
        "[service=api container=api-1] Could not resolve host: api.internal"
    )


def test_context_prefers_journald_identifiers_over_generic_fields() -> None:
    text = '{"MESSAGE":"Permission denied","SYSLOG_IDENTIFIER":"nginx","service":"fallback"}'
    assert normalize_input(text, "jsonl", include_context=True) == "[service=nginx] Permission denied"


def test_source_filters_select_matching_records() -> None:
    text = (
        '{"MESSAGE":"No space left on device","_HOSTNAME":"web-01","_SYSTEMD_UNIT":"api.service"}\n'
        '{"MESSAGE":"Permission denied","_HOSTNAME":"web-02","_SYSTEMD_UNIT":"api.service"}\n'
        '{"MESSAGE":"Could not resolve host: db.internal","_HOSTNAME":"web-01","_SYSTEMD_UNIT":"worker.service"}'
    )

    normalized = normalize_input(
        text,
        source_filters={"host": "web-01", "unit": "api.service"},
        include_context=True,
    )

    assert normalized == "[host=web-01 unit=api.service] No space left on device"


def test_source_filters_support_generic_application_fields() -> None:
    text = (
        '{"message":"Permission denied","service":"api","container_name":"api-1"}\n'
        '{"message":"No space left on device","service":"worker","container_name":"worker-1"}'
    )

    assert normalize_input(text, source_filters={"service": "api", "container": "api-1"}) == "Permission denied"


def test_source_filters_require_structured_input() -> None:
    with pytest.raises(InputFormatError, match="structured grouping and source filters require JSON Lines input"):
        normalize_input("Permission denied", "text", source_filters={"host": "web-01"})


def test_auto_with_source_filters_rejects_mixed_input() -> None:
    with pytest.raises(InputFormatError, match="invalid JSON on line 2"):
        normalize_input('{"message":"Permission denied"}\nplain text line', source_filters={"service": "api"})


def test_grouped_input_partitions_records_by_host() -> None:
    text = (
        '{"MESSAGE":"No space left on device","_HOSTNAME":"web-01"}\n'
        '{"MESSAGE":"filesystem /var 100%","_HOSTNAME":"web-02"}\n'
        '{"MESSAGE":"Permission denied","_HOSTNAME":"web-01"}'
    )

    grouped = normalize_grouped_input(text, "host", include_context=True)

    assert grouped == {
        "web-01": "[host=web-01] No space left on device\n[host=web-01] Permission denied",
        "web-02": "[host=web-02] filesystem /var 100%",
    }


def test_grouped_input_keeps_records_without_group_metadata() -> None:
    grouped = normalize_grouped_input('{"MESSAGE":"Permission denied"}', "service")
    assert grouped == {"<unknown>": "Permission denied"}


def test_grouped_input_applies_source_filters_before_grouping() -> None:
    text = (
        '{"MESSAGE":"Permission denied","_HOSTNAME":"web-01","_SYSTEMD_UNIT":"api.service"}\n'
        '{"MESSAGE":"No space left on device","_HOSTNAME":"web-02","_SYSTEMD_UNIT":"worker.service"}'
    )

    grouped = normalize_grouped_input(text, "host", source_filters={"unit": "api.service"})

    assert grouped == {"web-01": "Permission denied"}


def test_grouped_input_requires_structured_input() -> None:
    with pytest.raises(InputFormatError, match="structured grouping and source filters require JSON Lines input"):
        normalize_grouped_input("Permission denied", "host", "text")


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
