"""
ALI X STAR RACING 3D - MOBILE EDITION
Panda3D arcade racing prototype with on-screen touch controls.

Controls:
  Hold LEFT / RIGHT to steer
  Hold GAS to accelerate
  Hold BRAKE to slow down / reverse
  Hold NITRO for a boost
  Tap RESTART to restart

Note:
  This is the mobile-ready game source. Building an Android APK still
  requires Panda3D's Android packaging/build setup.
"""

import math
import random

from direct.showbase.ShowBase import ShowBase
from direct.gui.OnscreenText import OnscreenText
from direct.gui.DirectGui import DirectFrame, DirectButton, DirectGuiGlobals as DGG
from panda3d.core import (
    AmbientLight,
    DirectionalLight,
    Fog,
    Vec4,
    TextNode,
    WindowProperties,
)


class RacingGame(ShowBase):
    def __init__(self):
        super().__init__()

        self.disableMouse()
        self.setBackgroundColor(0.42, 0.68, 0.88, 1)

        # On Android, the app's manifest/build settings determine orientation.
        # This window setup is useful when testing on desktop.
        props = WindowProperties()
        props.setTitle("ALI X STAR RACING 3D")
        props.setSize(1280, 720)
        self.win.requestProperties(props)

        self.player_x = 0.0
        self.player_y = 0.0
        self.speed = 0.0
        self.steer = 0.0
        self.nitro = 100.0
        self.distance = 0.0
        self.finished = False
        self.message_timer = 0.0

        self.keys = {
            "forward": False,
            "back": False,
            "left": False,
            "right": False,
            "nitro": False,
        }

        self.setup_lighting()
        self.build_world()

        self.player = self.make_car((0.05, 0.35, 0.95, 1), "PLAYER")
        self.player.setPos(0, 0, 0.12)

        self.opponents = []
        self.make_opponents()

        self.setup_hud()
        self.setup_mobile_controls()
        self.accept_keyboard_for_testing()

        self.camera.setPos(0, -17, 7.2)
        self.camera.lookAt(0, 12, 0.7)
        self.camLens.setFov(78)

        self.taskMgr.add(self.update, "update")
        self.show_message("3... 2... 1... GO!", 2.0)

    def setup_lighting(self):
        ambient = AmbientLight("ambient")
        ambient.setColor(Vec4(0.58, 0.60, 0.66, 1))
        self.render.setLight(self.render.attachNewNode(ambient))

        sun = DirectionalLight("sun")
        sun.setColor(Vec4(1.0, 0.94, 0.82, 1))
        sun_node = self.render.attachNewNode(sun)
        sun_node.setHpr(-35, -55, 0)
        self.render.setLight(sun_node)

        fog = Fog("distance-fog")
        fog.setColor(0.55, 0.72, 0.82)
        fog.setExpDensity(0.0025)
        self.render.setFog(fog)

    def make_box(self, name, scale, position, color, parent=None):
        node = self.loader.loadModel("models/box")
        node.setName(name)
        node.reparentTo(parent if parent is not None else self.render)
        node.setScale(*scale)
        node.setPos(*position)
        node.setColor(*color)
        return node

    def build_world(self):
        self.make_box(
            "ground", (180, 650, 0.25), (0, 300, -0.45),
            (0.18, 0.42, 0.20, 1)
        )
        self.make_box(
            "road", (8.5, 650, 0.18), (0, 300, -0.12),
            (0.12, 0.13, 0.15, 1)
        )

        for x in (-8.9, 8.9):
            self.make_box(
                "road-shoulder", (0.45, 650, 0.2), (x, 300, -0.08),
                (0.82, 0.82, 0.78, 1)
            )

        # Fewer markings and scenery keep the mobile scene lighter.
        for y in range(-20, 1000, 24):
            for x in (-2.85, 2.85):
                self.make_box(
                    "lane-mark", (0.075, 5.0, 0.025), (x, y, 0.075),
                    (0.95, 0.94, 0.82, 1)
                )

        for side in (-1, 1):
            self.make_box(
                "guard-rail", (0.16, 650, 0.16),
                (side * 9.5, 300, 0.85), (0.72, 0.75, 0.78, 1)
            )
            for y in range(-10, 1000, 32):
                self.make_box(
                    "rail-post", (0.13, 0.16, 0.75),
                    (side * 9.5, y, 0.05), (0.42, 0.45, 0.48, 1)
                )

        random.seed(18)
        for y in range(-10, 1000, 36):
            for side in (-1, 1):
                x = side * random.uniform(13, 31)
                self.make_tree(
                    x, y + random.uniform(-7, 7),
                    random.uniform(0.8, 1.35)
                )

        for i in range(18):
            x = random.choice([-1, 1]) * random.uniform(14, 40)
            y = random.uniform(-10, 950)
            self.make_box(
                "rock",
                (random.uniform(0.5, 1.4),
                 random.uniform(0.5, 1.4),
                 random.uniform(0.25, 0.7)),
                (x, y, -0.05), (0.35, 0.38, 0.37, 1)
            )

        for i in range(18):
            x = -95 + i * 11
            mountain = self.loader.loadModel("models/cone")
            mountain.reparentTo(self.render)
            mountain.setScale(12, 12, random.uniform(12, 23))
            mountain.setPos(x, 420 + random.uniform(-25, 25), 10)
            mountain.setColor(0.35, 0.43, 0.48, 1)

        # Checkered finish line.
        for i in range(18):
            tile_color = (
                (0.95, 0.95, 0.95, 1)
                if i % 2 == 0 else (0.08, 0.08, 0.08, 1)
            )
            self.make_box(
                "finish-tile", (0.95, 1.0, 0.12),
                (-8.0 + i * 0.95, 520, 0.12), tile_color
            )

    def make_tree(self, x, y, scale=1.0):
        self.make_box(
            "tree-trunk",
            (0.22 * scale, 0.22 * scale, 1.4 * scale),
            (x, y, 1.1 * scale), (0.30, 0.17, 0.08, 1)
        )

        crown = self.loader.loadModel("models/sphere")
        crown.reparentTo(self.render)
        crown.setScale(1.15 * scale, 1.10 * scale, 1.5 * scale)
        crown.setPos(x, y, 3.0 * scale)
        crown.setColor(0.10, random.uniform(0.32, 0.48), 0.12, 1)

    def make_car(self, color, name):
        root = self.render.attachNewNode(name)

        self.make_box(
            "car-body", (1.05, 2.05, 0.42), (0, 0, 0.62), color, root
        )
        brighter = (
            min(1.0, color[0] * 1.12),
            min(1.0, color[1] * 1.12),
            min(1.0, color[2] * 1.12),
            1
        )
        self.make_box(
            "car-hood", (0.92, 0.78, 0.18), (0, 1.05, 0.98),
            brighter, root
        )
        self.make_box(
            "car-cabin", (0.72, 0.88, 0.48), (0, -0.15, 1.08),
            (0.08, 0.13, 0.18, 1), root
        )
        self.make_box(
            "car-roof", (0.69, 0.78, 0.07), (0, -0.12, 1.56),
            color, root
        )

        for wx in (-1.02, 1.02):
            for wy in (-1.25, 1.25):
                self.make_box(
                    "wheel", (0.22, 0.48, 0.42), (wx, wy, 0.38),
                    (0.025, 0.025, 0.03, 1), root
                )

        for hx in (-0.65, 0.65):
            self.make_box(
                "headlight", (0.22, 0.08, 0.12), (hx, 2.08, 0.72),
                (1.0, 0.92, 0.55, 1), root
            )

        for rx in (-0.65, 0.65):
            self.make_box(
                "taillight", (0.22, 0.08, 0.12), (rx, -2.08, 0.72),
                (0.9, 0.05, 0.03, 1), root
            )

        return root

    def make_opponents(self):
        colors = [
            (0.9, 0.12, 0.08, 1),
            (0.95, 0.68, 0.05, 1),
            (0.12, 0.72, 0.28, 1),
            (0.72, 0.16, 0.82, 1),
            (0.9, 0.9, 0.9, 1),
            (0.05, 0.65, 0.75, 1),
        ]
        lanes = [-5.6, -2.8, 0, 2.8, 5.6]

        for i in range(6):
            car = self.make_car(colors[i % len(colors)], "RIVAL")
            x = random.choice(lanes)
            y = 55 + i * 62
            car.setPos(x, y, 0.12)
            self.opponents.append({
                "node": car,
                "x": x,
                "y": y,
                "speed": random.uniform(12, 23),
                "phase": random.uniform(0, 6.28),
            })

    def setup_hud(self):
        self.hud_bg = DirectFrame(
            frameColor=(0.015, 0.025, 0.04, 0.68),
            frameSize=(-1.32, 1.32, -0.15, 0.15),
            pos=(0, 0, 0.88)
        )

        self.speed_text = OnscreenText(
            text="SPEED 0",
            pos=(-1.12, 0.91),
            scale=0.052,
            fg=(1, 1, 1, 1),
            align=TextNode.ALeft,
            mayChange=True,
        )
        self.nitro_text = OnscreenText(
            text="NITRO 100%",
            pos=(0, 0.91),
            scale=0.048,
            fg=(0.35, 0.85, 1, 1),
            align=TextNode.ACenter,
            mayChange=True,
        )
        self.distance_text = OnscreenText(
            text="DISTANCE 0 m",
            pos=(1.12, 0.91),
            scale=0.048,
            fg=(1, 1, 1, 1),
            align=TextNode.ARight,
            mayChange=True,
        )
        self.message = OnscreenText(
            text="",
            pos=(0, 0.25),
            scale=0.085,
            fg=(1, 0.9, 0.25, 1),
            align=TextNode.ACenter,
            mayChange=True,
            shadow=(0, 0, 0, 0.8),
        )

    def setup_mobile_controls(self):
        # Buttons are positioned in aspect2d and work as on-screen controls.
        self.mobile_buttons = []

        button_specs = [
            ("LEFT", -1.08, -0.70, "left", 0.19),
            ("RIGHT", -0.66, -0.70, "right", 0.19),
            ("BRAKE", 0.62, -0.70, "back", 0.20),
            ("GAS", 1.06, -0.70, "forward", 0.19),
            ("NITRO", 0.84, -0.36, "nitro", 0.18),
        ]

        for label, x, z, key, half_width in button_specs:
            button = DirectButton(
                text=label,
                text_scale=0.42,
                text_fg=(1, 1, 1, 1),
                frameColor=(0.04, 0.20, 0.42, 0.88),
                frameSize=(-half_width, half_width, -0.13, 0.13),
                pos=(x, 0, z),
                relief=DGG.FLAT,
                pressEffect=1,
                command=None,
            )
            button.bind(DGG.B1PRESS, self.set_key, [key, True])
            button.bind(DGG.B1RELEASE, self.set_key, [key, False])
            self.mobile_buttons.append(button)

        restart_button = DirectButton(
            text="RESTART",
            text_scale=0.34,
            text_fg=(1, 1, 1, 1),
            frameColor=(0.20, 0.20, 0.22, 0.82),
            frameSize=(-0.19, 0.19, -0.10, 0.10),
            pos=(-1.02, 0, 0.62),
            relief=DGG.FLAT,
            command=self.restart,
        )
        self.mobile_buttons.append(restart_button)

    def accept_keyboard_for_testing(self):
        # Optional keyboard controls for desktop testing.
        mapping = {
            "w": ("forward", True), "w-up": ("forward", False),
            "arrow_up": ("forward", True), "arrow_up-up": ("forward", False),
            "s": ("back", True), "s-up": ("back", False),
            "arrow_down": ("back", True), "arrow_down-up": ("back", False),
            "a": ("left", True), "a-up": ("left", False),
            "arrow_left": ("left", True), "arrow_left-up": ("left", False),
            "d": ("right", True), "d-up": ("right", False),
            "arrow_right": ("right", True), "arrow_right-up": ("right", False),
            "space": ("nitro", True), "space-up": ("nitro", False),
        }

        for event_name, (action, value) in mapping.items():
            self.accept(event_name, self.set_key, [action, value])

        self.accept("r", self.restart)
        self.accept("escape", self.userExit)

    def set_key(self, key, value):
        self.keys[key] = value

    def show_message(self, message, seconds=2.0):
        self.message.setText(message)
        self.message_timer = seconds

    def restart(self):
        self.player_x = 0.0
        self.player_y = 0.0
        self.speed = 0.0
        self.steer = 0.0
        self.nitro = 100.0
        self.distance = 0.0
        self.finished = False

        for key in self.keys:
            self.keys[key] = False

        self.player.setPos(0, 0, 0.12)
        for i, rival in enumerate(self.opponents):
            rival["x"] = random.choice([-5.6, -2.8, 0, 2.8, 5.6])
            rival["y"] = 55 + i * 62
            rival["node"].setPos(rival["x"], rival["y"], 0.12)

        self.show_message("RACE RESTARTED!", 1.5)

    def update(self, task):
        dt = min(globalClock.getDt(), 0.04)

        if self.message_timer > 0:
            self.message_timer -= dt
            if self.message_timer <= 0:
                self.message.setText("")

        if not self.finished:
            if self.keys["forward"]:
                self.speed += 23.0 * dt
            elif self.keys["back"]:
                self.speed -= 32.0 * dt
            else:
                if self.speed > 0:
                    self.speed = max(0, self.speed - 7.0 * dt)
                elif self.speed < 0:
                    self.speed = min(0, self.speed + 7.0 * dt)

            using_nitro = (
                self.keys["nitro"] and self.nitro > 0 and self.speed > 8
            )
            max_speed = 62 if using_nitro else 42

            if using_nitro:
                self.speed += 18 * dt
                self.nitro = max(0, self.nitro - 27 * dt)
            else:
                self.nitro = min(100, self.nitro + 8 * dt)

            self.speed = max(-8, min(max_speed, self.speed))

            steer_input = (
                (1 if self.keys["right"] else 0)
                - (1 if self.keys["left"] else 0)
            )
            self.steer += (steer_input - self.steer) * min(1, dt * 8)

            steering_power = 7.8 * (0.35 + abs(self.speed) / 42)
            self.player_x += self.steer * steering_power * dt
            self.player_x = max(-7.1, min(7.1, self.player_x))

            self.player_y += self.speed * dt
            self.distance = max(0, self.player_y)

            self.player.setPos(self.player_x, self.player_y, 0.12)
            self.player.setHpr(-self.steer * 8, 0, -self.steer * 5)

            for rival in self.opponents:
                rival["y"] += rival["speed"] * dt
                rival["x"] += (
                    math.sin(task.time * 0.7 + rival["phase"]) * 0.22 * dt
                )

                if rival["y"] < self.player_y - 22:
                    rival["y"] = self.player_y + random.uniform(180, 340)
                    rival["x"] = random.choice([-5.6, -2.8, 0, 2.8, 5.6])

                rival["node"].setPos(rival["x"], rival["y"], 0.12)

                dx = abs(rival["x"] - self.player_x)
                dy = abs(rival["y"] - self.player_y)
                if dx < 1.65 and dy < 3.2 and self.speed > 2:
                    self.speed *= 0.48
                    self.player_y -= 1.0
                    self.show_message("BUMP! WATCH THE ROAD!", 0.8)

            if self.player_y >= 520:
                self.finished = True
                self.speed = 0
                self.show_message("FINISH! YOU DID IT!", 10)

        cam_x = self.player_x * 0.42
        self.camera.setPos(cam_x, self.player_y - 17, 7.2)
        self.camera.lookAt(
            self.player_x * 0.15, self.player_y + 12, 0.65
        )

        self.speed_text.setText(
            "SPEED  %d km/h" % int(abs(self.speed) * 3.6)
        )
        self.nitro_text.setText("NITRO  %d%%" % int(self.nitro))
        self.distance_text.setText(
            "DISTANCE  %d m" % int(self.distance)
        )

        return task.cont


if __name__ == "__main__":
    game = RacingGame()
    game.run()
