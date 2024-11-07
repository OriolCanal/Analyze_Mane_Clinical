import logging
import os
from datetime import datetime
from pathlib import Path

class Logger:
    def __init__(self, name="AppLogger", log_file=None, level=logging.INFO):
        """
        Initializes a logger instance.

        Args:
            name (str): The name of the logger.
            log_file (str): Path to the log file. If None, logs to console only.
            level (int): Logging level (e.g., logging.INFO, logging.DEBUG).
        """
        self.logger = logging.getLogger(name)
        self.logger.setLevel(level)

        # Prevent adding handlers repeatedly if multiple instances are created
        if not self.logger.hasHandlers():
            formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
            
            # Console handler
            console_handler = logging.StreamHandler()
            console_handler.setFormatter(formatter)
            self.logger.addHandler(console_handler)
            
            # File handler, if specified
            if log_file:
                file_handler = logging.FileHandler(log_file)
                file_handler.setFormatter(formatter)
                self.logger.addHandler(file_handler)

    def info(self, message):
        """Logs an informational message."""
        self.logger.info(message)

    def debug(self, message):
        """Logs a debug message."""
        self.logger.debug(message)

    def warning(self, message):
        """Logs a warning message."""
        self.logger.warning(message)

    def error(self, message):
        """Logs an error message."""
        self.logger.error(message)

    def critical(self, message):
        """Logs a critical error message."""
        self.logger.critical(message)

# Define the path to the log file
log_file = os.path.join(str(Path(__file__).resolve().parents[1]), "Mane_clinical.log")

Log = Logger("Mane_clinical_logger", log_file)


# Usage Example
if __name__ == "__main__":
    # Define log file path with a timestamp
    log_file = f"/home/ocanal/Desktop/vep_with_gffmane_clinical.log"
    logger = Logger(name="MyAppLogger", log_file=log_file, level=logging.DEBUG)

    # Logging messages
    logger.info("This is an info message.")
    logger.debug("This is a debug message.")
    logger.warning("This is a warning message.")
    logger.error("This is an error message.")
    logger.critical("This is a critical error message.")