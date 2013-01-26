import random

class AIController(object):
    def __init__(self,agent):
        self.agent = agent
        self.lastpos = agent.pos[:]
        self.np = 0
        self.point_every = 4
        self.active = True
        self.following_points = []
        self.last_moved = 0
        
        self.state = "choose"
        self.next_states = []
        self.wait_time = 0
    def control(self):
        if not self.active:
            return
        a = self.agent
        a.idle()
        if self.agent.speaking or self.agent.world.get_update_mode()=="menu":
            return
        if a.following:
            self.state = "follow"
        elif a.follow_path:
            self.state = "follow_path"
        getattr(self,"state_"+self.state,self.state_idle)()
        
        if a.moved:
            self.last_moved = 0
        else:
            self.last_moved += 1
    def state_idle(self):
        pass
    def state_choose(self):
        self.state = "idle"
        self.following_points = []
        if self.next_states:
            self.state = self.next_states.pop(0)
            return
        a = self.agent
        if getattr(a,"attractors",{}):
            print a.attractors
            chosen = a.attractors["default"]
            for o in a.map.frobers:
                print chosen["name"],o.name
                if o.name==chosen["name"]:
                    print "found object"
                    for d in [(-1,0),(1,0),(0,-1),(0,1)]:
                        p = [o.pos[0]+d[0]*32,o.pos[1]+d[1]*32]
                        points = [a.pos,p]
                        path = a.update_path(points)
                        if path:
                            self.following_points = path
                            self.state = "follow_path"
                            self.next_states = ["wait"]
                            self.wait_time = 30*10
                            break
                if self.following_points:
                    break
            if self.following_points:
                return
        if hasattr(a,"paths"):
            self.active_path = self.select_path(a,a.paths)
            print "chose path",self.active_path
            self.following_points = a.get_path(self.active_path,True)
            print "following_points",self.following_points
            self.state = "follow_path"
            self.next_states = ["wait"]
            self.wait_time = 30*10
            if not self.following_points:
                self.following_points = []
                self.state = "choose"
    def state_wait(self):
        self.wait_time -= 1
        if self.wait_time<=0:
            self.state = "choose"
    def select_path(self,a,paths):
        if "default" in paths:
            pathset = paths["default"]
            if pathset["selector"]=="random":
                return random.choice(pathset["paths"])
    def state_follow(self):
        if not self.agent.following:
            self.state = "choose"
            return
        self.follow(self.agent.following)
    def state_follow_path(self):
        self.follow_path()
        if not self.following_points:
            self.agent.action()
            self.state = "choose"
    def random_walk(self):
            a.next_random_point-=1
            if a.next_random_point<=0:
                a.last_random_point = [a.pos[0]+random.randint(-100,100),a.pos[1]+random.randint(-100,100)]
                a.next_random_point = random.randint(200,400)
            self.walk_toward(self.agent.last_random_point)
    def follow_path(self,get_astar=False):
        a = self.agent
        world = a.world
        pathname = a.follow_path
        map = world.maps[a.mapname]
        if not self.following_points:
            self.following_points = a.get_path(self.active_path,get_astar)
        else:
            p = self.following_points[0]
            if self.walk_toward(p):
                del self.following_points[0]
                if not self.following_points:
                    #path done?
                    a.follow_path = None
                    return
            #Not moving, recalculate path
            if self.last_moved>30:
                print "find path for",self.following_points
                path = a.update_path(self.following_points[1:])
                if path:
                    self.following_points = path
                self.last_moved = 0
    def follow(self,target):
        if not target:
            return
        a = self.agent
        fp=1
        max = 15
        d = 6
        p = [target.pos[0]//fp*fp,target.pos[1]//fp*fp]
        if (not self.following_points or p!=self.following_points[-1]) and target.mapname==a.mapname:
            self.np-=1
            if self.np<=0:
                self.following_points.append(p)
                self.np = self.point_every
        if len(self.following_points)<d and target.mapname==a.mapname:
            return
        if len(self.following_points)>max:
            self.following_points = self.following_points[-max:]
            
        #player map transition, keep going
        if not self.following_points and target.mapname!=a.mapname:
            a.forward()
            return
            
            
        p = self.following_points[0]
        if self.walk_toward(p):
            del self.following_points[0]
    def walk_toward(self,p):
        a = self.agent
        md = 2
        if abs(a.pos[0]-p[0])<=md and abs(a.pos[1]-p[1])<=md:
            return True
        #a.idle()
        if a.pos[1]-p[1]>md:
            a.up()
        elif a.pos[1]-p[1]<-md:
            a.down()
        if a.pos[0]-p[0]>md:
            a.left()
        elif a.pos[0]-p[0]<-md:
            a.right()