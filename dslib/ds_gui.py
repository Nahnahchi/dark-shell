from dslib.ds_process import DSProcess
from tkinter import Tk, Label, StringVar, BooleanVar, Spinbox, Button, Entry, Checkbutton, LabelFrame
from threading import Thread
from time import sleep


class DSGraphicsGUI(Tk):

    def __init__(self, process: DSProcess):

        super(DSGraphicsGUI, self).__init__()

        self.process = process

        self.title("GraphicsGUI")
        self.resizable(False, False)

        render = LabelFrame(self, text="Render")
        render.pack(fill="both")

        self.draw_map = BooleanVar()
        self.draw_map.set(True)
        Checkbutton(render, text="Map", var=self.draw_map,
                    command=self.set_draw_map).grid(row=0, column=0, sticky="W")

        self.draw_creatures = BooleanVar()
        self.draw_creatures.set(True)
        Checkbutton(render, text="Creatures", var=self.draw_creatures,
                    command=self.set_draw_creatures).grid(row=1, column=0, sticky="W")

        self.draw_objects = BooleanVar()
        self.draw_objects.set(True)
        Checkbutton(render, text="Objects", var=self.draw_objects,
                    command=self.set_draw_objects).grid(row=2, column=0, sticky="W")

        self.draw_sfx = BooleanVar()
        self.draw_sfx.set(True)
        Checkbutton(render, text="SFX", var=self.draw_sfx,
                    command=self.set_draw_sfx).grid(row=3, column=0, sticky="W")

        self.draw_shadows = BooleanVar()
        self.draw_shadows.set(True)
        Checkbutton(render, text="Shadows", var=self.draw_shadows,
                    command=self.set_draw_shadows).grid(row=0, column=1, sticky="W")

        self.draw_sprite_shadows = BooleanVar()
        self.draw_sprite_shadows.set(True)
        Checkbutton(render, text="Sprite Shadows", var=self.draw_sprite_shadows,
                    command=self.set_draw_sprite_shadows).grid(row=1, column=1, sticky="W")

        self.draw_textures = BooleanVar()
        self.draw_textures.set(True)
        Checkbutton(render, text="Textures", var=self.draw_textures,
                    command=self.set_draw_textures).grid(row=2, column=1, sticky="W")

        self.normal_draw_tex_edge = BooleanVar()
        self.normal_draw_tex_edge.set(True)
        Checkbutton(render, text="NormalDraw_TexEdge", var=self.normal_draw_tex_edge,
                    command=self.set_draw_sprites).grid(row=3, column=1, sticky="W")

        self.depth_draw_depth_tex_edge = BooleanVar()
        self.depth_draw_depth_tex_edge.set(True)
        Checkbutton(render, text="DepthDraw_DepthTexEdge", var=self.depth_draw_depth_tex_edge,
                    command=self.set_draw_sprite_masks).grid(row=4, column=1, sticky="W")

        self.normal_draw_trans = BooleanVar()
        self.normal_draw_trans.set(True)
        Checkbutton(render, text="NormalDraw_Trans", var=self.normal_draw_trans,
                    command=self.set_draw_trans).grid(row=5, column=1, sticky="W")

        debug = LabelFrame(self, text="Debug")
        debug.pack(fill="both")

        self.large_compass = BooleanVar()
        self.large_compass.set(False)
        Checkbutton(debug, text="Large Compass", var=self.large_compass,
                    command=self.set_draw_compass_large).grid(row=0, column=0, sticky="W")

        self.small_compass = BooleanVar()
        self.small_compass.set(False)
        Checkbutton(debug, text="Small Compass", var=self.small_compass,
                    command=self.set_draw_compass_small).grid(row=1, column=0, sticky="W")

        self.altimeter = BooleanVar()
        self.altimeter.set(False)
        Checkbutton(debug, text="Altimeter", var=self.altimeter,
                    command=self.set_draw_altimeter).grid(row=2, column=0, sticky="W")

        self.node_graph = BooleanVar()
        self.node_graph.set(False)
        Checkbutton(debug, text="Node Graph", var=self.node_graph,
                    command=self.set_draw_node_graph).grid(row=0, column=1, sticky="W")

        self.bounding_boxes = BooleanVar()
        self.bounding_boxes.set(False)
        Checkbutton(debug, text="Bounding Boxes", var=self.bounding_boxes,
                    command=self.set_draw_bounding_boxes).grid(row=1, column=1, sticky="W")

    def set_draw_map(self):
        self.process.draw_map(self.draw_map.get())

    def set_draw_creatures(self):
        self.process.draw_creatures(self.draw_creatures.get())

    def set_draw_objects(self):
        self.process.draw_objects(self.draw_objects.get())

    def set_draw_sfx(self):
        self.process.draw_sfx(self.draw_sfx.get())

    def set_draw_shadows(self):
        self.process.draw_shadows(self.draw_shadows.get())

    def set_draw_sprite_shadows(self):
        self.process.draw_sprite_shadows(self.draw_sprite_shadows.get())

    def set_draw_textures(self):
        self.process.draw_textures(self.draw_textures.get())

    def set_draw_trans(self):
        self.process.draw_trans(self.normal_draw_trans.get())

    def set_draw_sprites(self):
        self.process.draw_sprites(self.normal_draw_tex_edge.get())

    def set_draw_sprite_masks(self):
        self.process.draw_sprite_masks(self.depth_draw_depth_tex_edge.get())

    def set_draw_compass_large(self):
        self.process.draw_compass_large(self.large_compass.get())

    def set_draw_compass_small(self):
        self.process.draw_compass_small(self.small_compass.get())

    def set_draw_altimeter(self):
        self.process.draw_altimeter(self.altimeter.get())

    def set_draw_node_graph(self):
        self.process.draw_nodes(self.node_graph.get())

    def set_draw_bounding_boxes(self):
        self.process.draw_bounding(self.bounding_boxes.get())


class DSPositionGUI(Tk):

    def __init__(self, process: DSProcess):

        super(DSPositionGUI, self).__init__()

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

