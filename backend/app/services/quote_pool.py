from __future__ import annotations

from itertools import cycle

from app.models.script_models import TransitionalQuote


class QuotePool:
    def __init__(self) -> None:
        self._quotes = [
            TransitionalQuote(text="疑则勿用，用则勿疑；然疑案之中，先问证据。", author="司马光", source="仿史论语气"),
            TransitionalQuote(text="天下之事，虑之贵详，行之贵力。", author="朱熹", source="宋人语境"),
            TransitionalQuote(text="纸上得来终觉浅，绝知此事要躬行。", author="陆游", source="《冬夜读书示子聿》"),
            TransitionalQuote(text="试玉要烧三日满，辨材须待七年期。", author="白居易", source="《放言五首》"),
        ]
        self._iterator = cycle(self._quotes)

    def next_quote(self) -> TransitionalQuote:
        return next(self._iterator)


quote_pool = QuotePool()
