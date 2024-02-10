from __future__ import annotations

from PIL import Image, ImageColor, ImageDraw, ImageOps

from dymoprint.lib.render_engines.margins import MarginsMode, MarginsRenderEngine
from dymoprint.lib.render_engines.render_context import RenderContext
from dymoprint.lib.render_engines.render_engine import RenderEngine


class PrintPreviewRenderEngine(RenderEngine):
    MARGIN_PX = 20
    DX = MARGIN_PX * 0.2

    def __init__(
        self,
        render_engine: RenderEngine,
        justify: str = "center",
        visible_horizontal_margin_px: float = 0,
        labeler_margin_px: tuple[float, float] = (0, 0),
        max_width_px: float | None = None,
        min_width_px: float = 0,
    ):
        super().__init__()
        self.render_engine = MarginsRenderEngine(
            render_engine=render_engine,
            mode=MarginsMode.PREVIEW,
            justify=justify,
            visible_horizontal_margin_px=visible_horizontal_margin_px,
            labeler_margin_px=labeler_margin_px,
            max_width_px=max_width_px,
            min_width_px=min_width_px,
        )

    def _get_preview_bitmap(self, context: RenderContext):
        label_bitmap, meta = self.render_engine.render(context)
        bitmap = ImageOps.invert(label_bitmap.convert("L")).convert("RGBA")
        pixel_map = {
            "black": context.foreground_color,
            "white": context.background_color,
        }
        pixel_map = {
            ImageColor.getcolor(k, "RGBA"): ImageColor.getcolor(v, "RGBA")
            for k, v in pixel_map.items()
        }
        pixdata = bitmap.load()
        width, height = bitmap.size
        for x in range(0, width):
            for y in range(0, height):
                pixdata[x, y] = pixel_map[pixdata[x, y]]
        return bitmap, meta

    def _show_margins(self, preview_bitmap, bitmap, meta, context):
        draw = ImageDraw.Draw(bitmap)
        x = meta["horizontal_offset_px"]
        y = meta["vertical_offset_px"]
        width, height = bitmap.size
        preview_width, preview_height = preview_bitmap.size
        lines = [
            (self.MARGIN_PX + x, 0, self.MARGIN_PX + x, height),
            (
                self.MARGIN_PX + preview_width - x,
                0,
                self.MARGIN_PX + preview_width - x,
                height,
            ),
            (0, self.MARGIN_PX + y, width, self.MARGIN_PX + y),
            (
                0,
                self.MARGIN_PX + preview_height - y,
                width,
                self.MARGIN_PX + preview_height - y,
            ),
        ]
        for line in lines:
            draw.line(line, fill=context.foreground_color)

    def render(self, context: RenderContext) -> Image.Image:
        preview_bitmap, meta = self._get_preview_bitmap(context)
        preview_width, preview_height = preview_bitmap.size
        width = preview_width + self.MARGIN_PX * 2
        height = preview_height + self.MARGIN_PX * 2
        bitmap = Image.new("RGBA", (width, height), color=(255, 0, 0, 0))
        bitmap.paste(preview_bitmap, box=(self.MARGIN_PX, self.MARGIN_PX))
        if context.preview_show_margins:
            self._show_margins(preview_bitmap, bitmap, meta, context)

        return bitmap
