import random

import pygame
from agents import Agent

class Particle(Agent):
    def init(self):
        self.vector = [0,0]
        self.timeout = 30
    def update(self,x):
        self.timeout -= 1
        if self.timeout<=0:
            self.kill = 1

class Particles(Agent):
    def init(self):
        #self.graphic = pygame.image.load("art/particles/sparkle.png").convert()
        #self.graphic = pygame.transform.scale(self.graphic,[10,10])
        self.graphic = pygame.Surface([1,1])
        self.graphic.fill([205,205,205])
        self.visible = set()
        self.invisible = set()
        self.next_particle = 1
        self.active = False
        self.vector = [1,0]
        self.init_particles()
    def init_particles(self,num_particles=150):
        for n in range(num_particles):
            self.invisible.add(Particle())
    def add_particle(self,pos=None,vector=[1,0],timeout=30):
        if self.invisible:
            p = self.invisible.pop()
        if not pos:
            pos = self.pos[:]
        p.pos = pos[:]
        p.vector = [(vector[0]+(random.random()-0.5)*0.8)*0.5,(vector[1]+(random.random()-0.5)*0.8)*0.5]
        p.timeout = timeout
        p.alpha = 255
        self.visible.add(p)
    def draw(self,engine,offset):
        for p in self.visible:
            pos = [p.pos[0]-offset[0],p.pos[1]-offset[1]]
            self.graphic.set_alpha(p.alpha)
            engine.surface.blit(self.graphic,pos)#,special_flags=pygame.BLEND_RGBA_ADD)
    def update(self,x):
        next = set()
        for p in self.visible:
            p.timeout-=1
            if p.timeout<=0:
                self.invisible.add(p)
                continue
            next.add(p)
            p.pos[0]+=p.vector[0]
            p.pos[1]+=p.vector[1]
            p.alpha -= 4
        self.visible = next
        if self.active:
            self.next_particle -= 1
            if self.next_particle<=0:
                self.add_particle(vector=self.vector)
                self.next_particle = 4

if __name__=="__main__":
    engine = Agent()
    engine.surface = pygame.display.set_mode([320,240])
    c = pygame.time.Clock()
    parts = Particles()
    parts.pos = [50,50]
    running = True
    while running:
        pygame.event.pump()
        for evt in pygame.event.get():
            if evt.type==pygame.QUIT:
                running = False
        engine.surface.fill([0,0,0])
        parts.update(1)
        parts.draw(engine,[0,0])
        pygame.display.update()
        c.tick(60)
        