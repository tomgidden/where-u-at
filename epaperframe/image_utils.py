#!/usr/bin/env python
# coding: utf-8

# Copyright 2011 Álvaro Justen [alvarojusten at gmail dot com]
# License: GPL <http://www.gnu.org/copyleft/gpl.html>

from PIL import Image, ImageDraw, ImageFont


class ImageText(object):
    def __init__(self, draw, encoding='utf8'):
        self.draw = draw
        self.encoding = encoding

    def save(self, filename=None):
        self.image.save(filename or self.filename)

    def get_font_size(self, text, font, max_width=None, max_height=None):
        if max_width is None and max_height is None:
            raise ValueError('You need to pass max_width or max_height')
        font_size = 1
        text_size = self.get_text_size(font, font_size, text)
        if (max_width is not None and text_size[0] > max_width) or \
           (max_height is not None and text_size[1] > max_height):
            raise ValueError("Text can't be filled in only (%dpx, %dpx)" % \
                    text_size)
        while True:
            if (max_width is not None and text_size[0] >= max_width) or \
               (max_height is not None and text_size[1] >= max_height):
                return font_size - 1
            font_size += 1
            text_size = self.get_text_size(font, font_size, text)

    def text(self, xy, text, font_filename, font_size=11,
                   color=(0, 0, 0), max_width=None, max_height=None):
        x, y = xy
        #if isinstance(text, str):
        #    text = text.decode(self.encoding)
        if font_size == 'fill' and \
           (max_width is not None or max_height is not None):
            font_size = self.get_font_size(text, font_filename, max_width,
                                           max_height)
        text_size = self.get_text_size(font_filename, font_size, text)
        font_obj = ImageFont.truetype(font_filename, font_size)
        if x == 'center':
            x = (self.size[0] - text_size[0]) / 2
        if y == 'center':
            y = (self.size[1] - text_size[1]) / 2
        self.draw.text((x, y), text, font=font_obj, fill=color)
        return text_size

    def get_text_size(self, font_filename, font_size, text):
        font = ImageFont.truetype(font_filename, font_size)
        return font.getsize(text)

    def text_box(self, xy, text, box_width, font_filename,
                 font_size=11, color=(0, 0, 0), place='left',
                 box_height=None,
                 background=None,
                 line_spacing=1.1,
                 margin=2,
                 lines_limit=None,
                 justify_last_line=False,
                 debug=False):
        x0, y0 = xy
        lines = []
        line = []
        words = text.split(' ')
        for word in words:
            new_line = ' '.join(line + [word])
            size = self.get_text_size(font_filename, font_size, new_line)
            if size[0] <= box_width:
                line.append(word)
            else:
                lines.append(line)
                line = [word]
        if line:
            lines.append(line)
        lines = [' '.join(line) for line in lines if line]

        line_height = font_size * line_spacing
        y = y0

        if lines_limit:
            if len(lines) > lines_limit:
                lines = lines[0:lines_limit]

        if background is not None:
            for index, line in enumerate(lines):
                if place == 'left':
                    total_size = self.get_text_size(font_filename, font_size, line)
                    rect = (x0-margin, y-margin, total_size[0]+x0+margin, total_size[1]+y+margin)
                    if debug:
                        self.draw.rectangle(rect, outline=color)
                    else:
                        self.draw.rectangle(rect, fill=background)

                elif place == 'right':
                    total_size = self.get_text_size(font_filename, font_size, line)
                    x_left = x0 + box_width - total_size[0]
                    rect = (x_left-margin, y-margin, total_size[0]+x_left+margin, total_size[1]+y+margin)
                    if debug:
                        self.draw.rectangle(rect, outline=color)
                    else:
                        self.draw.rectangle(rect, fill=background)


                elif place == 'center':
                    total_size = self.get_text_size(font_filename, font_size, line)
                    x_left = int(x0 + ((box_width - total_size[0]) / 2))
                    rect = (x_left-margin, y-margin, total_size[0]+x_left+margin, total_size[1]+y+margin)
                    if debug:
                        self.draw.rectangle(rect, outline=color)
                    else:
                        self.draw.rectangle(rect, fill=background)


                elif place == 'justify':
                    words = line.split()
                    if (index == len(lines) - 1 and not justify_last_line) or len(words) == 1:
                        total_size = self.get_text_size(font_filename, font_size, line)
                        rect = (x0-margin, y-margin, total_size[0]+x0+margin, total_size[1]+y+margin)
                        if debug:
                            self.draw.rectangle(rect, outline=color)
                        else:
                            self.draw.rectangle(rect, fill=background)
                    else:
                        total_size = self.get_text_size(font_filename, font_size, line)
                        rect = (x0-margin, y-margin, box_width+x0+margin, total_size[1]+y+margin)
                        if debug:
                            self.draw.rectangle(rect, outline=color)
                        else:
                            self.draw.rectangle(rect, fill=background)
                y += line_height
                if box_height and y > box_height:
                    break

        y = y0
        for index, line in enumerate(lines):
            if place == 'left':
                self.text((x0, y), line, font_filename, font_size,
                          color)
            elif place == 'right':
                total_size = self.get_text_size(font_filename, font_size, line)
                x_left = x0 + box_width - total_size[0]
                self.text((x_left, y), line, font_filename, font_size, color)
            elif place == 'center':
                total_size = self.get_text_size(font_filename, font_size, line)
                x_left = int(x0 + ((box_width - total_size[0]) / 2))
                self.text((x_left, y), line, font_filename, font_size, color)
            elif place == 'justify':
                words = line.split()
                if (index == len(lines) - 1 and not justify_last_line) or len(words) == 1:
                    self.text((x0, y), line, font_filename, font_size, color)
                    continue
                line_without_spaces = ''.join(words)
                total_size = self.get_text_size(font_filename, font_size,
                                                line_without_spaces)
                space_width = (box_width - total_size[0]) / (len(words) - 1.0)
                start_x = x0
                for word in words[:-1]:
                    self.text((start_x, y), word, font_filename,
                              font_size, color)
                    word_size = self.get_text_size(font_filename, font_size,
                                                    word)
                    start_x += word_size[0] + space_width
                last_word_size = self.get_text_size(font_filename, font_size,
                                                    words[-1])
                last_word_x = x0 + box_width - last_word_size[0]
                self.text((last_word_x, y), words[-1], font_filename,
                          font_size, color)
            y += line_height
            if box_height and y > box_height:
                break

        return (box_width, y - y0 - line_height)
