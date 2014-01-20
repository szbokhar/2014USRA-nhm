from processImage import *
import cv2
import sys
from PIL import Image, ImageTk
from Tkinter import Tk, Label, BOTH, Canvas, NW
from ttk import Frame, Style

class Example(Frame):

    def __init__(self, parent, fname):
        Frame.__init__(self, parent)

        self.parent = parent
        self.image_filename = fname
        self.imgtk = None
        self.cv1 = None
        self.hover = None
        self.imgid = None
        self.data = None
        self.phase = 0

        self.initUI()

    def initUI(self):
        self.parent.title("Simple")
        self.pack(fill=BOTH, expand=1)

        # Setup window
        self.parent.title("Absolute positioning")
        self.pack(fill=BOTH, expand=1)
        style = Style()
        style.configure("TFrame", background="#FFF")

        # Load image with opencv
        img = cv2.imread(self.image_filename)
        (display_image, ratio) = get_display_image(img)
        display_image = cv2.cvtColor(display_image, cv2.COLOR_RGB2BGR)
        pilimg = Image.fromarray(display_image)
        self.imgtk = ImageTk.PhotoImage(pilimg)
        self.data = (img, ratio)

        # Make canvas
        self.cv1 = Canvas(self, width=640, height=480)
        self.imgid = self.cv1.create_image(0,0,image=self.imgtk, anchor=NW)
        self.cv1.place(x=20, y=20)
        self.cv1.bind('<Motion>', self.__handle_move)
        self.cv1.bind('<Button-1>', self.__handle_click)

        # Make labels
        self.lbl1 = Label(self, text='Background point:')
        self.lbl1.place(x=20, y=520)
        self.lbl2 = Label(self, text='Foreground point:')
        self.lbl2.place(x=20, y=550)

    def __handle_move(self,event):
        if self.phase < 2:
            (x,y) = (event.x, event.y)
            (_, ratio) = self.data
            sz = int(30*ratio)
            hid = self.cv1.create_rectangle(x-sz, y-sz, x+sz, y+sz)
            if self.hover != None:
                self.cv1.delete(self.hover)
            self.hover = hid

    def __handle_click(self,event):
        if self.phase <= 2:
            (x,y) = (event.x, event.y)
            (_, ratio) = self.data
            sz = int(30*ratio)
            self.cv1.create_rectangle(x-sz, y-sz, x+sz, y+sz)
            img = click(event.x, event.y, self.data, self.phase)

            if self.phase == 0:
                self.lbl1.config(text='Background point: (%d,%d)'%(x/ratio,y/ratio))
            if self.phase == 1:
                self.lbl2.config(text='Foreground point: (%d,%d)'%(x/ratio,y/ratio))

            if img != None:
                (display_image, ratio) = get_display_image_2D(img)
                pilimg = Image.fromarray(display_image)
                self.imgtk = ImageTk.PhotoImage(pilimg)
                self.cv1.delete(self.imgid)
                self.imgid = self.cv1.create_image(0,0,image=self.imgtk, anchor=NW)

        self.phase += 1



# Main function
def main():
    fname = sys.argv[1]     # Get filename

    # Make gui
    root = Tk()
    root.geometry("680x600+100+100")
    root.configure(bg="#FFFFFF")
    app = Example(root, fname)
    root.mainloop()


if __name__ == "__main__":
    main()
