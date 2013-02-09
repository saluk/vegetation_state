import os,random,math

import pygame

from world import World
from tiles import TileMap
from characters import Player

from ui import Radial
from agents import Text,Agent
import quest

import json

songs = {"default":"Roger_Subirana_Mata_-_Nysfan"}

class GameWorld(World):
    def start(self):
        self.do_restart = False
        self.objects = []
        self.events = []
        
        self.maps = {}
        for map in ["room1","room2","room3","hubupgate","hubdowngate","hubleftgate","hubrightgate","hub","hubleftgate2"]:
            self.maps[map] = TileMap()
            self.maps[map].name = map
            self.maps[map].mapname = map
            self.add(self.maps[map])
            self.maps[map].load("dat/%s.tmx"%map)
        
        self.camera = self.offset
        
        self.scroll_speed = 5
        
        for mapkey in self.maps:
            if "playerspawn" in self.maps[mapkey].regions:
                spawn = self.maps[mapkey].regions["playerspawn"]
                self.player = self.add_character(mapname=mapkey,sprite="art/sprites/stickman.png",pos=[spawn.x+16,spawn.y+16],direction="right")
                self.player.name = "stickman"
                self.player.assign_ai(active=False)
                self.player.walk_speed = 1.5
                self.map = self.maps[mapkey]
                self.map_music()
            for o in self.maps[mapkey].npc_spawns:
                name = o["props"]["npc"]
                char = self.char_defs.get(name,{"name":name,"sprite":"flowergirl01"})
                pos = o["pos"][:]
                direction = random.choice(["up","down","left","right"])
                sprite = "art/sprites/"+char["sprite"]+".png"
                npc = self.add_character(mapname=mapkey,sprite=sprite,pos=pos,direction=direction)
                npc.name = name
                npc.paths = char.get("paths",{})
                npc.attractors = char.get("attractors",{})
                if "mood" in char:
                    npc.mood = char["mood"]
                if "items" in char:
                    npc.items.clear()
                    for i in char["items"]:
                        npc.items.add(name=i)
                if "quests" in char:
                    for q in char["quests"]:
                        quest_func = getattr(quest,q)()
                        quest_func.init(npc)
                        npc.quests.append(quest_func)
            for i in range(1):
                spawn = self.maps[mapkey].regions.get("spawn",None)
                if not spawn:
                    continue
                pos = [random.randint(spawn.left,spawn.right),random.randint(spawn.top,spawn.bottom)]
                direction = random.choice(["up","down","left","right"])
                art = [x for x in os.listdir("art/sprites") if x.endswith(".png")]
                sprite = "art/sprites/"+random.choice(art)
                npc = self.add_character(mapname=mapkey,sprite=sprite,pos=pos,direction=direction)
        
        self.camera_focus = self.player
        
        self.player.menu = Radial()
        self.player.menu.layer = 10
        self.player.menu.pos = self.player.pos
        self.add(self.player.menu)
        self.player.say_many(["VEGETATION STATE: Demo","<- -> to move","z - jump; x - shoot; v - push; c - vertical growth; a - horizontal growth","r - restart"],self.player)
    def add_character(self,mapname,sprite,pos,direction):
        p = Player()
        p.mapname = mapname
        p.map = self.maps[mapname]
        p.pos = pos
        p.map.add_entity(p)
        p.load(sprite)
        getattr(p,direction)()
        p.idle()
        self.add(p)
        return p
    def process_events(self):
        for e in self.events:
            getattr(self,e["func"])(*e.get("args",[]),**e.get("kwargs",{}))
        self.events = []
    def change_map(self,character,map,target,direction=None):
        if map not in self.maps:
            print "NO MAP"
            return
        if target not in self.maps[map].warps and target not in self.maps[map].destinations:
            print "NO 'DESTINATION'"
            return
        character.following_points = []
        #~ if direction=="none":
            #~ target = self.maps[map].destinations[target]
        #~ else:
            #~ target = self.maps[map].warps[target]["rect"]
        #~ if direction=="left":
            #~ character.pos = [target.left-32,character.pos[1]]
            #~ print character,map,target
            #~ print "warp left"
        #~ elif direction=="right":
            #~ character.pos = [target.right+32,character.pos[1]]
            #~ print "warp right"
        #~ elif direction=="up":
            #~ character.pos = [character.pos[0],target.top-12]
            #~ print "warp up"
        #~ elif direction=="down":
            #~ character.pos = [character.pos[0],target.bottom]
            #~ print "warp down"
        #~ else:
            #~ character.pos = [target.left,target.top]
        target = self.maps[map].destinations[target]
        character.pos = [target.left,target.top]
        character.mapname = map
        character.map = self.maps[map]
        if character == self.camera_focus:
            self.map = self.maps[map]
            self.map_music()
    def map_music(self):
        song = songs.get(self.map.name,songs["default"])
        if song:
            song = "music/"+song+".ogg"
        print song
        self.engine.play_music(song)
    def get_objects(self,agent):
        return [o for o in self.objects if (not hasattr(o,"mapname") or o.mapname==agent.mapname)]
    def get_update_mode(self):
        if self.player.menu.visible and self.player.menu.pause:
            return "menu"
        elif self.player.texter and self.player.texter.visible:
            return "textbox"
        return "normal"
    def update(self):
        """self.sprites starts empty, any object added to the list during
        update() is going to be rendered"""
        update_mode = self.get_update_mode()
        self.sprites = []
        
        self.ai()
        for m in self.maps.values():
            m.update(self)
        for o in self.objects:
            o.update(self)
        [o.on_kill() for o in self.objects if o.kill]
        self.objects = [o for o in self.objects if not o.kill]
        for o in self.get_objects(self.camera_focus):
            if o.visible:
                self.sprites.extend(o.get_sprites())
        self.sprites.sort(key=lambda sprite:(sprite.layer,sprite.pos[1]))
        
        self.focus_camera()
        self.player.menu.pos = self.player.pos
        
        self.process_events()
        if self.do_restart:
            self.restart()
    def collide(self,agent,flags=None):
        for ob in self.get_objects(agent):
            if ob==agent:
                continue
            if not hasattr(ob,"collide"):
                continue
            col = ob.collide(agent,flags)
            if col:
                return col
    def collide_point(self,agent,p,flags=None):
        for ob in self.get_objects(agent):
            if ob==agent:
                continue
            if not hasattr(ob,"collide_point"):
                continue
            col = ob.collide_point(p,flags)
            if col:
                return col
    def restart(self):
        import game
        import world
        import tiles
        import characters
        reload(world)
        reload(tiles)
        reload(characters)
        reload(game)
        self.engine.world = game.make_world(self.engine)
    def input(self,controller):
        if controller.restart:
            return self.restart()
        self.player.idle()
        player_move = True
        if self.player.texter:
            if self.player.texter.finished and (controller.jump or controller.menu):
                self.player.texter.end(self)
                controller.reset_all()
                return
            player_move = False
        elif self.player.menu.visible:
            if controller.left:
                controller.left = False
                self.player.menu.rotate_left()
            if controller.right:
                controller.right = False
                self.player.menu.rotate_right()
            #~ if controller.action:
                #~ self.player.menu.action()
            if controller.menu:
                self.player.menu.visible = False
            player_move = False
        if player_move:
            if controller.shoot:
                self.player.power("shoot")
            if controller.grow:
                self.player.power("grow")
            if controller.grow2:
                self.player.power("spread")
            if controller.push:
                self.player.power("push")
            if controller.left:
                self.player.left()
                self.player.assign_ai(active=False)
            if controller.right:
                self.player.right()
                self.player.assign_ai(active=False)
            if controller.jump:
                self.player.jump()
            else:
                self.player.reset_jump()
            if controller.menu:
                controller.reset_all()
                self.player.mymenu()
                self.player.assign_ai(active=False)
        #~ if controller.mbdown:
            #~ x = controller.mpos[0]+self.offset[0]
            #~ y = controller.mpos[1]+self.offset[1]
            #~ for o in reversed(self.sprites):
                #~ r = o.rect()
                #~ if hasattr(o,"click") and x>=r.left and x<=r.right and y>=r.top and y<=r.bottom:
                    #~ o.click(self,controller)
                    #~ return
            #~ for o in reversed(self.objects):
                #~ r = o.rect()
                #~ if hasattr(o,"click") and x>=r.left and x<=r.right and y>=r.top and y<=r.bottom:
                    #~ o.click(self,controller)
                    #~ return
        if controller.quit:
            self.quit()
    def quit(self):
        self.engine.running = False
    def ai(self):
        for ob in self.objects:
            ob.ai()
    def focus_camera(self):
        if not self.camera_focus:
            return
        self.camera[:] = [self.camera_focus.pos[0]-(self.engine.iwidth//2),self.camera_focus.pos[1]-(self.engine.iheight//2)]
        if self.camera[0]<0:
            self.camera[0] = 0
        if self.camera[1]<0:
            self.camera[1] = 0
        if self.camera[0]>self.map.rect().right-self.engine.iwidth:
            self.camera[0]=self.map.rect().right-self.engine.iwidth
        if self.camera[1]>self.map.rect().bottom-self.engine.iheight:
            self.camera[1]=self.map.rect().bottom-self.engine.iheight
            
    def find_object(self,name):
        for o in self.objects:
            if hasattr(o,"name") and o.name==name:
                return o

def make_world(engine):
    """This makes the starting world"""
    w = GameWorld(engine)
    return w