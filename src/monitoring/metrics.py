import csv
import time
from datetime import datetime
from pathlib import Path
from functools import wraps
import sys
import hashlib
from src.utils.image import analyze_image_content
from src.utils.task_id import generate_task_id
from src.database.db import insert_image_metadata, insert_prediction, insert_feedback

# Ajouter le répertoire racine au path
ROOT_DIR = Path(__file__).parent.parent.parent
sys.path.insert(0, str(ROOT_DIR))

from config.settings import ROOT_DIR, PROCESSED_DATA_DIR

# Fichier CSV pour stocker les métriques
MONITORING_FILE = PROCESSED_DATA_DIR / "monitoring_inference.csv"

def log_metrics(func):
    @wraps(func)
    async def wrapper(*args, **kwargs):
        start_time = time.perf_counter()
        success = False
        result = None
        image_info = {}
        uuid = generate_task_id()
        
        try:
            file = kwargs.get('file')
            if file and hasattr(file, 'filename'):
                # Read file content ONCE
                file_content = await file.read()
                
                # Fast MD5 hash instead of SHA256
                image_hash = hashlib.md5(file_content).hexdigest()
                
                # Analyze everything from content
                image_info = {
                    'hash': image_hash,
                    'filename': file.filename,
                    **analyze_image_content(file_content, file.filename)
                }
                
                # Pass content to function
                kwargs['image_data'] = file_content
            
            result = await func(*args, **kwargs)
            result['task_id'] = uuid
            prediction = {
                'p_cat': result["probabilities"]["cat"],
                'p_dog': result["probabilities"]["dog"]
            }
            success = True
            return result
            
        except Exception as e:
            success = False
            prediction = {'p_cat': None, 'p_dog': None}
            raise
            
        finally:
            end_time = time.perf_counter()
            inference_time_ms = (end_time - start_time) * 1000
            
            insert_image_metadata(
                hash=image_info.get('hash', None),
                filename=image_info.get('filename', 'unknown'),
                ext_type=image_info.get('extension', 'unknown'),
                size_w=image_info.get('width', 0),
                size_h=image_info.get('height', 0),
                color_mode=image_info.get('color_mode', 0)
            )
            insert_prediction(
                uuid=uuid,
                image_id=image_info.get('hash', 'unknown'),  # MD5 hash
                inference_time_ms=inference_time_ms,
                success=success,
                prediction= prediction
            )
            insert_feedback(uuid=uuid, grade=0)
            
    return wrapper