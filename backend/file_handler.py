import os
from werkzeug.utils import secure_filename
import uuid

# Конфигурация
UPLOAD_FOLDER = 'uploads'  # Папка для сохранения файлов
ALLOWED_IMAGE_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif'}
ALLOWED_VIDEO_EXTENSIONS = {'mp4', 'avi', 'mov'}
MAX_IMAGE_SIZE = 2 * 1024 * 1024  # 2MB
MAX_VIDEO_SIZE = 50 * 1024 * 1024  # 50MB

os.makedirs(UPLOAD_FOLDER, exist_ok=True)

def allowed_file(filename, allowed_extensions):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in allowed_extensions

def save_file(file, upload_folder=UPLOAD_FOLDER):
    unique_filename = str(uuid.uuid4())
    original_extension = os.path.splitext(secure_filename(file.filename))[1]  # Получаем расширение файла
    new_filename = f"{unique_filename}{original_extension}"
    file_path = os.path.join(upload_folder, new_filename)
    file.save(file_path)
    return file_path

def validate_and_save_file(file, content_type):
    if content_type.startswith('image/'):
        allowed_extensions = ALLOWED_IMAGE_EXTENSIONS
        max_size = MAX_IMAGE_SIZE
    elif content_type.startswith('video/'):
        allowed_extensions = ALLOWED_VIDEO_EXTENSIONS
        max_size = MAX_VIDEO_SIZE
    else:
        raise ValueError("Неподдерживаемый тип файла")

    if not allowed_file(file.filename, allowed_extensions):
        raise ValueError("Неподдерживаемое расширение файла")

    if len(file.read()) > max_size:
        raise ValueError("Файл слишком большой")
    file.seek(0)

    file_path = save_file(file)
    return file_path