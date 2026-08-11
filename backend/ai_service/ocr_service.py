import io
from loguru import logger
import numpy as np
from PIL import Image


class OCRService:
    _instance: "OCRService | None" = None
    _ocr = None

    def __new__(cls) -> "OCRService":
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    def __init__(self):
        if self._ocr is not None:
            return
        # paddleocr 为可选依赖（OCR 默认禁用），仅在实际使用时按需导入
        try:
            from paddleocr import PaddleOCR
        except ImportError as e:
            raise RuntimeError(
                "PaddleOCR 未安装，OCR 功能不可用（OCR_ENABLED=false 时属正常情况）"
            ) from e
        logger.info("初始化 PaddleOCR 引擎")
        self._ocr = PaddleOCR(use_angle_cls=True, lang="ch", show_log=False)
        logger.info("PaddleOCR 引擎初始化完成")

    def recognize_image(self, image_bytes: bytes) -> str:
        if not image_bytes:
            return ""

        try:
            image = Image.open(io.BytesIO(image_bytes)).convert("RGB")
            image_array = np.array(image)

            result = self._ocr.ocr(image_array, cls=True)

            if not result or not result[0]:
                logger.warning("OCR 未识别到任何文本")
                return ""

            lines = []
            for line in result[0]:
                text = line[1][0]
                confidence = line[1][1]
                if confidence >= 0.5:
                    lines.append(text)

            full_text = "\n".join(lines)
            logger.debug(f"OCR 识别完成: {len(lines)} 行文本, 置信度阈值 0.5")
            return full_text

        except Exception as e:
            logger.error(f"OCR 识别失败: {e}")
            raise