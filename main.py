import pygame
pygame.font.init()
import pymunk as pym
import pymunk.pygame_util
import time as t
import numpy as npy



space = pym.Space()
space.gravity = (0, 500)
space.iterations = 30

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
    def __init__(self):
        self.body = pym.Body(10, pym.moment_for_box(10, (25, 25)), body_type=pym.Body.DYNAMIC)
        self.body.position = (500, 300)
        self.body.angle = 0
        self.bodyShape = pym.Poly.create_box(self.body, (25, 25), 0.5)
        self.bodyShape.elasticity = 0.0
        self.bodyShape.friction = 0.5
        self.bodyShape.collision_type = 1
        self.maxspeedx = 400
        self.maxspeedy = 400
        self.jump = 400
        self.jumpCooldown = 0
        self.fireCooldown = 0
        self.gun = 'ball'
        self.isCrouching = False
        space.add(self.body, self.bodyShape)

    def draw(self, surface):
        self.vertices = [to_pygame(self.body.local_to_world(v)) for v in self.bodyShape.get_vertices()]
        self.PYGpoly = pygame.draw.polygon(surface, (0, 50, 150), self.vertices)
        #pygame.draw.circle(surface, (255, 255, 255), self.body.position, 6)

    def update(self, keys):
        self.body.angle = 0
        self.bodyShape.friction = 1
        if self.onGround and self.jumpCooldown <= 0:
            self.canJump = True
        else:
            self.canJump = False
        self.jumpCooldown -= 1
        self.fireCooldown -= 1

        if keys[pygame.K_UP] or keys[pygame.K_w]:
            if self.canJump:
                self.body.velocity += (0, -self.jump)
                self.jumpCooldown = 80
        if keys[pygame.K_DOWN] or keys[pygame.K_s]:
            self.bodyShape.friction = 10
            self.isCrouching = True
            print(self.isCrouching)
        else:
            self.isCrouching = False
        if keys[pygame.K_RIGHT] or keys[pygame.K_d]:
            self.bodyShape.friction = 0.2
            if self.body.velocity[0] < self.maxspeedx:
                if self.onGround:
                    self.body.apply_force_at_local_point((20000, 0))
                else:
                    self.body.apply_force_at_local_point((2000, 0))
        if keys[pygame.K_LEFT] or keys[pygame.K_a]:
            self.bodyShape.friction = 0.2
            if self.body.velocity[0] > -self.maxspeedx:
                if self.onGround:
                    self.body.apply_force_at_local_point((-20000, 0))
                else:
                    self.body.apply_force_at_local_point((-2000, 0))
        if keys[pygame.K_1]:
            self.gun = guns[0]
        if keys[pygame.K_2]:
            self.gun = guns[1]
            '''if keys[pygame.K_3]:
                self.gun = guns[2]
            if keys[pygame.K_4]:
                self.gun = guns[3]
            if keys[pygame.K_5]:
                self.gun = guns[4]
            if keys[pygame.K_6]:
                self.gun = guns[5]
            if keys[pygame.K_7]:
                self.gun = guns[6]
            if keys[pygame.K_8]:
                self.gun = guns[7]
            if keys[pygame.K_9]:
                self.gun = guns[8]'''

        if pygame.mouse.get_pressed()[0] and self.fireCooldown < 0:
            self.fire()

        if self.body.velocity[1] > 10:
            self.body.apply_force_at_world_point((0, 3000), self.body.position)

    def fire(self):
        mpos = pygame.mouse.get_pos()
        bodypos = to_pygame(self.body.position)
        angle = get_angle(mpos, bodypos)
        if self.gun == "ball":
            BallBullet(500, angle, self.body.position, self)
        elif self.gun == "grenade":
            Grenade(300, angle, self.body.position, self)

    def ifOnGround(self, arbiter, space, data):
        self.onGround = True
        return None

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
        space.add(self.body, self.bodyShape)

    def onTouchingEnemy(self, enemy):
        pass

    def update(self, surface):
        b.lifeCycle -= 1
        if self.lifeCycle < 0:
            bullets.remove(self)
            delete(self)
        pygame.draw.circle(screen, (0, 255, 255), to_pygame(self.body.position), 6)

class Grenade:
    def __init__(self, speed, angle, pos, player):
        bullets.append(self)
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
        player.fireCooldown = self.cooldown
        space.add(self.body, self.bodyShape)

    def update(self, screen):
        pygame.draw.circle(screen, (90, 90, 90), to_pygame(self.body.position), 6)
        self.lifeCycle -= 1
        if self.lifeCycle < 0:
            self.explode()

    def onTouchingEnemy(self, enemy):
        self.explode()

    def explode(self):
        Explosion(80, self.body.position, 10)
        bullets.remove(self)
        delete(self)

class Explosion:
    def __init__(self, rad, pos, span):
        self.pos = pos
        self.rad = rad
        self.lifeCycle = span
        explosions.append(self)
        for body in getAllBodies():
            if self.isWithinRange(body.position):
                dis = get_dist(self.pos, body.position)
                strength = -20000/body.mass
                body.apply_impulse_at_world_point((strength*dis[1]/dis[0], strength*dis[2]/dis[0]), body.position)

    def draw(self, surface):
        pygame.draw.circle(surface, (204, 102, 0), to_pygame(self.pos), self.rad)
        self.lifeCycle -= 1
        if self.lifeCycle < 0:
            explosions.remove(self)

    def isWithinRange(self, pos):
        if (pos[0] - self.pos[0])**2 + (pos[1] - self.pos[1])**2 <= self.rad**2:
            return True
        return False

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



class Rect:
    def __init__(self, pos, size):
        self.body = pym.Body(body_type=pym.Body.KINEMATIC)
        self.body.position = pos
        self.bodyShape = pym.Poly.create_box(self.body, size, 0.5)
        self.bodyShape.elasticity = 1
        self.bodyShape.friction = 1
        self.bodyShape.collision_type = 2
        space.add(self.body, self.bodyShape)

    def draw(self, surface):
        self.vertices = [to_pygame(self.body.local_to_world(v)) for v in self.bodyShape.get_vertices()]
        self.PYGpoly = pygame.draw.polygon(surface, (100, 100, 100), self.vertices)

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
    enemy = enemyShape.user_data

    if callable(bullet.onTouchingEnemy):
        bullet.onTouchingEnemy(enemy)

    if callable(enemy.onTouchingBullet):
        enemy.onTouchingBullet(bullet)

    return None

def to_pygame(pos):
    """ Convert Pymunk physics coordinates to Pygame coordinates. """
    if isinstance(pos, list):
        return [(v.x + camerapos[0], v.y + camerapos[1]) for v in pos]
    if isinstance(pos, tuple):  # Handle tuples
        return int(pos[0] + camerapos[0]), int(pos[1] + camerapos[1])
    return int(pos.x + camerapos[0]), int(pos.y + camerapos[1])  # Handle Pymunk Vec2d objects

def to_pymunk(pos):
    return (pos[0] - camerapos[0], pos[1] - camerapos[1])

def debug(message, value):
    print(str(message) + ": " + str(value))

def delete(self):
    try:
        space.remove(self.body, self.bodyShape)
    except AssertionError:
        pass

def getAllBodies():
    return space.bodies

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

running = True
isNotPaused = True
frame = 0

TriangleEnemy((500, 200))

p = Player()
'''ground = [Rect((500, 500), (1000, 100)),
          Rect((1300, 450), (1000, 150)),
          Rect((-300, 450), (1000, 150)),
          Rect([100, 300], [500, 25]),
          Rect([1300, 200], [700, 50]),
          Rect([1300, 400], [45, 200]),
          Rect((2000, 375), (500, 250)),
          Rect((1000, 75), (40, 250)),
          Rect((2000, 50), (200, 50)),
          Rect((-1300, 400), (1000, 75)),
          Rect((-1600, 300), (50, 200)),
          Rect((-1900, 100), (50, 350)),
          Rect((-2300, 400), (1000, 75)),]'''

ground = [
Rect((500, 500), (1000, 100)),
Rect((-50, 0), (100, 1100)),
Rect((1000, 0), (100, 1100)),
Rect((500, 350), (500, 30)),
]

space.on_collision(
    collision_type_a=1,
    collision_type_b=2,
    begin=None,
    pre_solve=p.ifOnGround,
    post_solve=None,
    separate=None,
    data=None
)

space.on_collision(
    collision_type_a=1,
    collision_type_b=3,
    begin=None,
    pre_solve=p.ifOnGround,
    post_solve=None,
    separate=None,
    data=None
)

space.on_collision(
    collision_type_a=3,
    collision_type_b=4,
    begin=None,
    pre_solve=onBulletTouchEnemy,
    post_solve=None,
    separate=None,
    data=None
)



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
