"""
Run the following in the notebook prior to using objects in this module:

    !pip install -q ipycanvas
    from google.colab import output
    output.enable_custom_widget_manager()
"""

#https://github.com/martinRenou/ipycanvas/issues/170#issuecomment-1062071346
#https://github.com/martinRenou/ipycanvas/blob/master/examples/hand_drawing.ipynb

from copy import deepcopy

from IPython.display import display
from ipywidgets import Image
from ipywidgets import (
    ColorPicker, 
    link, 
    HBox, 
    VBox,
    Button,
)

from ipywidgets import Image as ImageIpyw

from ipycanvas import (
  Canvas,
  RoughCanvas, 
  MultiRoughCanvas,
  MultiCanvas,
  hold_canvas,
)

from functools import partial

class Sketcher:
    """
    Run the following in the notebook prior to using this widget in colab:

        !pip install -q ipycanvas
        from google.colab import output
        output.enable_custom_widget_manager()
    """
    def __init__(
        self,
        starting_color="#749cb8",
    ):
        self.starting_color=starting_color
        self.reset()

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
            self.mask_canvas.to_file("_mask.png")
            with open("mask_data.npy") as f:
                self.mask_canvas.get_image_data().save(f)
        self.reset_button.on_click(
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
        width = 400,
        height = 400,
    ):
        self.width = width
        self.height = height 
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

    def set_background(self, im):
        if isinstance(im, str):
            try:
                self._set_background_from_fpath(fpath=im)
            except FileNotFoundError:
                self._set_background_from_url(url=im)
        else:
            raise NotImplementedError

    def _set_background(self, im):
        self.bgnd_canvas.draw_image(im, 0,0)

    def _set_background_from_fpath(self, fpath):
        """sets background image given path to image file"""
        im = ImageIpyw.from_file(fpath)
        self._set_background(im)

    def _set_background_from_url(self, url):
        """sets background image given path to image file"""
        im = ImageIpyw.from_url(url)
        self._set_background(im)


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
