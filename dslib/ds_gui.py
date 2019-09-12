from dslib.ds_process import DSProcess
from tkinter import Tk, Label, StringVar, BooleanVar, Spinbox, Button, Entry, Checkbutton

class PositionGUI(Tk):

    def __init__(self, process: DSProcess):

        super(PositionGUI, self).__init__()

        self.process = process
        self.exit_flag = False

        self.title("PosGUI")
        self.protocol("WM_DELETE_WINDOW", self.on_quit)
        self.resizable(False, False)

        Label(self, text="current").grid(column=2, row=2)
        Label(self, text="stable").grid(column=3, row=2)
        Label(self, text="stored").grid(column=4, row=2)
        Label(self, text="X").grid(column=1, row=3)
        Label(self, text="Y").grid(column=1, row=4)
        Label(self, text="Z").grid(column=1, row=5)
        Label(self, text="α").grid(column=1, row=6)

        self.x_current = StringVar()
        Entry(self, width=10, state="readonly", textvariable=self.x_current).grid(column=2, row=3)
        self.x_stable = StringVar()
        Entry(self, width=10, state="readonly", textvariable=self.x_stable).grid(column=3, row=3)
        self.x_stored = StringVar()
        self.x_stored.set(process.get_pos_stable()[0])
        Spinbox(self, from_=-1000, to=1000, format="%.3f", width=10, textvariable=self.x_stored).grid(column=4, row=3)

        self.y_current = StringVar()
        Entry(self, width=10, state="readonly", textvariable=self.y_current).grid(column=2, row=4)
        self.y_stable = StringVar()
        Entry(self, width=10, state="readonly", textvariable=self.y_stable).grid(column=3, row=4)
        self.y_stored = StringVar()
        self.y_stored.set(process.get_pos_stable()[1])
        Spinbox(self, from_=-1000, to=1000, format="%.3f", width=10, textvariable=self.y_stored).grid(column=4, row=4)

        self.z_current = StringVar()
        Entry(self, width=10, state="readonly", textvariable=self.z_current).grid(column=2, row=5)
        self.z_stable = StringVar()
        Entry(self, width=10, state="readonly", textvariable=self.z_stable).grid(column=3, row=5)
        self.z_stored = StringVar()
        self.z_stored.set(process.get_pos_stable()[2])
        Spinbox(self, from_=-1000, to=1000, format="%.3f", width=10, textvariable=self.z_stored).grid(column=4, row=5)

        self.a_current = StringVar()
        Entry(self, width=10, state="readonly", textvariable=self.a_current).grid(column=2, row=6)
        self.a_stable = StringVar()
        Entry(self, width=10, state="readonly", textvariable=self.a_stable).grid(column=3, row=6)
        self.a_stored = StringVar()
        self.a_stored.set(process.get_pos_stable()[3])
        Spinbox(self, from_=-360, to=360, format="%.3f", width=10, textvariable=self.a_stored).grid(column=4, row=6)

        Button(self, width=7, text="store", command=self.store).grid(column=2, row=7)
        Button(self, width=7, text="restore", command=self.restore).grid(column=4, row=7)

        Label(self, text="world:").grid(column=1, row=8)
        self.world = StringVar()
        self.world.set(process.get_world())
        Entry(self, width=10, state="readonly", textvariable=self.world).grid(column=2, row=8)
        Label(self, text="area:").grid(column=1, row=9)
        self.area = StringVar()
        self.area.set(process.get_area())
        Entry(self, width=10, state="readonly", textvariable=self.area).grid(column=2, row=9)

        self.lock_pos = BooleanVar()
        self.lock_pos.set(False)
        Checkbutton(self, text="freeze", var=self.lock_pos, command=self.freeze).grid(column=4, row=9)

        Thread(target=self.update).start()

    def update(self):
        while not self.exit_flag:
            self.x_current.set("%.3f" % self.process.get_pos()[0])
            self.x_stable.set("%.3f" % self.process.get_pos_stable()[0])
            self.y_current.set("%.3f" % self.process.get_pos()[1])
            self.y_stable.set("%.3f" % self.process.get_pos_stable()[1])
            self.z_current.set("%.3f" % self.process.get_pos()[2])
            self.z_stable.set("%.3f" % self.process.get_pos_stable()[2])
            self.a_current.set("%.3f" % self.process.get_pos()[3])
            self.a_stable.set("%.3f" % self.process.get_pos_stable()[3])
            self.world.set(self.process.get_world())
            self.area.set(self.process.get_area())
            sleep(0.2)

    def freeze(self):
        self.process.lock_pos(self.lock_pos.get())

    def store(self):
        self.x_stored.set(self.x_current.get())
        self.y_stored.set(self.y_current.get())
        self.z_stored.set(self.z_current.get())
        self.a_stored.set(self.a_current.get())

    def restore(self):
        try:
            self.process.jump_pos(
                float(self.x_stored.get()),
                float(self.y_stored.get()),
                float(self.z_stored.get()),
                float(self.a_stored.get())
            )
        except ValueError as e:
            print(e)

    def on_quit(self):
        self.exit_flag = True
        self.destroy()

