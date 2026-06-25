from docpage2md_app.run_logger import RunLogger


def test_run_logger_writes_chinese_progress_messages(tmp_path, capsys):
    log_path = tmp_path / "process.log"
    logger = RunLogger(log_path, echo=True)

    logger.info("Hybrid crop vision batch start: blocks=12, workers=6")
    logger.info("Hybrid Brain batch start: pages=4, workers=4")
    logger.info("Hybrid crop vision batch done: blocks=12, succeeded=11, failed=1, elapsed=8.5s")
    logger.info("Hybrid Brain batch done: pages=4, statuses=ok:3;partial:1, elapsed=30.2s")
    logger.info("Markdown rendering done: pages=4, elapsed=0.2s")

    captured = capsys.readouterr()
    log_text = log_path.read_text(encoding="utf-8")

    assert "开始并行识别裁剪块：裁剪块=12，并发=6" in log_text
    assert "开始并行 Brain 精修：页数=4，并发=4" in log_text
    assert "裁剪块并行识别完成：总数=12，成功=11，失败=1，耗时=8.5秒" in log_text
    assert "Brain 并行精修完成：页数=4，状态=正常:3；部分完成:1，耗时=30.2秒" in log_text
    assert "Markdown 渲染完成：页数=4，耗时=0.2秒" in log_text
    assert "Hybrid crop vision batch start" not in log_text
    assert "开始并行识别裁剪块" in captured.out
