from __future__ import annotations

import math
from enum import Enum

from PIL import Image

from dymoprint.lib.render_engines.render_context import RenderContext
from dymoprint.lib.render_engines.render_engine import RenderEngine


class BitmapTooBigError(ValueError):
    def __init__(self, width_px, max_width_px):
        msg = f"width_px: {width_px}, max_width_px: {max_width_px}"
        super().__init__(msg)


class MarginsMode(Enum):
    PRINT = 1
    PREVIEW = 2


class MarginsRenderEngine(RenderEngine):
    def __init__(
        self,
        render_engine: RenderEngine,
        mode: MarginsMode,
        justify: str = "center",
        visible_horizontal_margin_px: float = 0,
        labeler_margin_px: tuple[float, float] = (0, 0),
        max_width_px: float | None = None,
        min_width_px: float = 0,
    ):
        super().__init__()
        labeler_horizontal_margin_px, labeler_vertical_margin_px = labeler_margin_px
        assert visible_horizontal_margin_px >= 0
        assert labeler_horizontal_margin_px >= 0
        assert labeler_vertical_margin_px >= 0
        assert not max_width_px or max_width_px >= 0
        assert min_width_px >= 0
        self.mode = mode
        self.justify = justify
        self.visible_horizontal_margin_px = visible_horizontal_margin_px
        self.labeler_horizontal_margin_px = labeler_horizontal_margin_px
        self.labeler_vertical_margin_px = labeler_vertical_margin_px
        self.max_width_px = max_width_px
        self.min_width_px = min_width_px
        self.render_engine = render_engine

    def calculate_visible_width(self, payload_width_px: int) -> float:
        minimal_label_width_px = (
            payload_width_px + self.visible_horizontal_margin_px * 2
        )
        if self.max_width_px is not None and minimal_label_width_px > self.max_width_px:
            raise BitmapTooBigError(minimal_label_width_px, self.max_width_px)

        if self.min_width_px > minimal_label_width_px:
            label_width_px = self.min_width_px
        else:
            label_width_px = minimal_label_width_px
        return label_width_px

    def render(self, context: RenderContext) -> Image.Image:
        payload_bitmap = self.render_engine.render(context)
        payload_width_px = payload_bitmap.width
        label_width_px = self.calculate_visible_width(payload_width_px)
        padding_px = label_width_px - payload_width_px  # sum of margins from both sides

        if self.justify == "left":
            horizontal_offset_px = self.visible_horizontal_margin_px
        elif self.justify == "center":
            horizontal_offset_px = padding_px / 2
        elif self.justify == "right":
            horizontal_offset_px = padding_px - self.visible_horizontal_margin_px
        assert horizontal_offset_px >= self.visible_horizontal_margin_px

        # In print mode:
        # ==============
        # There is a gap between the printer head and the cutter (for the sake of this
        # example, let us say it is DX pixels wide).
        # We assume the printing starts when the print head is in offset DX from the
        # label's edge (just under the cutter).
        # After we print the payload, we need to offset the label DX pixels, in order
        # to move the edge of the printed payload past the cutter, othewise the cutter
        # will cut inside the printed payload.
        # Afterwards, we need to offset another DX pixels, so that the cut will have
        # some margin from the payload edge. The reason we move DX pixels this time, is
        # in order to have simmetry with the initial margin between label edge and start
        # of printed payload.
        #
        # There's also some vertical margin between printed area and the label edge

        vertical_offset_px: float = 0
        if self.mode == MarginsMode.PRINT:
            # print head is already in offset from label's edge under the cutter
            horizontal_offset_px -= self.labeler_horizontal_margin_px
            # no need to add vertical margins to bitmap
            bitmap_height = payload_bitmap.height
        elif self.mode == MarginsMode.PREVIEW:
            # add vertical margins to bitmap
            bitmap_height = payload_bitmap.height + self.labeler_vertical_margin_px * 2
            vertical_offset_px = self.labeler_vertical_margin_px

        bitmap = Image.new("1", (math.ceil(label_width_px), math.ceil(bitmap_height)))
        bitmap.paste(
            payload_bitmap, box=(round(horizontal_offset_px), round(vertical_offset_px))
        )
        meta = {
            "horizontal_offset_px": horizontal_offset_px,
            "vertical_offset_px": vertical_offset_px,
        }
        return bitmap, meta
