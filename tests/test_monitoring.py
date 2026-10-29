"""Tests for Sentry monitoring integration."""

from crystalia_collector.monitoring import init_monitoring


def test_init_monitoring_no_dsn_does_nothing():
    """init_monitoring with no DSN and no env var does nothing (smoke test)."""
    from unittest.mock import patch

    with patch.dict("os.environ", {}, clear=True):
        init_monitoring()  # Should not raise


def test_trace_context_is_none_without_active_client():
    import sentry_sdk

    from crystalia_collector.monitoring import trace_context

    assert trace_context(sentry_sdk.start_span(op="task_file")) is None


def test_traced_worker_without_headers_matches_plain_processing(tmp_path):
    from crystalia_collector.work import _process_task_file, _process_task_file_traced

    data = tmp_path / "a.txt"
    data.write_text("hello")
    task = tmp_path / "task_1"
    task.write_text(f"{data} 5 md5-8gb 0 0\n")

    assert _process_task_file_traced(str(task), None, None) == _process_task_file(str(task))


def test_trace_context_carries_trace_id_when_client_active():
    import sentry_sdk

    from crystalia_collector.monitoring import cli_transaction, trace_context

    sentry_sdk.init(dsn="http://k@127.0.0.1:1/1", traces_sample_rate=1.0, shutdown_timeout=0)
    try:
        with cli_transaction("t") as txn:
            span = sentry_sdk.start_span(op="task_file")
            headers = trace_context(span)
            assert headers is not None
            assert headers["sentry-trace"].startswith(txn.trace_id)
    finally:
        client = sentry_sdk.get_client()
        client.close()
        for scope in (sentry_sdk.get_global_scope(), sentry_sdk.get_isolation_scope(), sentry_sdk.get_current_scope()):
            scope.set_client(None)
