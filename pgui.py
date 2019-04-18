from helpers.gui_helper import GUIHelper
from helpers.global_access import debug_print, reg_print
from helpers.global_access import GlobalMods as GM
import utils

from urllib.parse import quote
from PIL import Image
from binascii import b2a_base64
from bs4 import BeautifulSoup


class PseudoGUI:

    mumble = None
    content = None
    box_open = False

    def __init__(self, mumble):
        self.mumble = mumble
        debug_print("Pseudo-GUI initialized.")

    def quick_gui(self, content, text_type="data", text_color=None, text_font='Calibri', text_align="center", bgcolor=None, border=None, box_align=None, row_align="center", cellpadding="5", cellspacing="5", channel=None, user=None):
        if self.box_open:
            return False
        if channel is None:
            channel = utils.get_my_channel(self.mumble)
        if bgcolor is None:
            bgcolor = GM.cfg['PGUI_Settings']['CanvasBGColor']
        if box_align is None:
            box_align = GM.cfg['PGUI_Settings']['CanvasAlignment']
        if border is None:
            border = GM.cfg['PGUI_Settings']['CanvasBorder']
        if text_color is None:
            text_color = GM.cfg['PGUI_Settings']['CanvasTextColor']

        self.open_box(bgcolor=bgcolor, border=border, align=box_align, cellspacing=cellspacing, cellpadding=cellpadding)
        content = self.make_content(content, text_type=text_type, text_color=text_color, text_font=text_font, text_align=text_align)
        self.append_row(content, align=row_align)
        self.close_box()
        self.display_box(channel=channel, user=user)
        self.clear_display()

    def quick_gui_img(self, caption, dir, img_name, channel=None, user=None):
        if self.box_open:
            return False
        if channel is None:
            channel = utils.get_my_channel(self.mumble)

        self.open_box(align='left')

        formatted_string = self.format_image(f"{img_name}", "jpg", dir)
        content = self.make_content(formatted_string, image=True, text_align='center')
        self.append_row(content)

        caption = self.make_content(caption, text_type="header", text_font='Calibri', image=False)
        self.append_row(caption)

        self.close_box()

        self.display_box(channel=channel, user=user)
        self.clear_display()

    def open_box(self, bgcolor=None, border=None, align=None, cellspacing="5", cellpadding="5"):
        if self.box_open:
            return False
        if bgcolor is None:
            bgcolor = GM.cfg['PGUI_Settings']['CanvasBGColor']
        if align is None:
            align = GM.cfg['PGUI_Settings']['CanvasAlignment']
        if border is None:
            border = GM.cfg['PGUI_Settings']['CanvasBorder']

        self.content = f'<table bgcolor="{bgcolor}" border="{border}" align="{align}" cellspacing="{cellspacing}" cellpadding="{cellpadding}">'
        self.box_open = True
        return True

    def close_box(self):
        if not self.box_open:
            return False
        self.content += '</table>'
        self.box_open = False
        return True

    def append_row(self, content, align="center"):
        if not self.box_open:
            return False
        self.content += f'<tr align="{align}">' + content + '</tr>'
        return True

    def append_content(self, content):
        if not self.box_open:
            return False
        self.content += content
        return True

    def make_content(self, text, text_type="data", text_color=None, text_font='Calibri', text_align="center", image=False):
        if not self.box_open:
            return None
        if image:
            return GUIHelper.img_content(text)
        if text_color is None:
            text_color = GM.cfg['PGUI_Settings']['CanvasTextColor']
        new_content = GUIHelper.content(text, tt=text_type, tc=text_color, tf=text_font, ta=text_align)
        return new_content

    def display_box(self, channel, user=None):
        if self.content is None or self.box_open:
            return
        if user is not None:
            utils.msg(self.mumble, user, self.content)
            self.clear_display()
            return
        utils.echo(channel, self.content)
        self.clear_display()

    def clear_display(self):
        self.content = None

    def mid(self, text, begin, length):
        return text[begin:begin+length]

    def format_image_html(self, img_ext, byte_arr):
        if img_ext == "jpg":
            img_ext = "JPEG"
        elif img_ext == "jpeg":
            img_ext = "JPEG"
        elif img_ext == "png":
            img_ext = "PNG"

        raw_base = self.encode_b64(byte_arr)
        encoded = []
        i = 0
        begin = 0
        end = 0

        begin = i * 72
        end = i * 72
        mid_raw_base = self.mid(raw_base, begin, 72)
        encoded.append(quote(mid_raw_base, safe=''))
        i += 1
        while end < len(raw_base):
            begin = i * 72
            end = i * 72
            mid_raw_base = self.mid(raw_base, begin, 72)
            encoded.append(quote(mid_raw_base, safe=''))
            i += 1

        return f"<img src='data:image/{img_ext};base64,{''.join(encoded)}' />"

    def format_image(self, img_name, img_ext, img_dir):
        # Open image
        img = Image.open(f"{img_dir}{img_name}.{img_ext}")
        img.load()
        img_width = img.size[0]
        img_height = img.size[1]
        # Scale image down with aspect ratio
        if img_width > 272 or img_height > 163:
            img.thumbnail((272, 163), Image.ANTIALIAS)
        # Save and close image
        img.save(f"{img_dir}{img_name}.{img_ext}")
        img.close()
        # Convert image to byte array
        with open(f"{img_dir}{img_name}.{img_ext}", "rb") as img_read:
            img_data = img_read.read()
            img_byte_arr = bytearray(img_data)
        # Keep lowering quality until it fits within the size restrictions.
        img_quality = 100
        while len(img_byte_arr) >= 32768 and img_quality > 0:
            img_byte_arr.clear()
            with open(f"{img_dir}{img_name}.{img_ext}", "rb") as img_file:
                img_data = img_file.read()
                img_byte_arr = bytearray(img_data)
            img = Image.open(f"{img_dir}{img_name}.{img_ext}")
            img.save(f"{img_dir}{img_name}.{img_ext}", quality=img_quality)
            img.close()
            img_quality -= 10
        if len(img_byte_arr) < 32768:
            # return formatted html img string
            return self.format_image_html(img_ext=img_ext, byte_arr=img_byte_arr)
        return ""

    def encode_b64(self, byte_arr):
        encvec = []
        eol = '\n'
        max_unencoded = 76 * 3 // 4
        s = byte_arr
        for i in range(0, len(s), max_unencoded):
            # BAW: should encode() inherit b2a_base64()'s dubious behavior in
            # adding a newline to the encoded string?
            enc = b2a_base64(s[i:i + max_unencoded]).decode("ascii")
            if enc.endswith('\n') and eol != '\n':
                enc = enc[:-1] + eol
            encvec.append(enc)

        b64_img = ''.join(encvec)
        return b64_img

