import cv2
import time
from PySide6.QtCore import QThread, Signal
import numpy as np

class CameraThread(QThread):
    change_pixmap_signal = Signal(np.ndarray)
    plate_detected_signal = Signal(dict)

    def __init__(self, source=0, engine=None, db=None, camera_id=0):
        super().__init__()
        self.source = source
        self.engine = engine
        self.db = db
        self.camera_id = camera_id
        self._run_flag = True
        self.last_p = "" # Aynı plakayı üst üste basmamak için
        self.last_t = 0

    def run(self):
        # RTSP veya Kamera kaynağını aç
        source = int(self.source) if str(self.source).isdigit() else self.source
        cap = cv2.VideoCapture(source)
        cap.set(cv2.CAP_PROP_BUFFERSIZE, 1) # Gecikmeyi önler
        
        last_process_time = 0
        process_interval = 0.1 # GPU kullandığımız için hızı artırdık (0.5 çok yavaştı)

        while self._run_flag:
            ret, frame = cap.read()
            if ret:
                current_time = time.time()
                
                # İŞLEME VE ANALİZ
                if self.engine and (current_time - last_process_time > process_interval):
                    # DÜZELTME: İki değer alıyoruz (results ve çizimli frame)
                    results, annotated_frame = self.engine.detect_and_recognize(frame)
                    
                    # Çizimli görüntüyü ekrana bas
                    self.change_pixmap_signal.emit(annotated_frame)
                    
                    for res in results:
                        plate_text = res['plate']
                        
                        # Aynı plakayı 5 saniye bekleterek logla (Spam önleme)
                        if plate_text != self.last_p or (current_time - self.last_t > 5):
                            status = self.db.get_plate_status(plate_text) if self.db else 'Guest'
                            
                            if self.db and hasattr(self.db, 'log_detection'):
                                self.db.log_detection(plate_text, status)
                            
                            detection_data = {
                                'camera_id': self.camera_id,
                                'plate': plate_text,
                                'status': status,
                                'crop': res['crop'],
                                'timestamp': time.strftime("%H:%M:%S")
                            }
                            # SON AKTİVİTEYE GÖNDER
                            self.plate_detected_signal.emit(detection_data)
                            
                            self.last_p = plate_text
                            self.last_t = current_time
                    
                    last_process_time = current_time
                else:
                    # Analiz yapılmayan karelerde orijinal görüntüyü bas
                    self.change_pixmap_signal.emit(frame)

            else:
                if isinstance(self.source, str):
                    cap.set(cv2.CAP_PROP_POS_FRAMES, 0)
                else:
                    time.sleep(1)
            
            time.sleep(0.01)

        cap.release()

    def stop(self):
        self._run_flag = False
        self.wait()