"""
ALI X STAR RACING 3D
A procedural 3D arcade racing prototype made with Panda3D.
No external art assets are required.

Controls:
  W / Up       Accelerate
  S / Down     Brake / reverse
  A,D / arrows Steer
  SPACE        Nitro boost
  R            Restart race
  ESC          Quit
"""

from direct.showbase.ShowBase import ShowBase
from direct.gui.OnscreenText import OnscreenText
from direct.gui.DirectGui import DirectFrame
from panda3d.core import (
    AmbientLight, DirectionalLight, Fog, Vec3, Vec4,
    Point3, TextNode, WindowProperties
)
import random
import math


class RacingGame(ShowBase):
    def __init__(self):
        super().__init__()
        self.disableMouse()
        self.setBackgroundColor(0.42, 0.68, 0.88, 1)

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
        self.crash_flash = 0.0
        self.keys = {k: False for k in
                     ["forward", "back", "left", "right", "nitro"]}

        self.setup_lighting()
        self.build_world()
        self.player = self.make_car((0.05, 0.35, 0.95, 1), "PLAYER")
        self.player.setPos(0, 0, 0.12)

        self.opponents = []
        self.make_opponents()
        self.setup_hud()
        self.accept_keys()

        self.camera.setPos(0, -17, 7.2)
        self.camera.lookAt(0, 12, 0.7)
        self.camLens.setFov(78)

        self.taskMgr.add(self.update, "update")
        self.show_message("READY?  3... 2... 1... GO!", 2.2)

    def setup_lighting(self):
        ambient = AmbientLight("ambient")
        ambient.setColor(Vec4(0.55, 0.58, 0.65, 1))
        self.render.setLight(self.render.attachNewNode(ambient))

        sun = DirectionalLight("sun")
        sun.setColor(Vec4(1.0, 0.92, 0.78, 1))
        sun_np = self.render.attachNewNode(sun)
        sun_np.setHpr(-35, -55, 0)
        self.render.setLight(sun_np)

        fog = Fog("distance-fog")
        fog.setColor(0.55, 0.72, 0.82)
        fog.setExpDensity(0.0025)
        self.render.setFog(fog)

    def build_world(self):
        # Ground and long asphalt road
        ground = self.loader.loadModel("models/box")
        ground.reparentTo(self.render)
        ground.setScale(180, 650, 0.25)
        ground.setPos(0, 300, -0.45)
        ground.setColor(0.18, 0.42, 0.20, 1)

        road = self.loader.loadModel("models/box")
        road.reparentTo(self.render)
        road.setScale(8.5, 650, 0.18)
        road.setPos(0, 300, -0.12)
        road.setColor(0.12, 0.13, 0.15, 1)

        # Road shoulders
        for x in (-8.9, 8.9):
            shoulder = self.loader.loadModel("models/box")
            shoulder.reparentTo(self.render)
            shoulder.setScale(0.45, 650, 0.2)
            shoulder.setPos(x, 300, -0.08)
            shoulder.setColor(0.82, 0.82, 0.78, 1)

        # Dashed lane markings
        for y in range(-20, 1000, 18):
            for x in (-2.85, 2.85):
                line = self.loader.loadModel("models/box")
                line.reparentTo(self.render)
                line.setScale(0.075, 5.0, 0.025)
                line.setPos(x, y, 0.075)
                line.setColor(0.95, 0.94, 0.82, 1)

        # Guard rails and posts
        for side in (-1, 1):
            rail = self.loader.loadModel("models/box")
            rail.reparentTo(self.render)
            rail.setScale(0.16, 650, 0.16)
            rail.setPos(side * 9.5, 300, 0.85)
            rail.setColor(0.72, 0.75, 0.78, 1)
            for y in range(-10, 1000, 20):
                post = self.loader.loadModel("models/box")
                post.reparentTo(self.render)
                post.setScale(0.13, 0.16, 0.75)
                post.setPos(side * 9.5, y, 0.05)
                post.setColor(0.42, 0.45, 0.48, 1)

        # Procedural trees and rocks along the road
        random.seed(18)
        for y in range(-10, 1000, 24):
            for side in (-1, 1):
                x = side * random.uniform(13, 35)
                self.make_tree(x, y + random.uniform(-7, 7),
                               random.uniform(0.8, 1.5))
        for i in range(45):
            x = random.choice([-1, 1]) * random.uniform(14, 45)
            y = random.uniform(-10, 950)
            rock = self.loader.loadModel("models/box")
            rock.reparentTo(self.render)
            rock.setScale(random.uniform(.5, 1.6),
                          random.uniform(.5, 1.5),
                          random.uniform(.25, .8))
            rock.setPos(x, y, -0.05)
            rock.setColor(0.35, 0.38, 0.37, 1)

        # Distant simple mountain silhouettes
        for i in range(24):
            x = -100 + i * 9
            mountain = self.loader.loadModel("models/cone")
            mountain.reparentTo(self.render)
            mountain.setScale(random.uniform(9, 18),
                              random.uniform(9, 18),
                              random.uniform(12, 25))
            mountain.setPos(x, 420 + random.uniform(-30, 30), 10)
            mountain.setColor(0.35, 0.43, 0.48, 1)

        # Finish line far ahead
        for i in range(18):
            tile = self.loader.loadModel("models/box")
            tile.reparentTo(self.render)
            tile.setScale(0.95, 1.0, 0.12)
            tile.setPos(-8.0 + i * 0.95, 520, 0.12)
            tile.setColor(0.95, 0.95, 0.95, 1) if i % 2 == 0 else tile.setColor(0.08, 0.08, 0.08, 1)

    def make_tree(self, x, y, scale=1.0):
        trunk = self.loader.loadModel("models/box")
        trunk.reparentTo(self.render)
        trunk.setScale(0.22 * scale, 0.22 * scale, 1.4 * scale)
        trunk.setPos(x, y, 1.1 * scale)
        trunk.setColor(0.30, 0.17, 0.08, 1)

        crown = self.loader.loadModel("models/sphere")
        crown.reparentTo(self.render)
        crown.setScale(1.25 * scale, 1.15 * scale, 1.65 * scale)
        crown.setPos(x, y, 3.0 * scale)
        crown.setColor(0.10, random.uniform(.32, .48), 0.12, 1)

    def make_car(self, color, name):
        root = self.render.attachNewNode(name)
        body = self.loader.loadModel("models/box")
        body.reparentTo(root)
        body.setScale(1.05, 2.05, 0.42)
        body.setPos(0, 0, 0.62)
        body.setColor(*color)

        hood = self.loader.loadModel("models/box")
        hood.reparentTo(root)
        hood.setScale(0.92, 0.78, 0.18)
        hood.setPos(0, 1.05, 0.98)
        hood.setColor(*(min(1, c * 1.12) for c in color[:3]), 1)

        cabin = self.loader.loadModel("models/box")
        cabin.reparentTo(root)
        cabin.setScale(0.72, 0.88, 0.48)
        cabin.setPos(0, -0.15, 1.08)
        cabin.setColor(0.08, 0.13, 0.18, 1)

        roof = self.loader.loadModel("models/box")
        roof.reparentTo(root)
        roof.setScale(0.69, 0.78, 0.07)
        roof.setPos(0, -0.12, 1.56)
        roof.setColor(*color)

        # Wheels: dark blocks, deliberately simple and robust
        for wx in (-1.02, 1.02):
            for wy in (-1.25, 1.25):
                wheel = self.loader.loadModel("models/box")
                wheel.reparentTo(root)
                wheel.setScale(0.22, 0.48, 0.42)
                wheel.setPos(wx, wy, 0.38)
                wheel.setColor(0.025, 0.025, 0.03, 1)

        for hx in (-0.65, 0.65):
            lamp = self.loader.loadModel("models/box")
            lamp.reparentTo(root)
            lamp.setScale(0.22, 0.08, 0.12)
            lamp.setPos(hx, 2.08, 0.72)
            lamp.setColor(1.0, 0.92, 0.55, 1)

        for rx in (-0.65, 0.65):
            lamp = self.loader.loadModel("models/box")
            lamp.reparentTo(root)
            lamp.setScale(0.22, 0.08, 0.12)
            lamp.setPos(rx, -2.08, 0.72)
            lamp.setColor(0.9, 0.05, 0.03, 1)
        return root

    def make_opponents(self):
        colors = [
            (0.9, 0.12, 0.08, 1), (0.95, 0.68, 0.05, 1),
            (0.12, 0.72, 0.28, 1), (0.72, 0.16, 0.82, 1),
            (0.9, 0.9, 0.9, 1), (0.05, 0.65, 0.75, 1)
        ]
        lanes = [-5.6, -2.8, 0, 2.8, 5.6]
        for i in range(9):
            car = self.make_car(colors[i % len(colors)], "RIVAL")
            y = 55 + i * 48
            x = random.choice(lanes)
            car.setPos(x, y, 0.12)
            self.opponents.append({
                "node": car, "x": x, "y": y,
                "speed": random.uniform(12, 25),
                "phase": random.uniform(0, 6.28)
            })

    def setup_hud(self):
        self.hud_bg = DirectFrame(
            frameColor=(0.015, 0.025, 0.04, 0.72),
            frameSize=(-1.32, 1.32, -0.18, 0.18),
            pos=(0, 0, 0.82)
        )
        self.speed_text = OnscreenText(
            text="SPEED  0 km/h", pos=(-1.05, 0.92),
            scale=0.055, fg=(1, 1, 1, 1),
            align=TextNode.ALeft, mayChange=True
        )
        self.nitro_text = OnscreenText(
            text="NITRO  100%", pos=(0, 0.92),
            scale=0.05, fg=(0.35, 0.85, 1, 1),
            align=TextNode.ACenter, mayChange=True
        )
        self.distance_text = OnscreenText(
            text="DISTANCE  0 m", pos=(1.05, 0.92),
            scale=0.05, fg=(1, 1, 1, 1),
            align=TextNode.ARight, mayChange=True
        )
        self.help_text = OnscreenText(
            text="W/↑ GAS   S/↓ BRAKE   A,D/←,→ STEER   SPACE NITRO   R RESTART",
            pos=(0, -0.94), scale=0.035, fg=(1, 1, 1, 0.9),
            align=TextNode.ACenter
        )
        self.message = OnscreenText(
            text="", pos=(0, 0.25), scale=0.085,
            fg=(1, 0.9, 0.25, 1), align=TextNode.ACenter,
            mayChange=True, shadow=(0, 0, 0, 0.8)
        )

    def show_message(self, msg, seconds=2):
        self.message.setText(msg)
        self.message_timer = seconds

    def accept_keys(self):
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
        for key, (action, value) in mapping.items():
            self.accept(key, self.set_key, [action, value])
        self.accept("r", self.restart)
        self.accept("escape", self.userExit)

    def set_key(self, key, value):
        self.keys[key] = value

    def restart(self):
        self.player_x = 0
        self.player_y = 0
        self.speed = 0
        self.nitro = 100
        self.distance = 0
        self.finished = False
        self.player.setPos(0, 0, 0.12)
        for i, rival in enumerate(self.opponents):
            rival["x"] = random.choice([-5.6, -2.8, 0, 2.8, 5.6])
            rival["y"] = 55 + i * 48
            rival["node"].setPos(rival["x"], rival["y"], 0.12)
        self.show_message("RACE RESTARTED!", 1.5)

    def update(self, task):
        dt = min(globalClock.getDt(), 0.04)
        if self.message_timer > 0:
            self.message_timer -= dt
            if self.message_timer <= 0:
                self.message.setText("")

        if not self.finished:
            # Acceleration, braking, drag
            if self.keys["forward"]:
                self.speed += 23.0 * dt
            elif self.keys["back"]:
                self.speed -= 32.0 * dt
            else:
                self.speed -= math.copysign(min(abs(self.speed), 7.0 * dt), self.speed)

            using_nitro = self.keys["nitro"] and self.nitro > 0 and self.speed > 8
            max_speed = 62 if using_nitro else 42
            if using_nitro:
                self.speed += 18 * dt
                self.nitro = max(0, self.nitro - 27 * dt)
            else:
                self.nitro = min(100, self.nitro + 8 * dt)
            self.speed = max(-8, min(max_speed, self.speed))

            steer_input = (1 if self.keys["right"] else 0) - (1 if self.keys["left"] else 0)
            self.steer += (steer_input - self.steer) * min(1, dt * 8)
            steering_power = 7.8 * (0.35 + abs(self.speed) / 42)
            self.player_x += self.steer * steering_power * dt
            self.player_x = max(-7.1, min(7.1, self.player_x))
            self.player_y += self.speed * dt
            self.distance = max(0, self.player_y)

            # Slight body lean while steering
            self.player.setPos(self.player_x, self.player_y, 0.12)
            self.player.setHpr(-self.steer * 8, 0, -self.steer * 5)

            # Opponent traffic moves forward at its own pace
            for rival in self.opponents:
                rival["y"] += rival["speed"] * dt
                rival["x"] += math.sin(task.time * 0.7 + rival["phase"]) * 0.22 * dt
                if rival["y"] < self.player_y - 22:
                    rival["y"] = self.player_y + random.uniform(180, 360)
                    rival["x"] = random.choice([-5.6, -2.8, 0, 2.8, 5.6])
                rival["node"].setPos(rival["x"], rival["y"], 0.12)

                # Arcade collision check
                dx = abs(rival["x"] - self.player_x)
                dy = abs(rival["y"] - self.player_y)
                if dx < 1.65 and dy < 3.2 and self.speed > 2:
                    self.speed *= 0.48
                    self.player_y -= 1.0
                    self.crash_flash = 0.18
                    self.show_message("BUMP! WATCH THE ROAD!", 0.8)

            if self.player_y >= 520:
                self.finished = True
                self.speed = 0
                self.show_message("🏁 FINISH!  YOU DID IT!", 10)

        # Follow camera, slight lateral smoothing
        cam_x = self.player_x * 0.42
        self.camera.setPos(cam_x, self.player_y - 17, 7.2)
        self.camera.lookAt(self.player_x * 0.15, self.player_y + 12, 0.65)

        self.speed_text.setText("SPEED  %d km/h" % int(abs(self.speed) * 3.6))
        self.nitro_text.setText("NITRO  %d%%" % int(self.nitro))
        self.distance_text.setText("DISTANCE  %d m" % int(self.distance))

        return task.cont


if __name__ == "__main__":
    game = RacingGame()
    game.run()
