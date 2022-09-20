from typing import Union
import tkinter as tk
from PIL import Image, ImageTk

UI_HIDE_DELAY = 3000  # milliseconds


class ResizingImageCanvas(tk.Canvas):
    """
    This class inherits from tkinter.Canvas and provides some additional
    functionality so that the canvas will resize the image it contains in
    response to a change in size of the canvas.
    """

    def __init__(self, parent, image_filename: str):
        """
        For the constructor for this class, in addition to sending the parent
        widget, you also send the name of the file containing the image to
        display in the canvas.

        Args:
            parent:  the widget in which the canvas will be contained
            image_filename: the path and filename of the image to be displayed
        """

        # Open the image to be used and determine its default size
        self.image = Image.open(image_filename)
        self.original_image_width = self.image.size[0]
        self.original_image_height = self.image.size[1]
        self.tk_image = ImageTk.PhotoImage(self.image)

        # Call the constructor for tkinter.Canvas and set the initial size
        #   of the canvas to be the default image size
        tk.Canvas.__init__(self, parent,
                           width=self.original_image_width,
                           height=self.original_image_height)

        # Create an image object on the canvas
        self.image_id = self.create_image(0, 0, image=self.tk_image,
                                          anchor=tk.NW)

        # Bind the "Configure" event to a method so that when the canvas size
        #  changes, the image size can be changed.
        self.bind("<Configure>", self.on_resize)

        # Create UI Objects on top of image
        # The "ui_objects" list will contain the following:
        #   0 - Upper left rectangle
        #   1 - Upper right rectangle
        self.RECTANGLE_SIZE = 40
        self.ui_objects = []
        rectangle_id = self.create_rectangle(10, 10,
                                             10+self.RECTANGLE_SIZE,
                                             10+self.RECTANGLE_SIZE)
        self.ui_objects.append(rectangle_id)
        rectangle_id = self.create_rectangle(self.original_image_width - 10
                                             - self.RECTANGLE_SIZE,
                                             10,
                                             self.original_image_width - 10,
                                             10+self.RECTANGLE_SIZE)
        self.ui_objects.append(rectangle_id)

        # Remove UI elements after 3 seconds
        self.hide_function_id = self.after(UI_HIDE_DELAY, self.hide_ui_objects)

        # Bind mouse motion to showing UI
        self.bind("<Motion>", self.mouse_motion)

        # Bind mouse click
        self.bind("<Button-1>", self.on_click)

    def on_resize(self, event):
        """
        This method will is bound to the "Configure" event and thus will be
        called when the size of the canvas is changed.  The original image
        will be resized to the new canvas size.

        Args:
            event: generated by the <Configure> event, it contains information
            about the new size of the canvas

        """

        # In this prototype, I'm only resizing for the height, or y, direction.
        #   But, could also check for width/x size and scale to whichever
        #   ratio is smaller.
        alpha_x = event.width / self.original_image_width
        alpha_y = event.height / self.original_image_height
        alpha = min(alpha_x, alpha_y)
        new_width = round(self.image.size[0] * alpha)
        new_height = round(self.image.size[1] * alpha)
        self.tk_image = ImageTk.PhotoImage(self.image.resize(
            (new_width, new_height)
        ))
        self.itemconfigure(self.image_id, image=self.tk_image)
        # Resize UI elements
        self.coords(self.ui_objects[1],
                    new_width - 10 - self.RECTANGLE_SIZE,
                    10,
                    new_width - 10,
                    10+self.RECTANGLE_SIZE)

    def hide_ui_objects(self):
        """
        Sets all UI objects to the "hidden" state
        """
        for object_id in self.ui_objects:
            self.itemconfigure(object_id, state="hidden")

    def show_ui_objects(self):
        """
        Sets all UI objects to the "normal" state so they are shown
        """
        for object_id in self.ui_objects:
            self.itemconfigure(object_id, state="normal")

    def mouse_motion(self, event):
        """
        When mouse movement is detected within the canvas, this function is
        called.  It first cancels the running timer to hide the UI elements
        after a certain period of time.  Then, it calls the method to set the
        UI elements to the "normal" or shown state.  Then, it restarts the
        3-second timer to hide the UI elements.

        Args:
            event: generated by the "<Motion>" event and contains information
            about the mouse position.  Not currently used.
        """
        self.after_cancel(self.hide_function_id)
        self.show_ui_objects()
        self.hide_function_id = self.after(UI_HIDE_DELAY, self.hide_ui_objects)

    def on_click(self, event):
        """
        Event handler called when <Button-1> mouse click is detected.  This
        function searches through the UI elements and determines if the mouse
        is currently located inside any of the ui elements.

        Args:
            event: Generated by the "<Button-1>" event, it contains information
            about the mouse click.  Specficially, .x and .y are the coordinates
            in the canvas.
        """
        for object_id in self.ui_objects:
            x1, y1, x2, y2 = self.bbox(object_id)
            if (x1 <= event.x < x2) and (y1 <= event.y <= y2):
                print("Clicked in UI object {}".format(object_id))


class MainWindow(tk.Tk):
    """
    The MainWindow class inherits from tkinter.Tk and so is essentially the
    root window for Tk with some additional functionality.

    """
    def __init__(self):
        super(MainWindow, self).__init__()

        self.canvas = ResizingImageCanvas(self, "download.png")
        self.canvas.grid(column=0, row=0, sticky="news")
        # When using the .grid() method, by default tkinter will put the widget
        #   (the canvas in this case) in the center of the cell defined by
        #   the column and row.  The `sticky` property can be used to change
        #   its placement.  For example, if you wanted the canvas to be aligned
        #   with the left-side of the cell, you would say `sticky="w"` where
        #   "w"est means the left side.  If you wanted it to line up on the
        #   right side and the bottom of the cell, you would use `sticky="se"`
        #   where e=east and s=south.  In this case, we want the canvas to
        #   take up the entire cell.  So, we use `sticky="news"` so it lines
        #   up with all four directions.  This will cause the canvas size to
        #   change when the grid size changes.

        # This button is simply a place holder for other grid content.
        self.button = tk.Button(self, text="Here")
        self.button.grid(column=0, row=1)

        # By default, each grid column and row will be sized to fit its
        #   contents.  But, in the lines below, we are telling column 0 and
        #   row 0 to use 100% of the window size remaining after other rows
        #   and columns take up how much space they need.
        self.columnconfigure(0, weight=1)
        self.rowconfigure(0, weight=1)

        # This line binds the hitting the space bar to a function that prints
        #   out some data on the size of things.  This is just for diagnostics.
        #   It is not required for the resizing to work.
        self.bind("<space>", self.print_stats)

        self.mainloop()

    def print_stats(self, event):
        print("***************** Stats ****************")
        self.print_widget_stats(self)
        self.print_widget_stats(self.canvas)
        self.print_widget_stats(self.button)

    @staticmethod
    def print_widget_stats(widget: Union[tk.Widget, tk.Tk]):
        print("Widget Stats for {}".format(type(widget)))
        print("  Size: {}x{}".format(widget.winfo_width(),
                                     widget.winfo_height()))
        print("  Req Size: {}x{}".format(widget.winfo_reqwidth(),
                                         widget.winfo_reqheight()))


if __name__ == '__main__':
    MainWindow()
