"""Centralized logging configuration."""

import logging


def configure_logging(level: int = logging.INFO) -> None:
    logging.basicConfig(level=level)


def get_logger(name: str) -> logging.Logger:
    return logging.getLogger(name)
