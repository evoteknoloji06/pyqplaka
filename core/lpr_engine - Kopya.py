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
                 print(f"Model file {self.model_path} not found. Detector will not work.")
                 return
            
            model = self.ie.read_model(model=self.model_path)
            self.compiled_model = self.ie.compile_model(model=model, device_name="GPU")
            self.input_layer = self.compiled_model.input(0)
            self.output_layer = self.compiled_model.output(0)
            print("OpenVINO detector loaded successfully")
        except Exception as e:
            print(f"Error loading OpenVINO detector: {e}")

    def _load_ocr(self):
        if PaddleOCR:
            try:
                self.ocr = PaddleOCR(use_angle_cls=True, lang='en', show_log=False, use_gpu=True)
                print("PaddleOCR loaded successfully")
            except Exception as e:
                print(f"Error loading PaddleOCR: {e}")
        else:
            print("PaddleOCR not available")

    def detect_and_recognize(self, frame):
        """
        Detects license plates and recognizes text.
        Returns a list of dictionaries: [{'plate': 'ABC1234', 'box': [x1, y1, x2, y2], 'crop': image_np}]
        """
        results = []
        
        if self.compiled_model is None:
            return results

        # Preprocessing for YOLOv8 (640x640)
        h, w = frame.shape[:2]
        input_size = (640, 640)
        resized_frame = cv2.resize(frame, input_size)
        input_data = np.expand_dims(resized_frame.transpose(2, 0, 1), 0).astype(np.float32) / 255.0

        # Inference
        outputs = self.compiled_model([input_data])[self.output_layer]
        
        # Post-processing YOLOv8 (Output shape is usually [1, 84, 8400] for v8)
        # 84 = 4 (box) + 80 (classes). If only 1 class (license plate), 84 -> 5
        outputs = np.squeeze(outputs).T
        
        boxes = []
        scores = []
        class_ids = []
        
        for i in range(len(outputs)):
            classes_scores = outputs[i][4:]
            max_score = np.amax(classes_scores)
            
            if max_score >= 0.25:
                class_id = np.argmax(classes_scores)
                x, y, w_det, h_det = outputs[i][:4]
                
                # Scale boxes back to original image size
                x1 = int((x - w_det / 2) * w / 640)
                y1 = int((y - h_det / 2) * h / 640)
                x2 = int((x + w_det / 2) * w / 640)
                y2 = int((y + h_det / 2) * h / 640)
                
                boxes.append([x1, y1, x2 - x1, y2 - y1])
                scores.append(max_score)
                class_ids.append(class_id)
        
        indices = cv2.dnn.NMSBoxes(boxes, scores, 0.25, 0.45)
        
        if len(indices) > 0:
            for i in indices.flatten():
                x1, y1, w_box, h_box = boxes[i]
                x2, y2 = x1 + w_box, y1 + h_box
                
                # Ensure box is within frame
                x1, y1 = max(0, x1), max(0, y1)
                x2, y2 = min(w, x2), min(h, y2)
                
                crop = frame[y1:y2, x1:x2]
                
                if crop.size == 0:
                    continue
                
                plate_text = "UNKNOWN"
                if self.ocr:
                    ocr_res = self.ocr.ocr(crop, cls=True)
                    if ocr_res and ocr_res[0]:
                        # PaddleOCR returns [[[box], (text, score)], ...]
                        plate_text = ocr_res[0][0][1][0]
                
                results.append({
                    'plate': plate_text.upper(),
                    'box': [x1, y1, x2, y2],
                    'crop': crop
                })
        
        return results
