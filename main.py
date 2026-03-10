import pdb

import pygame
pygame.font.init()
import matplotlib.pyplot as plt
import pymunk as pym
import pymunk.pygame_util
import numpy as npy
import pygame
import time as t
import random as r
import gymnasium as gym
from gymnasium import spaces


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
    onGround = False
    def __init__(self, space, env=None, color=(0, 0, 255), pos=(500, 300)):
        self.env = env
        self.playerDamageDict = {True: self.env.selfDamagePun, False: self.env.enemyDamageRew}
        self.space = space
        self.color = color
        self.body = pym.Body(10, pym.moment_for_box(10, (25, 25)), body_type=pym.Body.DYNAMIC)
        self.body.position = pos
        self.body.angle = 0
        self.bodyShape = pym.Poly.create_box(self.body, (25, 25), 0.5)
        self.bodyShape.elasticity = 0.0
        self.bodyShape.friction = 0.5
        self.bodyShape.data = self
        self.bodyShape.collision_type = 1
        self.maxspeedx = 400
        self.maxspeedy = 800
        self.jump = 500
        self.jumpCooldown = 0
        self.fireCooldown = 0
        self.gun = 'grenade'
        self.health = 100
        self.maxHealth = 100
        self.damageTimer = 15
        self.isCrouching = False
        self.reward = 0
        self.space.add(self.body, self.bodyShape)

    def draw(self, surface, isBlittingText):
        self.vertices = [to_pygame(self.body.local_to_world(v), self.env.camerapos) for v in self.bodyShape.get_vertices()]
        self.PYGpoly = pygame.draw.polygon(surface, self.color, self.vertices)
        if isBlittingText:
            text(str(self.health), surface, 10, to_pygame(self.body.position + (0, -20), self.env.camerapos), (255, 255, 255), (0, 0, 0))
        #pygame.draw.circle(surface, (255, 255, 255), self.body.position, 6)

    def isGettingDamaged(self):
        for e in self.env.explosions:
            if e.isWithinRange(self.body.position):
                return True, e.player
        return False, None

    def update(self, action):
        self.reward = 0
        self.damageTimer -= 1
        self.body.angle = 0
        self.bodyShape.friction = 1
        if self.onGround and self.jumpCooldown <= 0:
            self.canJump = True
        else:
            self.canJump = False

        self.jumpCooldown -= 1
        self.fireCooldown -= 1

        if self.body.velocity[1] > 2:
            self.body.velocity += (0, 15)

        if action[0] == 0:
            if self.canJump:
                self.body.velocity += (0, -self.jump)
                self.jumpCooldown = 80
        if action[0] == 1:
            if self.onGround:
                self.body.velocity = [self.body.velocity[0]*.75, self.body.velocity[1]]
            else:
                self.body.velocity = [self.body.velocity[0]*.95, self.body.velocity[1]]
            self.isCrouching = True
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

        if action[1] == 1 and self.fireCooldown < 0 and len(self.env.bullets) < 20:
            self.fire(action[2], action[3])

        if self.body.velocity[1] > 10:
            self.body.apply_force_at_world_point((0, 3000), self.body.position)

        getDamaged = self.isGettingDamaged()
        if getDamaged[0] and self.damageTimer < 0:
            self.reward -= self.playerDamageDict[self == getDamaged[1]]
            self.health -= self.playerDamageDict[self == getDamaged[1]]
            self.damageTimer = 10

        return self.reward

    def fire(self, angle, speed):
        if self.gun == "grenade":
            Grenade(150+speed, angle, self.body.position, self, self.env.space)

    def reset(self):
        self.body.angle = 0
        self.bodyShape.data = self
        self.jumpCooldown = 0
        self.fireCooldown = 0
        self.health = 100
        self.isCrouching = False



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
        Explosion(80, self.body.position, 10, self.player, self.env)
        try:
            self.player.env.bullets.remove(self)
        except ValueError:
            pass
        self.env.delete(self)

class Explosion:
    def __init__(self, rad, pos, span, player, env=None):
        self.pos = pos
        self.rad = rad
        self.lifeCycle = span
        self.env = env
        self.player = player
        self.env.explosions.append(self)
        for body in self.env.getAllBodies():
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
    winLoseRew = 10
    enemyDamageRew = 5
    selfDamagePun = 2
    genRewBias = -3
    winLoseRewBias = -2

    space = pym.Space()
    space.gravity = (0, 700)
    space.iterations = 30

    clock = pygame.time.Clock()
    frame = 0
    attempt = 1
    attemptFrame = 0

    screen = pygame.display.set_mode((1000, 600))
    pygame.display.set_caption("")

    maxTrainingSteps = 500
    trainingSteps = 0

    currentModelID = 0

    textBlitting = False

    modelAdvsCurrent = None
    modelAdvsList = []
    modelAdvsMaxLen = 3
    modelAdvsChooseFreq = 1

    bullets = []
    explosions = []
    guns = ["grenade"]

    plt.ion()
    attemptRewards = []
    smoothedAttemptRewards = []
    fig, ax = plt.subplots()
    scatPlot = ax.scatter(range(1, len(attemptRewards) + 1), attemptRewards, s=2)
    regPlot, = ax.plot(range(1, len(smoothedAttemptRewards) + 1), smoothedAttemptRewards, color=(1, 0, 0))
    rewardThisAttempt = 0
    smoothing = 200

    def __init__(self, isRendering, hasHumanPlayer, advsModel, printsBasicdebug):
        self.printsBasicDebug = printsBasicdebug
        self.advsModel = advsModel
        self.isRendering = isRendering
        self.hasHumanPlayer = hasHumanPlayer
        self.PlayerA = Player(self.space, self, (200, 0, 0), pos=(200, 430))
        self.PlayerB = Player(self.space, self, (0, 0, 200), pos=(800, 430))
        self.PlayerA.enemy = self.PlayerB
        self.PlayerB.enemy = self.PlayerA
        self.camerapos = [0, 100]
        self.action_space = spaces.MultiDiscrete([4, 2, 360, 301]) #(button, isFiring, firingAngle)
        self.observation_space = spaces.Dict(spaces=({"PlayerPosVel": spaces.Box(low=-npy.inf, high=npy.inf, shape=(4,), dtype=npy.int32),
                                               "EnemyPosVel": spaces.Box(low=-npy.inf, high=npy.inf, shape=(4,), dtype=npy.int32),
                                               "BulletsPosVel": spaces.Box(low=-npy.inf, high=npy.inf, shape=(80,), dtype=npy.int32)}))
                                               #((playerPos, playerVel), (enemyPos, enemyVel), ((bulletPos, bulletVel)...))

        self.selectedPlayer = self.PlayerA

        self.ground = [Rect((500, 500), (1000, 100), self),
                       Rect((0, 150), (100, 800), self),
                       Rect((1000, 150), (100, 800), self),
                       Rect((500, 350), (600, 24), self),
                       Rect((500, 233), (24, 150), self),
                       Rect((100, 254), (200, 24), self),
                       Rect((900, 254), (200, 24), self),
                       Rect((500, 146), (200, 24), self),
                       Rect((810, 0), (150, 24), self),
                       Rect((190, 0), (150, 24), self),
                       Rect((500, -150), (1000, 100), self)]

        if not self.isRendering:
            self.screen = pygame.display.set_mode((200, 200))

        self.space.on_collision(
            collision_type_a=1,
            collision_type_b=2,
            pre_solve=ifPlayerOnGround,
        )

        self.space.on_collision(
            collision_type_a=1,
            collision_type_b=3,
            pre_solve=onBulletTouchEnemy,
        )

    def _get_obs(self):
        playerArr = npy.array([self.PlayerA.body.position[0], self.PlayerA.body.position[1], self.PlayerA.body.velocity[0], self.PlayerA.body.velocity[1]], dtype=npy.int32)
        enemyArr = npy.array([self.PlayerB.body.position[0], self.PlayerB.body.position[1], self.PlayerB.body.velocity[0], self.PlayerB.body.velocity[1]], dtype=npy.int32)
        bulletsArr = npy.array([[b.body.position[0], b.body.position[1], b.body.velocity[0], b.body.velocity[1]] for b in self.bullets] + [[0, 0, 0, 0]]*(20-len(self.bullets)), dtype=npy.int32).flatten()
        return {"PlayerPosVel":playerArr, "EnemyPosVel":enemyArr, "BulletsPosVel":bulletsArr}

    def reset(self, seed=None, options=None):
        self.PlayerA.reset()
        self.PlayerA.body.position = (r.randint(200, 800), 430)
        self.PlayerB.reset()
        self.PlayerB.body.position = (r.randint(200, 800), 430)
        for b in self.bullets:
            try:
                self.delete(b)
            except TypeError:
                pass
        self.bullets = []
        self.explosions = []
        self.trainingSteps = 0
        if self.printsBasicDebug:
            self.attempt += 1
            self.attemptFrame = 0
        if self.attempt % self.modelAdvsChooseFreq == 0:
            self.chooseModelAdvs()
        self.updatePlt(self.rewardThisAttempt)
        self.rewardThisAttempt = 0
        return self._get_obs(), {}

    def step(self, action):
        reward = 0
        self.trainingSteps += 1
        self.frame += 1
        done = False

        self.PlayerA.onGround = False
        self.PlayerB.onGround = False

        if isNotPaused:
            self.frame += 1
            self.space.step(1 / 60)
        s = t.time()

        screen.fill((0, 0, 0))

        if not (self.modelAdvsCurrent == None):
            modelAdvsAction, _ = self.modelAdvsCurrent.predict(self._get_obs(), deterministic=False)
            reward -= self.PlayerB.update(modelAdvsAction)
        reward += self.PlayerA.update(action)
        reward += self.genRewBias/self.maxTrainingSteps

        if self.PlayerA.health <= 0:
            reward -= self.winLoseRew
            reward += self.winLoseRewBias
            done = True
        if self.PlayerB.health <= 0:
            reward += self.winLoseRew
            reward -= self.winLoseRewBias
            done = True

        for e in enemies:
            e.update()

        #self.camerapos[0] -= ((self.selectedPlayer.body.position[0]+(((pygame.mouse.get_pos())[0] - 500)/2)/2) + (self.camerapos[0] - 500))/10
        #self.camerapos[1] -= ((self.selectedPlayer.body.position[1]+(((pygame.mouse.get_pos())[1] - 300)/2)/2) + (self.camerapos[1] - 300))/10

        if self.trainingSteps >= self.maxTrainingSteps:
            done = True

        self.rewardThisAttempt += reward

        if self.isRendering:
            self.render()

        for ev in pygame.event.get():
            if ev.type == pygame.KEYDOWN:
                if ev.key == pygame.K_p:
                    pdb.set_trace()
            elif ev.type == pygame.QUIT:
                pygame.quit()

        if self.printsBasicDebug:
            if not(self.modelAdvsCurrent == None):
                print(f'PA Act: {action}, PB Act: {modelAdvsAction}, frame: {self.frame}, ModelID: {self.currentModelID}')
            else: print(f'PA Act: {action}, models: {self.modelAdvsList}, frame: {self.frame}, ModelID: {self.currentModelID}')

        return self._get_obs(), reward, done, False, {}

    def render(self):
        for exp in self.explosions:
            exp.draw(screen)
        self.PlayerA.draw(screen, self.textBlitting)
        self.PlayerB.draw(screen, self.textBlitting)
        for r in self.ground:
            r.draw(screen)
        for b in self.bullets:
            b.update(screen)
        try:
            pygame.display.flip()
        except UnicodeDecodeError:
            pass

    def chooseModelAdvs(self):
        try:
            self.modelAdvsCurrent = r.choice(self.modelAdvsList)
        except IndexError:
            return None

    def addModeltoList(self, model):
        self.modelAdvsList.append(model)
        if len(self.modelAdvsList) > self.modelAdvsMaxLen:
            self.modelAdvsList.pop(0)

    def updatePlt(self, newItem):
        self.attemptRewards.append(int(newItem))
        if len(self.attemptRewards) >= 2000:
            self.attemptRewards.pop(0)
        smoothInds = [i for i in range(-self.smoothing, self.smoothing + 1)]
        avg = 0
        for ind in range(0, len(self.attemptRewards)):
            numsToBeAvgd = []
            for sInd in smoothInds:
                if ((ind + sInd) >= 0) and ((sInd + ind) <= (len(self.attemptRewards) - 1)):
                    numsToBeAvgd.append(self.attemptRewards[sInd + ind])
            if len(numsToBeAvgd) == 0:
                numsToBeAvgd = [self.attemptRewards[ind]]
            avg = sum(numsToBeAvgd) / len(numsToBeAvgd)
            self.smoothedAttemptRewards.append(avg)
        self.regPlot.set_data(range(1, len(self.smoothedAttemptRewards) + 1), self.smoothedAttemptRewards)
        self.scatPlot.set_offsets(npy.c_[npy.array(range(1, len(self.attemptRewards) + 1)), npy.array(self.attemptRewards)])
        self.ax.update_datalim(self.scatPlot.get_datalim(self.ax.transData))
        self.ax.autoscale_view()
        self.fig.canvas.draw()
        self.fig.canvas.flush_events()
        plt.pause(0.001)
        self.smoothedAttemptRewards = []

    def getAllBodies(self):
        return self.space.bodies

    def delete(self, grenade):
        try:
            self.space.remove(grenade.body, grenade.bodyShape)
        except AssertionError:
            pass

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
#env = GunEnv(True, True)


'''
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
    env.step(npy.array([B, isFiring, angle, 300]))
    print([B, isFiring])
    env.render()
    for ev in pygame.event.get():
        if ev.type == pygame.QUIT:
            running = False'
'''

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
