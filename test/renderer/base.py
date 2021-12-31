# -*- coding: utf-8 -*-

import gc
import abc
from typing import List
import base64
from io import BytesIO
from PIL import Image, ImageDraw, ImageFont


class RenderBase(metaclass=abc.ABCMeta):
    '''
    @abstractmethod for self.__generate_image
    '''

    def __init__(self, fontsize: int = 32) -> None:
        self._fonttype = self.__get_fonttype(fontsize)
        self._image: Image = None
        self._drawtable: ImageDraw = None
        self._w, self._h = 0, 0
        self._fontsize = fontsize

    def __get_fonttype(self, fontsize) -> ImageFont.FreeTypeFont:
        return ImageFont.truetype('../static/font/YaHeiConsolas.ttf', fontsize)

    async def __image2base64(self) -> bytes:
        _buffer = BytesIO()
        self._image.save(_buffer, format='PNG')
        return base64.b64encode(_buffer.getvalue())

    async def __allocate(self, width: int, height: int):
        self._w, self._h = width, height
        self._image = Image.new('RGB', (width, height), 'white')
        self._drawtable = ImageDraw.Draw(im=self._image)

    async def __free(self):
        del self._image, self._drawtable
        gc.collect()

    def draw_text(self, xy: tuple, text: str, fontsize: int = 0, fill: str = '#000000'):
        if not self._drawtable:
            return
        _font = self.__get_fonttype(
            fontsize) if fontsize and fontsize != self._fontsize else self._fonttype
        self._drawtable.text(
            xy=xy, text=text, fill=fill, font=_font)

    def __calc_texts_center_index(self, texts: List[str], fontsizes: List[int], pivot: int) -> List[int]:
        def _(c: str) -> float:
            return 1 if '\u4e00' <= c and c <= '\u9fa5' else 0.5
        real_sizes = []
        for idx, text in enumerate(texts):
            real_sizes.append(sum(list(map(lambda x: _(x) * fontsizes[idx], text))))
        totalsize = sum(real_sizes)
        heads = [0] * len(texts)
        if pivot == -1:
            heads = [(self._w - totalsize) / 2]
            for rsize in real_sizes[:-1]:
                heads.append(heads[-1] + rsize)
        else: # valid pivot
            heads[pivot] = (self._w - real_sizes[pivot]) / 2
            for front_idx in range(1, pivot + 1):
                heads[pivot - front_idx] = heads[pivot - front_idx + 1] - real_sizes[pivot - front_idx]
            for back_idx in range(pivot + 1, len(texts)):
                heads[back_idx] = heads[back_idx - 1] + real_sizes[back_idx - 1]
        return heads

    def draw_text_center(self, y: int, texts: List[str], fontsizes: List[int] = [], fills: List[str] = [], pivot: int = -1):
        texts = list(map(str, texts))
        if len(fontsizes) == 0:
            fontsizes = [self._fontsize] * len(texts)
        if len(fills) == 0:
            fills = ['#000000'] * len(texts)
        maxsize = max(fontsizes)
        ydiffs = list(map(lambda x: maxsize - x, fontsizes))
        heads = self.__calc_texts_center_index(texts, fontsizes, pivot)
        for idx, text in enumerate(texts):
            self.draw_text((heads[idx], y + ydiffs[idx]), text, fontsizes[idx], fills[idx])

    @abc.abstractmethod
    async def generate_image(self, content: dict):
        '''
        different methods in different scenario
        use self.draw_text to draw text on image
        '''

    async def draw(self, width: int, height: int, content: dict) -> bytes:
        await self.__allocate(width, height)
        await self.generate_image(content)

        _b64bytes = await self.__image2base64()
        await self.__free()
        return _b64bytes