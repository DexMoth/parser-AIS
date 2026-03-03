#!/usr/bin/env python
import sys
import logging
from pathlib import Path
from src.main_window import MainWindow

logger = logging.getLogger(__name__)

def main():
    try:
        app = MainWindow()
        app.run()
        
    except Exception as e:
        print(f"!!! ошибка: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()