import tkinter as tk
from PIL import Image, ImageTk

DUKEBLUE = "#012169"


class SplashLabel(tk.Label):

    def __init__(self, parent, **kwargs):
        super(SplashLabel, self).__init__(parent, **kwargs)
        self.configure(bg=DUKEBLUE, fg="white")


class Splash(tk.Toplevel):

    def __init__(self, parent: tk.Tk):
        super(Splash, self).__init__(parent)
        self.title("Splash")

        # Get Logo Image so its width can be used to set splash screen width
        image = Image.open("resources/duke_bass_connections_logos.JPG")

        screen_width = parent.winfo_screenwidth()
        screen_height = parent.winfo_screenheight()

        splash_width = image.size[0]
        splash_height = 150

        splash_x = round((screen_width - splash_width) / 2)
        splash_y = round((screen_height - splash_height) / 2)

        self.geometry("{}x{}+{}+{}".format(splash_width, splash_height,
                                           splash_x, splash_y))
        self.config(bg=DUKEBLUE)

        SplashLabel(self, text="KeyScope Viewer",
                    font=('Arial', '24', 'bold')).pack()

        self.tk_image = ImageTk.PhotoImage(image)
        tk.Label(self, image=self.tk_image, bd=0).pack()

        SplashLabel(self, text="Loading...").pack()

        self.overrideredirect(True)
        self.update()
