import pygame
pygame.font.init()
import pymunk as pym
import pymunk.pygame_util
import numpy as npy
import matplotlib.pyplot as plt
import pygame
import time as t
import random as r
import gymnasium as gym
from gymnasium import spaces
import pdb


clock = pygame.time.Clock()
screen = pygame.display.set_mode((1000, 600))
#control_panel = pygame.Surface((160, 1000))
pygame.display.set_caption("")

draw_options = pymunk.pygame_util.DrawOptions(screen)

bullets = []
explosions = []
guns = ["ball", "grenade"]
enemies = []

class Player:
    def __init__(self, space, env=None, color=(0, 0, 255)):
        self.env = env
        self.space = space
        self.color = color
        self.body = pym.Body(10, pym.moment_for_box(10, (25, 25)), body_type=pym.Body.DYNAMIC)
        self.body.position = (500 + r.randint(-100, 100), 300)
        self.body.angle = 0
        self.bodyShape = pym.Poly.create_box(self.body, (25, 25), 0.5)
        self.bodyShape.elasticity = 0.0
        self.bodyShape.friction = 0.5
        self.bodyShape.data = self
        self.bodyShape.collision_type = 1
        self.maxspeedx = 400
        self.maxspeedy = 800
        self.jump = 400
        self.jumpCooldown = 0
        self.fireCooldown = 0
        self.gun = 'grenade'
        self.health = 100
        self.maxHealth = 100
        self.damageTimer = 15
        self.isCrouching = False
        self.reward = 0
        if self == self.env.PlayerA:
            self.enemy = self.env.PlayerB
        else:
            self.enemy = self.env.PlayerA
        self.space.add(self.body, self.bodyShape)

    def draw(self, surface):
        self.vertices = [to_pygame(self.body.local_to_world(v), self.env.camerapos) for v in self.bodyShape.get_vertices()]
        self.PYGpoly = pygame.draw.polygon(surface, self.color, self.vertices)
        text(str(self.health), surface, 10, to_pygame(self.body.position + (0, -20), self.env.camerapos), (255, 255, 255), (0, 0, 0))
        #pygame.draw.circle(surface, (255, 255, 255), self.body.position, 6)

    def isGettingDamaged(self):
        for e in self.env.explosions:
            print("check")
            if e.isWithinRange(self.body.position):
                return True
        return False

    def update(self, action):
        self.reward = 0
        self.damageTimer -= 1
        self.body.angle = 0
        self.bodyShape.friction = 1
        if self.onGround and self.jumpCooldown <= 0:
            self.canJump = True
        else:
            self.canJump = False
        print(self.onGround)

        self.jumpCooldown -= 1
        self.fireCooldown -= 1

        if action[0] == 0:
            if self.canJump:
                self.body.velocity += (0, -self.jump)
                self.jumpCooldown = 80
        if action[0] == 1:
            self.bodyShape.friction = 10
            self.isCrouching = True
            print(self.isCrouching)
        else:
            self.isCrouching = False
        if action[0] == 2:
            self.bodyShape.friction = 0.2
            if self.body.velocity[0] < self.maxspeedx:
                if self.onGround:
                    self.body.apply_force_at_local_point((20000, 0))
                else:
                    self.body.apply_force_at_local_point((5000, 0))
        if action[0] == 3:
            self.bodyShape.friction = 0.2
            if self.body.velocity[0] > -self.maxspeedx:
                if self.onGround:
                    self.body.apply_force_at_local_point((-20000, 0))
                else:
                    self.body.apply_force_at_local_point((-5000, 0))

        if action[1] == 1 and self.fireCooldown < 0:
            self.fire(action[2])

        if self.body.velocity[1] > 10:
            self.body.apply_force_at_world_point((0, 3000), self.body.position)

        if self.isGettingDamaged() and self.damageTimer < 0:
            self.reward -= 5
            self.health -= 5
            print("ow")
            self.damageTimer = 10

        return self.reward
    def fire(self, angle):
        if self.gun == "grenade":
            Grenade(300, angle, self.body.position, self, self.env.space)

    def reset(self):
        self.body.position = (500 + r.randint(-100, 100), 300)
        self.body.angle = 0
        self.bodyShape.data = self
        self.jumpCooldown = 0
        self.fireCooldown = 0
        self.health = 100
        self.isCrouching = False
        self.space.add(self.body, self.bodyShape)



'''
class BallBullet:
    def __init__(self, speed, angle, pos, player):
        bullets.append(self)
        self.body = pym.Body(5, pym.moment_for_circle(10, 0, 6), body_type=pym.Body.DYNAMIC)
        try:
            self.body.position = pos + (20 * npy.cos(angle), 20 * npy.sin(angle))
        except AssertionError:
            pass
        self.bodyShape = pym.Circle(self.body, 6)
        self.bodyShape.elasticity = 0.95
        self.bodyShape.friction = 0
        self.lifeCycle = 1000
        self.bodyShape.user_data = self
        self.bodyShape.collision_type = 3
        self.cooldown = 7
        self.body.velocity = (speed * npy.cos(angle), speed * npy.sin(angle))
        player.fireCooldown = self.cooldown
        self.space.add(self.body, self.bodyShape)

    def onTouchingEnemy(self, enemy):
        pass

    def update(self, surface):
        b.lifeCycle -= 1
        if self.lifeCycle < 0:
            bullets.remove(self)
            delete(self)
        pygame.draw.circle(screen, (0, 255, 255), to_pygame(self.body.position, self.env.camerapos), 6)
'''
class Grenade:
    def __init__(self, speed, angle, pos, player, space):
        self.space = space
        player.env.bullets.append(self)
        self.body = pym.Body(3, pym.moment_for_circle(10, 0, 6), body_type=pym.Body.DYNAMIC)
        try:
            self.body.position = pos + (20 * npy.cos(angle), 20 * npy.sin(angle))
        except AssertionError:
            pass
        self.bodyShape = pym.Circle(self.body, 6)
        self.bodyShape.elasticity = 0.8
        self.bodyShape.friction = 0
        self.lifeCycle = 100
        self.hasExploded = False
        self.bodyShape.user_data = self
        self.bodyShape.collision_type = 3
        self.cooldown = 10
        self.body.velocity = (speed * npy.cos(angle), speed * npy.sin(angle))
        self.player = player
        self.env = self.player.env
        player.fireCooldown = self.cooldown
        self.space.add(self.body, self.bodyShape)

    def update(self, screen):
        pygame.draw.circle(screen, (90, 90, 90), to_pygame(self.body.position, self.player.env.camerapos), 6)
        self.lifeCycle -= 1
        if self.lifeCycle < 0:
            self.explode()

    def onTouchingEnemy(self, enemy):
        self.explode()

    def explode(self):
        Explosion(80, self.body.position, 10, self.env)
        try:
            self.player.env.bullets.remove(self)
        except ValueError:
            pass
        delete(self)

class Explosion:
    def __init__(self, rad, pos, span, env=None):
        self.pos = pos
        self.rad = rad
        self.lifeCycle = span
        self.env = env
        self.env.explosions.append(self)
        for body in getAllBodies():
            if self.isWithinRange(body.position):
                dis = get_dist(self.pos, body.position)
                strength = -20000/body.mass
                body.apply_impulse_at_world_point((strength*dis[1]/dis[0], strength*dis[2]/dis[0]), body.position)

    def draw(self, surface):
        pygame.draw.circle(surface, (204, 102, 0), to_pygame(self.pos, self.env.camerapos), self.rad)
        self.lifeCycle -= 1
        if self.lifeCycle < 0:
            self.env.explosions.remove(self)

    def isWithinRange(self, pos):
        if (pos[0] - self.pos[0])**2 + (pos[1] - self.pos[1])**2 <= self.rad**2:
            return True
        return False

'''
class TriangleEnemy:
    def __init__(self, pos):
        enemies.append(self)
        self.body = pym.Body(20, pym.moment_for_poly(10, [(0, 14.43), (-12.5, -7.21), (12.5, -7.21)]), body_type=pym.Body.DYNAMIC)
        try:
            self.body.position = pos
        except AssertionError:
            pass
        self.bodyShape = pym.Poly(self.body, [(0, 14.43), (-12.5, -7.21), (12.5, -7.21)])
        self.bodyShape.elasticity = 0.8
        self.bodyShape.friction = 0.1
        self.bodyShape.user_data = self
        self.bodyShape.collision_type = 4
        self.health = 100
        self.maxHealth = 100
        self.healTimer = 3
        self.damageTimer = 10
        space.add(self.body, self.bodyShape)

    def draw(self, surface):
        self.vertices = [to_pygame(self.body.local_to_world(v)) for v in self.bodyShape.get_vertices()]
        self.PYGpoly = pygame.draw.polygon(surface, (150, 50, 0), self.vertices)
        text(str(self.health), surface, 10, to_pygame(self.body.position + (0, -20)), (255, 255, 255), (0, 0, 0))
        self.body.apply_impulse_at_world_point((0, -160), self.body.position)
        self.body.angular_velocity *= 0.98

    def isGettingDamaged(self):
        for e in explosions:
            print("check")
            if e.isWithinRange(self.body.position):
                return True
        return False

    def onTouchingBullet(self, bullet):
        pass

    def update(self):
        self.healTimer -= 1
        self.damageTimer -= 1
        if self.healTimer < 0 and self.health < self.maxHealth:
            self.health += 1
            self.healTimer = 3
            print("heal")
        if self.isGettingDamaged() and self.damageTimer < 0:
            self.health -= 30
            print("ow")
            self.damageTimer = 10
'''

class Rect:
    def __init__(self, pos, size, env=None):
        self.space = env.space
        self.body = pym.Body(body_type=pym.Body.KINEMATIC)
        self.body.position = pos
        self.bodyShape = pym.Poly.create_box(self.body, size, 0.5)
        self.bodyShape.elasticity = 1
        self.bodyShape.friction = 1
        self.bodyShape.collision_type = 2
        self.env = env
        self.space.add(self.body, self.bodyShape)

    def draw(self, surface):
        self.vertices = [to_pygame(self.body.local_to_world(v), self.env.camerapos) for v in self.bodyShape.get_vertices()]
        self.PYGpoly = pygame.draw.polygon(surface, (100, 100, 100), self.vertices)

class GunEnv(gym.Env):
    WinLoseRew = 10
    damageRew = 1
    space = pym.Space()
    space.gravity = (0, 500)
    space.iterations = 30

    clock = pygame.time.Clock()
    frame = 0
    screen = pygame.display.set_mode((1000, 600))
    pygame.display.set_caption("")

    maxTrainingSteps = 10000
    trainingSteps = 0

    bullets = []
    explosions = []
    guns = ["grenade"]

    def __init__(self, isRendering, hasHumanPlayer):
        self.isRendering = isRendering
        self.hasHumanPlayer = hasHumanPlayer
        self.PlayerA = Player(self.space, self, (200, 0, 0))
        self.PlayerB = Player(self.space, self, (0, 0, 200))
        self.action_space = spaces.Tuple((spaces.Discrete(4), spaces.Discrete(359),
                                         spaces.Discrete(1))) #(button, isFiring, firingAngle)
        self.observation_space = spaces.Tuple((spaces.Box(low=-npy.inf, high=npy.inf, shape=(2, 2)),
                                               spaces.Box(low=-npy.inf, high=npy.inf, shape=(2, 2)),
                                               spaces.Sequence(spaces.Box(low=-npy.inf, high=npy.inf, shape=(2,2)))))
                                               #((playerPos, playerVel), (enemyPos, enemyVel), ((bulletPos, bulletVel)...))

        self.selectedPlayer = self.PlayerA

        self.ground = [Rect((500, 500), (1000, 100), self),
                  Rect((1300, 450), (1000, 150), self),
                  Rect((-300, 450), (1000, 150), self),
                  Rect([100, 300], [500, 25], self),
                  Rect([1300, 200], [700, 50], self),
                  Rect([1300, 400], [45, 200], self),
                  Rect((2000, 375), (500, 250), self),
                  Rect((1000, 75), (40, 250), self),
                  Rect((2000, 50), (200, 50), self),
                  Rect((-1300, 400), (1000, 75), self),
                  Rect((-1600, 300), (50, 200), self),
                  Rect((-1900, 100), (50, 350), self),
                  Rect((-2300, 400), (1000, 75), self), ]

        if self.isRendering:
            self.camerapos = [0, 0]

    def _get_obs(self):
        playerArr = npy.array(self.PlayerA.body.position, self.PlayerA.body.velocity)
        enemyArr = npy.array(self.PlayerB.body.position, self.PlayerB.body.velocity)
        bulletsArr = [npy.array([b.body.position, b.body.velocity]) for b in self.bullets]
        return (playerArr, enemyArr, bulletsArr)

    def reset(self):
        self.PlayerA.reset()
        self.PlayerB.reset()
        for b in self.bullets:
            delete(b)
        self.bullets = []
        self.explosions = []
        self.trainingSteps = 0
        return self._get_obs(), {}

    def step(self, action):
        reward = 0
        self.trainingSteps += 1
        done = False

        self.PlayerA.onGround = False
        self.PlayerB.onGround = False

        if isNotPaused:
            self.frame += 1
            self.space.step(1 / 60)
        s = t.time()

        screen.fill((0, 0, 0))

        reward += self.PlayerA.update(action)
        reward -= self.PlayerB.update(action)

        if self.PlayerA.health <= 0:
            reward -= 100
            done = True
        if self.PlayerB.health <= 0:
            reward += 100
            done = True

        for e in enemies:
            e.update()

        if self.selectedPlayer == 'A':
            self.camerapos[0] -= ((self.PlayerA.body.position[0]+(((pygame.mouse.get_pos())[0] - 500)/2)/2) + (self.camerapos[0] - 500))/10
            self.camerapos[1] -= ((self.PlayerA.body.position[1]+(((pygame.mouse.get_pos())[1] - 300)/2)/2) + (self.camerapos[1] - 300))/10
        else:
            self.camerapos[0] -= ((self.PlayerB.body.position[0] + (((pygame.mouse.get_pos())[0] - 500) / 2) / 2) + (self.camerapos[0] - 500)) / 10
            self.camerapos[1] -= ((self.PlayerB.body.position[1] + (((pygame.mouse.get_pos())[1] - 300) / 2) / 2) + (self.camerapos[1] - 300)) / 10

        frame_time = t.time() - s
        if frame_time < 1 / 60:
            t.sleep(1 / 60 - frame_time)

        if self.trainingSteps >= self.maxTrainingSteps:
            done = True

        return self._get_obs(), reward, done, {}

    def render(self):
        for exp in self.explosions:
            exp.draw(screen)
        self.PlayerA.draw(screen)
        self.PlayerB.draw(screen)
        for r in self.ground:
            r.draw(screen)
        for b in self.bullets:
            b.update(screen)
        pygame.display.flip()

'''
    To obtain a list of all bodies present in a Pymunk Space object, the pymunk.batch module can be utilized. This module provides efficient methods for retrieving batched data from the space.
The following steps outline the process: Import necessary modules.
Python

    import pymunk
    import pymunk.batch
Create a Space object and add bodies to it:
Python

    s = pymunk.Space()
    b1 = pymunk.Body(1, 100)
    b1.position = 10, 20
    s.add(b1, pymunk.Circle(b1, 5))

    b2 = pymunk.Body(2, 200)
    b2.position = 30, 40
    s.add(b2, pymunk.Circle(b2, 10))
Create a Buffer object to hold the batched data:
Python

    data = pymunk.batch.Buffer()
Call pymunk.batch.get_space_bodies to populate the buffer: Specify the Space object and the desired fields to retrieve using pymunk.batch.BodyFields.
Python

    pymunk.batch.get_space_bodies(s, pymunk.batch.BodyFields.BODY_ID | pymunk.batch.BodyFields.POSITION, data)
Access the retrieved bodies from the Buffer object: The bodies attribute of the Buffer object will contain a list of the retrieved Body objects.
Python

    all_bodies = data.bodies
    print(all_bodies)
This method efficiently retrieves the body data in a batched manner, which can be beneficial for performance when dealing with a large number of bodies.

'''

def onBulletTouchEnemy(arbiter, space, data):
    shape_a, shape_b = arbiter.shapes
    if shape_a.collision_type == 3:
        bulletShape = shape_a
        enemyShape = shape_b
    else:
        bulletShape = shape_b
        enemyShape = shape_a

    bullet = bulletShape.user_data
    enemy = enemyShape.data

    if callable(bullet.onTouchingEnemy):
        bullet.onTouchingEnemy(enemy)

    return None

def to_pygame(pos, camerapos):
    """ Convert Pymunk physics coordinates to Pygame coordinates. """
    if isinstance(pos, list):
        return [(v.x + camerapos[0], v.y + camerapos[1]) for v in pos]
    if isinstance(pos, tuple):  # Handle tuples
        return int(pos[0] + camerapos[0]), int(pos[1] + camerapos[1])
    return int(pos.x + camerapos[0]), int(pos.y + camerapos[1])  # Handle Pymunk Vec2d objects

def to_pymunk(pos, camerapos):
    return (pos[0] - camerapos[0], pos[1] - camerapos[1])

def debug(message, value):
    print(str(message) + ": " + str(value))

def delete(self):
    try:
        env.space.remove(self.body, self.bodyShape)
    except AssertionError:
        pass

def getAllBodies():
    return env.space.bodies

def get_angle(p1, p2):
    return npy.arctan2(p1[1] - p2[1], p1[0] - p2[0])

def get_dist(p1, p2):
    return (npy.sqrt((p1[0] - p2[0])**2 + (p1[1] - p2[1])**2), p1[0] - p2[0], (p1[1] - p2[1]))

def text(text, screen, size, position, color, background):
    font = pygame.font.Font('Quinquefive-KVpBp.ttf', size)
    text_surface = font.render(text, True, color, background)
    text_rect = text_surface.get_rect()
    text_rect.center = position
    screen.blit(text_surface, text_rect)

def ifPlayerOnGround(arbiter, space, data):
    arbiter.shapes[0].data.onGround = True
    return None

running = True
isNotPaused = True
frame = 0


#p = Player()
'''

ground = [
Rect((500, 500), (1000, 100)),
Rect((-50, 0), (100, 1100)),
Rect((1000, 0), (100, 1100)),
Rect((500, 350), (500, 30)),
]
'''
env = GunEnv(True, True)

env.space.on_collision(
    collision_type_a=1,
    collision_type_b=2,
    pre_solve=ifPlayerOnGround,
)

env.space.on_collision(
    collision_type_a=1,
    collision_type_b=3,
    pre_solve=onBulletTouchEnemy,
)

buttons = [pygame.K_w, pygame.K_s, pygame.K_d, pygame.K_a]

while running:
    Keys = pygame.key.get_pressed()
    B = 4
    for b in buttons:
        if Keys[b]:
            B = buttons.index(b)
    if pygame.mouse.get_pressed()[0]:
        isFiring = 1
    else:
        isFiring = 0
    mpos = pygame.mouse.get_pos()
    bodypos = to_pygame(env.selectedPlayer.body.position, env.camerapos)
    angle = get_angle(mpos, bodypos)
    env.step(npy.array([B, isFiring, angle]))
    print([B, isFiring])
    env.render()
    for ev in pygame.event.get():
        if ev.type == pygame.QUIT:
            running = False

'''
camerapos = [30, 0]
while running:
    p.onGround = False

    if isNotPaused:
        frame += 1
        space.step(1 / 60)
    s = t.time()

    screen.fill((0, 0, 0))

    #space.debug_draw(draw_options)

    text(p.gun, screen, 16, (500, 30), (255, 255, 255), (0, 0, 0))
    for exp in explosions:
        exp.draw(screen)
    p.draw(screen)
    for r in ground:
        r.draw(screen)
    for b in bullets:
        b.update(screen)
    for e in enemies:
        e.draw(screen)

    Keys = pygame.key.get_pressed()
    p.update(Keys)
    for e in enemies:
        e.update()
    camerapos[0] -= ((p.body.position[0]+(((pygame.mouse.get_pos())[0] - 500)/2)/2) + (camerapos[0] - 500))/10
    camerapos[1] -= ((p.body.position[1]+(((pygame.mouse.get_pos())[1] - 300)/2)/2) + (camerapos[1] - 300))/10



    for ev in pygame.event.get():


        if ev.type == pygame.QUIT:
            running = False

    pygame.display.flip()
    frame_time = t.time() - s
    # print(f"frametime: 1/{int(1/frame_time)} seconds")
    if frame_time < 1 / 60:
        t.sleep(1 / 60 - frame_time)
      # Pymunk physics step
'''
