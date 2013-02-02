import pygame
import random
import math

from agents import Agent
from particle import Particles
from ui import Textbox,PopupText
from aicontroller import AIController
from tiles import FallingTiles
import interactions

class Laser(Agent):
    def init(self):
        self.end = [0,0]
        self.timeout = 30
    def update(self,*args):
        self.timeout-=1
        if self.timeout<=0:
            self.kill = 1
            self.parent.laser = None
    def draw(self,engine,offset):
        for i in range(3):
            p1 = [self.pos[0]-offset[0],self.pos[1]-offset[1]+random.randint(-2,2)-5]
            p2 = [self.end[0]-offset[0],self.end[1]-offset[1]+random.randint(-5,5)]
            pygame.draw.line(engine.surface,[0,random.randint(40,140),0],p1,p2,2)
            
class PushLaser(Agent):
    def init(self):
        self.end = [0,0]
        self.timeout = 30
    def update(self,*args):
        self.timeout-=1
        if self.timeout<=0:
            self.kill = 1
            self.parent.laser = None
    def draw(self,engine,offset):
        for i in range(1):
            p1 = [self.pos[0]-offset[0],self.pos[1]-offset[1]+random.randint(-2,2)-5]
            p2 = [self.end[0]-offset[0],self.end[1]-offset[1]+random.randint(-5,5)]
            pygame.draw.line(engine.surface,[0,0,random.randint(140,240)],p1,p2,5)
            
class WaterDrop(Agent):
    def update(self,*args):
        self.pos[1]+=4
        col = self.world.collide_point(self,[int(x) for x in self.pos],"move")
        if col==self.parent:
            return
        if col:
            self.kill = 1
            self.parent.water = None
        if hasattr(col,"vines"):
            if col.vines=="horiz":
                #TODO: convert vine into corner and grow vertical
                return
            x=col.pos[0]//32
            y=col.pos[1]//32-1
            n = 3
            while y>=0 and n:
                n-=1
                ncol = None
                for p in [(x*32,y*32),(x*32+31,y*32),(x*32+31,y*32+31),(x*32,y*32+31)]:
                    ncol = self.world.collide_point(self,p,"move")
                    if ncol and ncol.col:
                        break
                if ncol and ncol.col:
                    break
                ncol = col.layer.tiles[y][x]
                ncol.pos = [x*32,y*32]
                ncol.index = col.index
                ncol.vines = col.vines
                ncol.col = col.col
                ncol.set_surface()
                y-=1
            col.layer.cache_surface = None
    def draw(self,engine,offset):
        p = [int(self.pos[0]-offset[0]),int(self.pos[1]-offset[1])]
        pygame.draw.circle(engine.surface,[0,0,100],p,10)
        
class HorizWaterDrop(Agent):
    def update(self,*args):
        self.pos[1]+=4
        col = self.world.collide_point(self,[int(x) for x in self.pos],"move")
        if col==self.parent:
            return
        if col:
            self.kill = 1
            self.parent.water = None
        if hasattr(col,"vines") and col.vines=="horiz":
            x=col.pos[0]//32
            y=col.pos[1]//32
            left = x-1
            right = x+1
            lefttile = self.world.collide_point(self,[left*32,y*32],"move")
            righttile = self.world.collide_point(self,[right*32,y*32],"move")
            if lefttile and lefttile.col:
                dir=1
            elif righttile and righttile.col:
                dir=-1
            else:
                return
            n = 3
            while x>=0 and x<len(col.layer.tiles[y]) and n:
                x+=dir
                n-=1
                ncol = self.world.collide_point(self,[x*32+16,y*32+16],"move")
                if ncol and ncol.col:
                    break
                ncol = col.layer.tiles[y][x]
                ncol.pos = [x*32,y*32]
                ncol.index = col.index
                ncol.vines = col.vines
                ncol.col = col.col
                ncol.set_surface()
            col.layer.cache_surface = None
    def draw(self,engine,offset):
        p = [int(self.pos[0]-offset[0]),int(self.pos[1]-offset[1])]
        pygame.draw.circle(engine.surface,[0,100,0],p,10)

class Player(Agent):
    def init(self):
        self.hotspot = [16,32]
        self.facing = [-1,0]
        self.next_frame = 10
        self.animdelay = 6
        self.frame = 0
        self.anim = None
        self.animating = False
        self.horiz_accel = 0.2
        self.a = [0,0]
        self.vector = [0,0]
        self.laser = None
        self.water = None
        
        self.jumptime = 0
        
        self.particles = Particles()
        
        self.last_hit = None
        
        self.moved = False
        self.following = None
        self.follow_path = ""
        
        self.last_random_point = None
        self.next_random_point = 0
        
        self.menu = None
        self.texter = None
        
        self.aicontroller = AIController(self)
        self.interactable = interactions.CharacterInteractable(self)
        self.quests = []
        
        self.topics = set([])
        
        self.powers = ["shoot","grow","spread","push"]
        self.col = "full"
    def power(self,name):
        if name in self.powers:
            getattr(self,"power_"+name)()
    def start_death(self):
        self.world.remove(self)
        nt = FallingTiles()
        nt.pos = self.pos
        nt.graphic = self.surface
        nt.surface = self.surface
        nt.on_kill = self.on_kill
        nt.v = [0,-5]
        self.world.add(nt)
    def on_kill(self):
        """What to do when deleted from world"""
        self.world.do_restart = True
    def click(self,world,controller):
        if self.name=="erik":
            self.mymenu()
        else:
            self.action()
    def get_map(self):
        return self.world.maps[self.mapname]
    def get_path(self,pathname,get_astar=False):
        if pathname==True:
            return
        map = self.get_map()
        if pathname not in map.paths:
            return
        path = map.paths[pathname][:]
        if get_astar:
            path = self.update_path(path)
        return path
    def update_path(self,path):
        print "update path",path
        if not path:
            return None
        map = self.get_map()
        map.remove_entity(self)
        path2 = []
        path2.extend(map.get_path(self.pos,path[0]))
        if not path2:
            return self.update_path(path[1:])
        for i,next in enumerate(path[1:]):
            if path2[-1]==next:
                continue
            np = map.get_path(path2[-1],next)
            if np:
                for p in np:
                    if p!=path2[-1]:
                        path2.append(p)
            else:
                rest = path[i+1:]
                if not rest:
                    return None
                print i
                print path
                if i>0:
                    path = path2+path[i+1:]
                else:
                    path = path[i+1:]
                print path
                return self.update_path(path)
        map.add_entity(self)
        return path2
    def assign_ai(self,active=True):
        self.aicontroller.active = active
    def ai(self):
        if self.aicontroller.active:
            self.aicontroller.control()
    def load(self,spritesheet):
        super(Player,self).load(spritesheet)
        self.anims = {}
        order = ["right"]
        for y in range(1):
            frames = []
            for x in range(4):
                frames.append(self.graphics.subsurface([[x*32,y*48],[32,48]]))
            self.anims[order[y]] = frames
        self.anims["left"] = [pygame.transform.flip(x,1,0) for x in self.anims["right"]]
    def draw(self,engine,offset=[0,0]):
        #elipserect = [[0,0],[20,12]]
        #elipse = pygame.Surface([20,12]).convert_alpha()
        #elipse.fill([0,0,0,0])
        #pygame.draw.ellipse(elipse,[0,0,0,50],elipserect)
        self.particles.draw(engine,offset)
        #engine.surface.blit(elipse,[self.pos[0]-offset[0]-10,self.pos[1]-offset[1]])
        p = self.pos[:]
        super(Player,self).draw(engine,offset)
        self.pos = p
        x,y = (self.pos[0])//32*32-offset[0],(self.pos[1])//32*32-offset[1]
        w,h = 32,32
        #pygame.draw.rect(engine.surface,[255,0,255],pygame.Rect([[x,y],[w,h]]))
        for p in self.aicontroller.following_points:
            pygame.draw.rect(engine.surface,[255,0,255],[[p[0]-offset[0],p[1]-offset[1]],[2,2]])
        #engine.surface.blit(engine.font.render(self.aicontroller.state,1,[255,0,0]),[self.pos[0]-offset[0],self.pos[1]-offset[1]])
    def walk(self):
        self.map.remove_entity(self)
        
        self.moved = False
        col1=col2=None
        
        #calculate inside collisions
        col0 = self.world.collide(self)
        
        vector = self.vector[:]
        if self.vector[0]:
            self.pos[0]+=self.vector[0]
            col1 = self.world.collide(self,"move")
            if col1 and hasattr(col1,"col") and col1.col!="trigger" and not col0:
                if self.vector[0]>0:
                    self.pos[0]=col1.rect().left-16
                else:
                    self.pos[0]=col1.rect().right+16-1
                self.vector[0] = 0
            else:
                self.facing = [self.vector[0]/abs(self.vector[0]),0]
                self.moved = True
        if self.vector[1]:
            self.pos[1]+=self.vector[1]
            col2 = self.world.collide(self,"move")
            if col2 and hasattr(col2,"col") and col2.col!="trigger" and not col0:
                if self.vector[1]>0:
                    self.pos[1]=col2.rect().top-16
                else:
                    self.pos[1]=col2.rect().bottom+48
                    self.jumptime = -1
                self.vector[1]=0
            else:
                pass
                #self.moved = True
        trigger = self.world.collide(self,"trigger")
                
        
        hit_any = None
                        
        if hit_any:
            self.last_hit = hit_any
        else:
            self.last_hit = None
        
        if self.moved:
            self.animating = True
            self.particles.active = True
            self.particles.vector = [-vector[0],-vector[1]]
            
        self.map.add_entity(self)
        
        for col in col1,col2,trigger:
            if col:
                hit_any = col
                if hasattr(col,"col") and hasattr(col,"spikes"):
                    self.start_death()
                if isinstance(col,dict):
                    if "warptarget" in col: #and (col["direction"]=="left" and vector[0]<0 or col["direction"]=="right" and vector[0]>0 or col["direction"]=="up" and vector[1]<0 or col["direction"]=="down" and vector[1]>0 or col["direction"]=="none"):
                        print self.mapname,col
                        print self.world.events
                        self.world.events.append(
                        {"func":"change_map",
                        "args":(self,col["map"],col["warptarget"],"none")
                        })
                        break
    def say(self,text,actor=None,subjects=[]):
        if self.name != "erik":
            return
        for s in subjects:
            s.speaking = True
        if not actor:
            actor = self
        self = actor
        self.texter = Textbox()
        self.texter.subjects = subjects
        self.texter.to_say = text
        self.world.add(self.texter)
        topics = text.split("*")
        in_topic = False
        for i,t in enumerate(topics):
            if in_topic:
                self.topics.add(t)
            in_topic = not in_topic
            print self.topics
        print self.texter,self.texter.to_say,self.texter.said,self.texter.pos
    def say_many(self,lines,actor=None,subjects=[]):
        self = actor
        self.say(lines[0],actor,subjects)
        if lines[1:]:
            self.texter.do_next = (self.say_many,(lines[1:],actor,subjects))
    def frobme(self,actor):
        self.interactable.frobme(actor)
    def mymenu(self):
        if not self.menu:
            return
        options = []
        options.append( ("quit",self.world.quit,()) )
        self.menu.setup(options,label="Menu")
    def show_items(self,actor,item):
        if not self.menu:
            returrn
        options = []
        for i in self.items:
            options.append( (i.name,self.examine_item,(self,i)) )
        self.menu.setup(options,label="Items")
    def examine_item(self,actor,item):
        self.say(item.description)
    def follow(self,actor):
        self.following = actor
        #self.world.camera_focus = self
    def unfollow(self,actor):
        self.following = None
        self.following_points = []
        #self.world.camera_focus = actor
    def action(self):
        """Interact with object in front of us"""
        p = self.pos[:]
        for s in range(3):
            p[0]+=self.facing[0]*8
            p[1]+=self.facing[1]*8
            col = self.world.collide_point(self,p,"frobme")
            if col:
                print col,dir(col)
                if hasattr(col,"frobme"):
                    col.frobme(self)
                return
    def idle(self):
        self.animating = False
        self.particles.active = False
        self.a = [0,0]
    def left(self):
        if self.laser:
            return
        self.facing = [-1,0]
        self.a[0] = -self.horiz_accel
    def right(self):
        if self.laser:
            return
        self.facing = [1,0]
        self.a[0] = self.horiz_accel
    def set_anim(self,anim):
        self.anim = anim
        self.frame = 0
        self.next_frame = self.animdelay
        self.set_animation_frame()
    def set_animation_frame(self):
        anim = self.anims[self.anim]
        if self.frame>=len(anim):
            self.frame = 0
        self.surface = anim[self.frame]
    def on_ground(self):
        return self.world.collide_point(self,[int(self.pos[0]),int(self.rect().bottom+5)],"move")
    def on_ceiling(self):
        return self.world.collide_point(self,[int(self.pos[0]),int(self.rect().top-5)],"move")
    def jump(self):
        if self.on_ground() and self.jumptime==0:
            self.jumptime = 15
            self.vector[1]=-10
        elif self.jumptime==0:
            self.jumptime = -1
            if self.vector[1]<0:
                self.vector[1]=0
        if self.jumptime>0:
            self.jumptime-=1
            if self.jumptime==0:
                self.jumptime = -1
    def reset_jump(self):
        self.jumptime = 0
        if self.vector[1]<0:
            self.vector[1]=0
    def physics(self):
        mx = 5
        my = 10
        damp = 1
        if self.a[0]!=0:
            self.vector[0]+=self.a[0]
            if self.vector[0]<-mx:
                self.vector[0]=-mx
            if self.vector[0]>mx:
                self.vector[0]=mx
        else:
            if self.vector[0]>0:
                self.vector[0]-=damp
                if self.vector[0]<0:
                    self.vector[0]=0
            if self.vector[0]<0:
                self.vector[0]+=damp
                if self.vector[0]>0:
                    self.vector[0]=0
        if self.a[1]!=0:
            self.vector[1]+=self.a[1]
            if self.vector[1]<-my:
                self.vector[1]=-my
            if self.vector[1]>my:
                self.vector[1]=my
    def update(self,world):
        self.a[1]=0.3
            
        self.physics()
            
        if self.vector[0] or self.vector[1]:
            self.walk()
            
        if self.facing[0]<0:
            anim = "left"
        elif self.facing[0]>0:
            anim = "right"
        else:
            anim = self.anim
        if anim!=self.anim:
            self.set_anim(anim)
        if self.animating:
            self.next_frame -= 1
        if self.next_frame<=0:
            self.next_frame = self.animdelay
            self.frame += 1
            self.set_animation_frame()
        
        self.particles.pos = self.pos[:]
        self.particles.update(world)
        
        
    def collide(self,agent,flags=None):
        return self.collide_point(agent.pos,flags)
    def collide_point(self,p,flags=None):
        left,top,right,bottom = self.pos[0]-16+1,self.pos[1]-42+1,self.pos[0]+16-1,self.pos[1]+16-1
        if p[0]>=left and p[0]<=right and p[1]>=top and p[1]<=bottom:
            return self
    def rect(self):
        left,top,right,bottom = self.pos[0]-16+1,self.pos[1]-42+1,self.pos[0]+16-1,self.pos[1]+16-1
        return pygame.Rect([[left,top],[right-left,bottom-top]])
        
        

    def power_shoot(self):
        if self.laser:
            return
        l = Laser()
        l.parent = self
        self.laser = l
        l.pos = [int(self.pos[0]+3*self.facing[0]),int(self.pos[1])]
        l.end = [int(l.pos[0]//32*32+16),int(l.pos[1]//32*32+16)]
        while 1:
            l.end[0]+=int(self.facing[0]*32)
            ob = self.world.collide_point(self,l.end,"move")
            #Maybe break here, maybe keep going
            if ob and hasattr(ob,"col"):
                if ob.col=="trigger":
                    continue
                if hasattr(ob,"hit"):
                    ob.hit(self,l)
                break
        self.world.add(l)

    def power_push(self):
        if self.laser:
            return
        l = PushLaser()
        l.parent = self
        self.laser = l
        l.pos = [int(self.pos[0]+3*self.facing[0]),int(self.pos[1])]
        l.end = [int(l.pos[0]//32*32+16),int(l.pos[1]//32*32+16)]
        while 1:
            l.end[0]+=int(self.facing[0]*32)
            ob = self.world.collide_point(self,l.end,"move")
            #Maybe break here, maybe keep going
            if ob and hasattr(ob,"col"):
                if ob.col=="trigger":
                    continue
                if hasattr(ob,"push"):
                    ob.push(self,l,self.facing[0])
                break
        self.world.add(l)

    def power_grow(self):
        if self.water:
            return
        self.water = WaterDrop()
        self.water.parent = self
        self.water.mapname = self.mapname
        self.water.pos = [self.pos[0]+self.facing[0]*32,self.pos[1]]
        self.world.add(self.water)
        
    def power_spread(self):
        if self.water:
            return
        self.water = HorizWaterDrop()
        self.water.parent = self
        self.water.mapname = self.mapname
        self.water.pos = [self.pos[0]+self.facing[0]*32,self.pos[1]]
        self.world.add(self.water)
        