from tkinter import *
from PIL import Image, ImageTk
def gui(path):
    window = Frame()
    window.pack(expand=YES,fill=BOTH)
    #window.title("Join")
    #window.geometry("300x300")
    #window.configure(background = 'grey')
    img = ImageTk.PhotoImage(Image.open(path))
    panel = Label(window, image=img)
    panel.pack(fill="both",expand="yes")

    text = StringVar()
    text.set('Choose upper bound')
    label = Label(window, textvariable = text)
    label.pack(side = "bottom")
    upper = None
    lower = None
    count = 2
    def onRelease(event):
        nonlocal count, upper, lower
        if count == 2:
            text.set('Choose lower bound')
            upper = (event.x, event.y)
            count -= 1
        elif count == 1:
            text.set('Close window')
            lower = (event.x, event.y)
    panel.bind("<ButtonRelease-1>", onRelease )
    window.mainloop()
    return upper, lower
class ReceiptScanner( Frame ):
    def __init__( self , path):
      Frame.__init__( self )
      self.pack( expand = YES, fill = BOTH )
      #self.master.title( path )
      #self.master.geometry(  "275x275" )
      img = ImageTk.PhotoImage(Image.open(path))
      self.pic = Label(self, image = img)
      self.pic.pack()
      #self.bottomtext = StringVar() # displays mouse position
      #self.bottomtext.set( "Choose upper bound for receipt crop" )
      #self.positionLabel = Label( self,textvariable = self.bottomtext )
      #self.positionLabel.pack( side = BOTTOM )
      #self.count = 2
      #self.bind( "<ButtonRelease-1>", self.buttonReleased )
      #self.bind( "<Enter>", self.enteredWindow )
      #self.upper = None
      #self.lower = None

    def enteredWindow(self,event):
        self.bottomtext.set("entered window")
    def buttonReleased( self, event ):
       if self.count == 2:
           self.upper = (event.x, event.y)
           self.bottomtext.set( "Choose lower bound for receipt crop" )
           self.count -= 1
       elif self.count == 1:
           self.lower = (event.x, event.y)
           self.bottomtext.set("Close the window to continue")

    def mainloop(self):
       Frame.mainloop(self)
       if self.upper is None or self.lower is None:
           raise Exception('bounds not found')
       return self.upper, self.lower
