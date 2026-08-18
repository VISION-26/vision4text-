import os
from typing import Tuple
import cv2
import numpy as np
from PIL import Image

from app.utils.logger import logger


def load_image_cv2(image_path: str) -> np.ndarray:
    """
    Load image using OpenCV (BGR format).
    """
    if not os.path.exists(image_path):
        raise FileNotFoundError(f"Image not found at path: {image_path}")
        
    img = cv2.imread(image_path)
    if img is None:
        raise ValueError(f"Could not decode image at path: {image_path}")
    return img


def save_image_cv2(image_path: str, image: np.ndarray) -> str:
    """
    Save OpenCV image array to file path.
    """
    os.makedirs(os.path.dirname(image_path), exist_ok=True)
    success = cv2.imwrite(image_path, image)
    if not success:
        raise IOError(f"Failed to write image to {image_path}")
    return image_path


def load_image_pil(image_path: str) -> Image.Image:
    """
    Load image using Pillow.
    """
    if not os.path.exists(image_path):
        raise FileNotFoundError(f"Image file does not exist: {image_path}")
    return Image.open(image_path).convert("RGB")


def resize_image_if_needed(image: np.ndarray, max_dim: int = 1024) -> np.ndarray:
    """
    Resize image proportionally if dimensions exceed max_dim.
    """
    h, w = image.shape[:2]
    if max(h, w) > max_dim:
        scale = max_dim / float(max(h, w))
        new_w, new_h = int(w * scale), int(h * scale)
        return cv2.resize(image, (new_w, new_h), interpolation=cv2.INTER_AREA)
    return image
