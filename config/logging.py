import logging
import sys
from pathlib import Path


def setup_logging() -> None:
    log_dir = Path("data/logs")
    log_dir.mkdir(parents=True, exist_ok=True)

    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s | %(name)s | %(levelname)s | %(message)s",
        handlers=[
            logging.StreamHandler(sys.stdout),
            logging.FileHandler(
                log_dir / "bot.log", encoding="utf-8", mode="a"
            ),
        ],
    )
