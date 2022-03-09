"""
Run the following in the notebook prior to using objects in this module:

    !pip install -q ipycanvas
    from google.colab import output
    output.enable_custom_widget_manager()
"""

#https://github.com/martinRenou/ipycanvas/issues/170#issuecomment-1062071346
#https://github.com/martinRenou/ipycanvas/blob/master/examples/hand_drawing.ipynb

from IPython.display import display
from ipywidgets import Image
from ipywidgets import ColorPicker, IntSlider, link, AppLayout, HBox

from ipycanvas import (
  Canvas,
  RoughCanvas, 
  MultiRoughCanvas,
  MultiCanvas,
  hold_canvas,
)

from functools import partial

class Sketcher:
    def __init__(
        self,
        starting_color="#749cb8",
        factory=partial(MultiRoughCanvas, 2)
    ):
        self.factory=factory
        self.starting_color=starting_color
        self.init_canvas()
        self.init_picker()
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
    @property
    def mask_canvas(self):
        #if not hasattr(self, 'canvas'):
        #    self.init_canvas()
        canvas = self.canvas
        if isinstance(self.canvas, MultiCanvas):
            canvas = self.canvas[-1]
        return canvas
    
    def init_canvas(
        self,
        width = 400,
        height = 400,
    ):
        self.width = width
        self.height = height 

        factory = self.factory       
        self.canvas = factory(width=width, height=height, sync_image_data=True)
        #canvas = self.canvas
        #if isinstance(self.canvas, MultiCanvas):
        #    canvas = self.canvas[-1]
        canvas = self.mask_canvas
        canvas.on_mouse_down(self.on_mouse_down)
        canvas.on_mouse_move(self.on_mouse_move)
        canvas.on_mouse_up(self.on_mouse_up)
        canvas.stroke_style = self.starting_color # can I just link the picker here?

        self.drawing = False
        self.position = None
        self.shape = []
        return canvas

    def set_background(self, im):
        self.canvas[0] = im
        return self.canvas

    def on_mouse_down(self, x, y):
        self.drawing = True
        self.position = (x, y)
        self.shape = [self.position]

    def on_mouse_move(self, x1, y1):
        if not self.drawing:
            return
        with hold_canvas(self.mask_canvas):
            x0, y0 = self.position
            self.mask_canvas.stroke_line(x0, y0, x1, y1)
            self.position = (x1, y1)
        self.shape.append(self.position)

    def on_mouse_up(self, x1, y1):
        self.drawing = False
        with hold_canvas(self.mask_canvas):
            x0, y0 = self.position
            self.mask_canvas.stroke_line(x0, y0, x1, y1)
            self.mask_canvas.fill_polygon(self.shape)
        self.shape = []

    def show(self):
        display(HBox((self.canvas, self.picker)))