import sys
import os
from PySide6.QtWidgets import QApplication
from core.database import DatabaseManager
from core.lpr_engine import LPREngine
from core.camera_thread import CameraThread
from gui.main_window import MainWindow

def main():
    app = QApplication(sys.argv)
    
    db = DatabaseManager()
    engine = LPREngine()
    
    sources = [0, "mock_source_1.mp4", "mock_source_2.mp4", "mock_source_3.mp4"]
    camera_threads = []
    
    for i, source in enumerate(sources):
        thread = CameraThread(source=source, engine=engine, db=db, camera_id=i)
        camera_threads.append(thread)
        thread.start()
        
    window = MainWindow(db, camera_threads)
    window.show()
    
    try:
        sys.exit(app.exec())
    finally:
        for thread in camera_threads:
            thread.stop()

if __name__ == "__main__":
    main()
