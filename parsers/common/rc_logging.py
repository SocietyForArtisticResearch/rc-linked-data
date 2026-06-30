import logging
import logging.handlers
import os


def setup_logger(research_folder, name="parse_rc", retention_days=14):
    """File+console logger that rotates daily and keeps only the last
    `retention_days` log files, so old logs disappear on their own without
    cron/logrotate setup."""
    logger = logging.getLogger(name)
    if logger.handlers:
        return logger

    log_dir = os.path.join(research_folder, "logs")
    os.makedirs(log_dir, exist_ok=True)
    log_path = os.path.join(log_dir, f"{name}.log")

    logger.setLevel(logging.INFO)
    logger.propagate = False

    file_handler = logging.handlers.TimedRotatingFileHandler(
        log_path, when="midnight", interval=1, backupCount=retention_days
    )
    file_handler.setFormatter(logging.Formatter("%(asctime)s %(levelname)s %(message)s"))
    logger.addHandler(file_handler)

    console_handler = logging.StreamHandler()
    console_handler.setFormatter(logging.Formatter("%(levelname)s %(message)s"))
    logger.addHandler(console_handler)

    return logger
