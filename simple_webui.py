import streamlit as st
from IT8951 import constants
from IT8951.display import AutoEPDDisplay
from PIL import Image

VCOM = -1.45


class IT8951Display:
    def __init__(self, vcom: float):
        self._epd = AutoEPDDisplay(vcom=vcom)
        self._width = self._epd.width
        self._height = self._epd.height

    def width(self) -> int:
        return self._width

    def height(self) -> int:
        return self._height

    def clear(self):
        self._epd.clear()

    def update(self, file):
        self._epd.frame_buf.paste(0xFF, box=(0, 0, self.width(), self.height()))
        img = Image.open(file)
        dims = (self.width(), self.height())
        if img.size[0] / img.size[1] < dims[0] / dims[1]:
            target_height = dims[1]
            target_width = int(target_height / img.size[1] * img.size[0])
        else:
            target_width = dims[0]
            target_height = int(target_width / img.size[0] * img.size[1])
        img = img.resize((target_width, target_height))
        x = int((dims[0] - target_width) / 2)
        y = int((dims[1] - target_height) / 2)
        self._epd.frame_buf.paste(img, (x, y))
        self._epd.draw_full(constants.DisplayModes.GC16)


if __name__ == '__main__':
    if "display" not in st.session_state:
        st.session_state.display = IT8951Display(VCOM)

    st.title("墨水屏控制")
    st.file_uploader("上传一张图片", key="img")
    c1, c2 = st.columns(2)
    with c1:
        if st.button("清屏", use_container_width=True):
            st.session_state.display.clear()
    with c2:
        if st.button("更新", use_container_width=True):
            if st.session_state.img is not None:
                st.session_state.display.clear()
                st.session_state.display.update(st.session_state.img)
