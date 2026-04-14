import cv2
import numpy as np
import os
try:
    from openvino.runtime import Core
except ImportError:
    Core = None

try:
    from paddleocr import PaddleOCR
except ImportError:
    PaddleOCR = None

class LPREngine:
    def __init__(self, model_path='models/license_plate_detector.xml'):
        self.model_path = model_path
        self.ie = Core() if Core else None
        self.compiled_model = None
        self.input_layer = None
        self.output_layer = None
        self.ocr = None
        
        self._load_detector()
        self._load_ocr()

    def _load_detector(self):
        if not self.ie:
            print("OpenVINO Core not available")
            return
        
        try:
            if not os.path.exists(self.model_path):
                 print(f"Model dosyası bulunamadı: {self.model_path}")
                 return
            
            model = self.ie.read_model(model=self.model_path)
            # INTEL GPU (620) DESTEĞİ BURADA
            self.compiled_model = self.ie.compile_model(model=model, device_name="GPU")
            self.input_layer = self.compiled_model.input(0)
            self.output_layer = self.compiled_model.output(0)
            print(">>> EvoSmart: OpenVINO GPU Modunda Başlatıldı")
        except Exception as e:
            print(f"GPU yükleme hatası (CPU'ya dönülüyor): {e}")
            # GPU hata verirse güvenli liman olan CPU'ya döner
            self.compiled_model = self.ie.compile_model(model=model, device_name="CPU")

    def _load_ocr(self):
        if PaddleOCR:
            try:
                # GPU desteği aktif, hız için limit_side_len eklendi
                self.ocr = PaddleOCR(use_angle_cls=True, lang='en', show_log=False, use_gpu=True, det_limit_side_len=480)
                print(">>> EvoSmart: PaddleOCR GPU Modunda Hazır")
            except Exception as e:
                print(f"OCR yükleme hatası: {e}")

    def detect_and_recognize(self, frame):
        results = []
        annotated_frame = frame.copy() # Arayüz için çizim yapılacak kopya
        
        if self.compiled_model is None:
            return results, annotated_frame

        h, w = frame.shape[:2]
        input_size = (640, 640)
        resized_frame = cv2.resize(frame, input_size)
        input_data = np.expand_dims(resized_frame.transpose(2, 0, 1), 0).astype(np.float32) / 255.0

        outputs = self.compiled_model([input_data])[self.output_layer]
        outputs = np.squeeze(outputs).T
        
        boxes, scores = [], []
        for i in range(len(outputs)):
            classes_scores = outputs[i][4:]
            max_score = np.amax(classes_scores)
            
            if max_score >= 0.25:
                x, y, w_det, h_det = outputs[i][:4]
                x1 = int((x - w_det / 2) * w / 640)
                y1 = int((y - h_det / 2) * h / 640)
                boxes.append([x1, y1, int(w_det * w / 640), int(h_det * h / 640)])
                scores.append(max_score)
        
        indices = cv2.dnn.NMSBoxes(boxes, scores, 0.25, 0.45)
        
        for i in indices:
            # OpenCV sürümüne göre i bazen liste bazen integer döner
            idx = i[0] if isinstance(i, (list, np.ndarray)) else i
            x1, y1, w_box, h_box = boxes[idx]
            x2, y2 = x1 + w_box, y1 + h_box
            
            x1, y1 = max(0, x1), max(0, y1)
            x2, y2 = min(w, x2), min(h, y2)
            
            crop = frame[y1:y2, x1:x2]
            if crop.size == 0: continue
            
            # EKRANA YEŞİL ÇERÇEVE ÇİZ
            cv2.rectangle(annotated_frame, (x1, y1), (x2, y2), (0, 255, 0), 2)
            
            plate_text = ""
            if self.ocr:
                ocr_res = self.ocr.ocr(crop, cls=True)
                if ocr_res and ocr_res[0]:
                    plate_text = ocr_res[0][0][1][0].upper().replace(" ", "")
            
            if plate_text:
                cv2.putText(annotated_frame, plate_text, (x1, y1-10), 
                            cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 0), 2)
                
                results.append({
                    'plate': plate_text,
                    'box': [x1, y1, x2, y2],
                    'crop': crop
                })
        
        return results, annotated_frame