#
# controller.py
# not well implemented for expansion
# but, provides a lot of nice base behavior:
# * alt-enter to toggle fullscreen
# * minimise pauses the engine (although the world still needs to check if the engine is paused)
# * un minimise unpauses the engine
# * can resize the window to change the display resolution
# * can quit the game

import pygame

class Controller:
    def __init__(self,engine):
        self.engine = engine
        self.mbdown = 0
        self.mpos = [0,0]
        self.joysticks = None
        self.joy = {}
        self.get_joysticks()
        self.reset_all()
    def get_joysticks(self):
        pygame.joystick.init()
        self.joysticks = []
        for i in range(pygame.joystick.get_count()):
            j = pygame.joystick.Joystick(i)
            j.init()
            self.joysticks.append(j)
    def reset_triggers(self):
        self.mbdown = 0
        self.action = 0
        self.menu = 0
        self.restart = 0
        self.quit = 0
    def reset_all(self):
        self.reset_triggers()
        self.left = 0
        self.right = 0
        self.up = 0
        self.down = 0
    def input(self):
        self.reset_triggers()
        engine = self.engine
        pygame.event.pump()
        for e in pygame.event.get():
            if e.type==pygame.ACTIVEEVENT:
                if e.gain==0 and (e.state==6 or e.state==2 or e.state==4):
                    self.engine.pause()
                    continue
                if e.gain==1 and (e.state==6 or e.state==2 or e.state==4):
                    self.engine.unpause()
                    continue
            if e.type==pygame.VIDEORESIZE:
                w,h = e.w,e.h
                engine.swidth = w
                engine.sheight = h
                engine.make_screen()
                continue
            if e.type == pygame.QUIT:
                self.engine.stop()
                continue
            if e.type==pygame.KEYDOWN and\
                e.key==pygame.K_RETURN and pygame.key.get_mods() & pygame.KMOD_ALT:
                engine.fullscreen = 1-engine.fullscreen
                engine.make_screen()
                continue
            if e.type==pygame.KEYDOWN and\
                e.key==pygame.K_F12:
                pygame.image.save(engine.window,"screen.jpg")
                continue
            self.handle_pygame_event(e)
        if engine.world:
            engine.world.input(self)
    def handle_pygame_event(self,e):
        """Ideally, build this out with state so that the world
        can make a query like controller.enter_was_pressed or key_held_for(3)"""
        if e.type==pygame.JOYAXISMOTION:
            if e.joy == 0:
                if e.axis==0:
                    self.left=self.right=0
                    if e.value<-.5:
                        self.left = 1
                    elif e.value>.5:
                        self.right = 1
                elif e.axis==1:
                    self.up=self.down=0
                    if e.value<-.5:
                        self.up = 1
                    elif e.value>.5:
                        self.down = 1
        if e.type == pygame.JOYBUTTONUP:
            if e.joy == 0:
                if e.button == 1:
                    self.action = 1
                if e.button == 2:
                    self.menu = 1
        elif e.type == pygame.JOYBUTTONDOWN:
            if e.joy == 0:
                if e.button == 1:
                    self.action = 0
                if e.button == 2:
                    self.menu = 0
        if e.type == pygame.MOUSEBUTTONDOWN:
            self.mbdown = 1
            self.mpos = int(e.pos[0]/self.engine.sfw),int(e.pos[1]/self.engine.sfh)
        if e.type == pygame.KEYDOWN:
            if e.key == pygame.K_LEFT:
                self.left = 1
            elif e.key == pygame.K_RIGHT:
                self.right = 1
            if e.key == pygame.K_UP:
                self.up = 1
            elif e.key == pygame.K_DOWN:
                self.down = 1
            if e.key == pygame.K_z:
                self.action = 1
            if e.key == pygame.K_x:
                self.menu = 1
            if e.key == pygame.K_r:
                self.restart = 1
            if e.key == pygame.K_F6:
                self.quit = 1
        elif e.type == pygame.KEYUP:
            if e.key == pygame.K_LEFT:
                self.left = 0
            elif e.key == pygame.K_RIGHT:
                self.right = 0
            if e.key == pygame.K_UP:
                self.up = 0
            elif e.key == pygame.K_DOWN:
                self.down = 0
            elif e.key == pygame.K_x:
                self.menu = 0
            if e.key == pygame.K_r:
                self.restart = 0
            if e.key == pygame.K_F6:
                self.quit = 0