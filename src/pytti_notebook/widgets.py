"""
Run the following in the notebook prior to using objects in this module:

    !pip install -q ipycanvas
    from google.colab import output
    output.enable_custom_widget_manager()
"""

#https://github.com/martinRenou/ipycanvas/issues/170#issuecomment-1062071346
#https://github.com/martinRenou/ipycanvas/blob/master/examples/hand_drawing.ipynb

from copy import deepcopy
from functools import partial

from IPython.display import display
from ipycanvas import (
  Canvas,
  RoughCanvas, 
  MultiRoughCanvas,
  MultiCanvas,
  hold_canvas,
)
from ipywidgets import Image as ImageIpyw
from ipywidgets import (
    ColorPicker, 
    link, 
    HBox, 
    VBox,
    Button,
)


import numpy as np
from PIL import Image as ImagePil


def fix_transparency(
    mask,
    bgnd=(255, 255, 255, 1), # white
):
    img = ImagePil.new("RGBA", mask.size, bgnd)
    img.alpha_composite(mask)
    return img

class Sketcher:
    """
    Run the following in the notebook prior to using this widget in colab:

        !pip install -q ipycanvas
        from google.colab import output
        output.enable_custom_widget_manager()
    """
    def __init__(
        self,
        background_image=None,
        starting_color="#000000",
        # defaults to be overriden after/if background image provided
        width = 400,
        height = 400,
    ):
        self.width = width
        self.height = height
        self.starting_color=starting_color
        if background_image:
            self.load_background(background_image)
        self.reset()
        if background_image:
            self._set_background()


    def reset(self):
        self.init_canvas()
        self.init_picker()
        self.init_reset_button()
        self.init_save_button()
        self.link()

    def link(self):
        picker, canvas = self.picker, self.mask_canvas
        link((picker, "value"), (canvas, "stroke_style"))
        link((picker, "value"), (canvas, "fill_style"))
        return picker, canvas 

    def init_picker(self):
        self.picker = ColorPicker(
            description="Color:", 
            value=self.starting_color,
        )

    def init_reset_button(self):
        self.reset_button = Button(
            description="Reset"
        )
        def _on_clicked(b):
            self.container.clear()
        self.reset_button.on_click(
            _on_clicked
            )
    
    def init_save_button(self):
        self.save_button = Button(
            description="Save"
        )
        def _on_clicked(b):
            self.container.to_file("_mask_with_image.png")
            #self.mask_canvas.to_file("_mask.png")
            mask_np = self.mask_canvas.get_image_data()
            mask_pil = ImagePil.fromarray(mask_np)
            mask_pil = fix_transparency(mask_pil)

            with open("mask_data.npy", 'wb') as f:
                #np.save(f, self.mask_canvas.get_image_data())
                mask_pil.save(f)
        self.save_button.on_click(
            _on_clicked
            )

    @property
    def mask_canvas(self): 
        return self.container[1]

    @property
    def bgnd_canvas(self): 
        return self.container[0]

    def init_canvas(
        self,
    ):
        width = self.width
        height = self.height 
        self.container = MultiCanvas(2, width=width, height=height, sync_image_data=True)

        self.mask_canvas.sync_image_data=True
        self.mask_canvas.on_mouse_down(self.on_mouse_down)
        self.mask_canvas.on_mouse_move(self.on_mouse_move)
        self.mask_canvas.on_mouse_up(self.on_mouse_up)
        self.mask_canvas.stroke_style = self.starting_color # can I just link the picker here?
        self.mask_canvas.fill_style = self.starting_color # can I just link the picker here?

        self.drawing = False
        self.position = None
        self.shape = []
        self.poly = []
        return self.container

    def load_background(self, im):
        if isinstance(im, str):
            try:
                self._load_background_from_fpath(fpath=im)
            except FileNotFoundError:
                self._load_background_from_url(url=im)
        else:
            raise NotImplementedError
        #img = self._bgnd_im 
        #self.height, self.width = img.height, img.width

    def set_background(self, im):
        self.load_background(im)
        self._set_background()

    def _set_background(self, im=None):
        #if not im:
        #    #im = self._bgnd_im
        #self.bgnd_canvas.draw_image(im, 0,0)
        #self._bgnd_im = im
        self.bgnd_canvas.put_image_data(self._bgnd_im_np, 0,0)

    def _load_background_from_fpath(self, fpath):
        """sets background image given path to image file"""
        #im = ImageIpyw.from_file(fpath)
        #im_pil = Image
        with ImagePil.open(fpath) as im:
            self._bgnd_im_pil = im
            self.width, self.height = self._bgnd_im_pil.size
            self._bgnd_im_np = np.asarray(im)
            

    def _load_background_from_url(self, url):
        """sets background image given path to image file"""
        raise NotImplementedError
        #im = ImageIpyw.from_url(url)
        #self._bgnd_im = im


    def on_mouse_down(self, x, y):
        self.drawing = True
        self.position = (x, y)
        self.shape = [self.position]

        #self.mask_canvas.begin_path()
        #self.mask_canvas.move_to(x ,y)

    def on_mouse_move(self, x1, y1):
        if not self.drawing:
            return
        with hold_canvas(self.container):
            x0, y0 = self.position
            self.mask_canvas.stroke_line(x0, y0, x1, y1)

        self.position = (x1, y1)
        self.shape.append(self.position)

    def on_mouse_up(self, x1, y1):
        self.drawing = False
        with hold_canvas(self.container):
            x_previous, y_previous = self.position
            x0, y0 = self.shape[0]
            self.mask_canvas.stroke_line(x_previous, y_previous, x1, y1)
            self.mask_canvas.stroke_line(x1, y1, x0, y0)
            self.shape.append((x0, y0))             
            self.mask_canvas.fill_polygon(self.shape)
        self.poly.append(deepcopy(self.shape))
        self.shape = []
        self.mask_canvas.save()

    def undo(self):
        # yeah.... this doesn't work.
        self.mask_canvas.restore()

    def show(self):
        layout = HBox(
            (self.container, 
             VBox((
                self.picker,
                self.reset_button,
                self.save_button,
                ))
            )
        )
        display(layout)
