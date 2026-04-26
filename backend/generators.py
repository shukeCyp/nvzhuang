from abc import ABC, abstractmethod


class BaseImageGenerator(ABC):
    """图片生成器父类。"""

    @abstractmethod
    def generate(self, *args, **kwargs) -> str:
        """执行图片生成，并返回生成文件的路径。"""
        raise NotImplementedError


class BaseVideoGenerator(ABC):
    """视频生成器父类。"""

    @abstractmethod
    def generate(
        self,
        image_b64: str,
        prompt: str,
        model: str,
        duration: int,
        quality: str,
        ratio: str,
        **kwargs,
    ) -> str:
        """执行视频生成，返回生成文件的路径。"""
        raise NotImplementedError
