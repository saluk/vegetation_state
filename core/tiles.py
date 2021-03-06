import os,random

import pygame
from agents import Agent
from interactions import FrobberInteractable

import astar

try:
    import android
except:
    android = None
    
class FallingTiles(Agent):
    def init(self):
        self.angm = random.randint(-3,3)
        self.ang = 0
        self.a = [random.random()-0.5,1]
        self.v = [0,0]
    def update(self,*args):
        self.surface = pygame.transform.rotate(self.graphic,self.ang)
        self.ang+=self.a[0]*3
        self.v[0]+=self.a[0]*0.1
        self.v[1]+=self.a[1]*0.1
        self.pos[0]+=self.v[0]
        self.pos[1]+=self.v[1]
        if self.pos[0]<0 or self.pos[0]>self.world.map.rect().width or self.pos[1]<0 or self.pos[1]>self.world.map.rect().height:
            self.kill = 1

class Tile(Agent):
    def init(self):
        self.col = None    #full,top,bottom,left,right,trigger
        self.index = -1
        self.layer = None
        self.save = ["pos","col","index","vines","spikes","key","door","losepower"]
    def rect(self):
        return pygame.Rect([self.pos,[32,32]])
    def serialized(self):
        d = {}
        for s in self.save:
            if hasattr(self,s):
                d[s] = getattr(self,s)
        return d
    @staticmethod
    def unserialize(d,layer):
        t = Tile()
        t.layer = layer
        for s in t.save:
            if s in d:
                setattr(t,s,d[s])
        t.set_surface()
        return t
    def is_empty(self):
        return self.index==-1
    def set_surface(self):
        self.surface = self.layer.tileset_list[self.index]
        self.graphic = self.surface
    def draw(self,engine,offset):
        super(Tile,self).draw(engine,offset)
        if hasattr(self,"chest"):
            s = pygame.Surface([32,32])
            s.fill([255,255,255])
            s.set_alpha(50)
            engine.surface.blit(s,[self.pos[0]-offset[0],self.pos[1]-offset[1]])
    def collide_point(self,point,flags=None):
        if not self.col:
            return
        if self.col=="trigger" and flags!="trigger":
            return
        if self.col!="trigger" and flags=="trigger":
            return
        top = self.pos[1]
        left = self.pos[0]
        right = self.pos[0]+31
        bottom = self.pos[1]+31
        if self.col == "top":
            bottom-=16
        if self.col == "left":
            right-=16
        if self.col == "right":
            left+=16
        if self.col == "bottom":
            top+=16
        if point[0]>=left and point[0]<=right and point[1]>=top and point[1]<=bottom:
            return self
    def push(self,agent,laser,dirv):
        if hasattr(self,"vines"):
            x = int(self.pos[0])
            x1 = x+int(dirv)*32
            y = self.pos[1]
            yabove = y-32
            y2 = y+32
            
            top = self.layer.map.collide_point([x,yabove],"move")
            free1 = self.layer.map.collide_point([x1,y],"move")
            free2 = self.layer.map.collide_point([x1,y],"trigger")
            ground = self.layer.map.collide_point([x,y2],"move")
            
            freeground1 = self.layer.map.collide_point([x1,y2],"move")
            freeground2 = self.layer.map.collide_point([x1,y2],"trigger")
            
            if free1:
                print "no free spot",x1//32,y//32
                return
            if free2 and (hasattr(free2,"spikes") or hasattr(free2,"losepower")):
                print "free spot has spikes"
                return
            
            #~ if ground and top:
                #~ print "attached above and below"
                #~ return
            if ground and hasattr(ground,"vines") and ground.vines!="horiz":
                print "our ground is vines"
                return
            if top and hasattr(top,"vines"):
                print "our top is vines"
                return
            
            print freeground1,freeground2
            if not freeground1 or freeground2:
                print "our new ground is not valid"
                return

            free = self.layer.get_tile([x1//32,y//32])
            free.vines = self.vines
            free.col = self.col
            free.index = self.index
            free.surface = self.surface
            self.layer.cache_surface = None
            self.erase()
    def hit(self,agent,laser):
        if hasattr(self,"vines") and self.vines=="weak":
            x = self.pos[0]//32
            y = self.pos[1]//32-1
            to_erase = []
            while y>-1:
                t = self.layer.tiles[y][x]
                col = self.layer.map.collide_point([x*32+16,y*32+16],"move")
                if hasattr(t,"vines") and t.vines!="horiz":
                    to_erase.append(t)
                elif col and col.col:
                    to_erase = []
                    break
                else:
                    break
                y-=1
            to_erase2 = []
            y = self.pos[1]//32+1
            while y<len(self.layer.tiles):
                t = self.layer.tiles[y][x]
                col = self.layer.map.collide_point([x*32+16,y*32+16],"move")
                if hasattr(t,"vines") and t.vines!="horiz":
                    to_erase2.append(t)
                elif not col or not col.col:
                    to_erase.extend(to_erase2)
                    break
                else:
                    break
                y+=1
            for t in [self]+to_erase:
                falling = FallingTiles()
                falling.pos = t.pos[:]
                surf = pygame.Surface([32,32]).convert_alpha()
                surf.fill([0,0,0,0])
                s = self.layer.map.world.engine.surface
                self.layer.map.world.engine.surface = surf
                t.pos = [0,0]
                t.draw(self.layer.map.world.engine,[0,0])
                t.pos = falling.pos[:]
                self.layer.map.world.engine.surface = s
                falling.graphic = surf
                falling.surface = falling.graphic
                self.layer.map.world.add(falling)
                t.erase()
    def erase(self):
        if self.layer:
            #self.layer.tiles[self.pos[1]//32][self.pos[0]//32] = t = Tile()
            #t.layer = self.layer
            if hasattr(self,"door"):
                del self.door
                x = self.pos[0]//32
                y = self.pos[1]//32
                if y-1>-1:
                    t = self.layer.tiles[y-1][x]
                    if hasattr(t,"door"):
                        t.erase()
                if y+1<len(self.layer.tiles):
                    t = self.layer.tiles[y+1][x]
                    if hasattr(t,"door"):
                        t.erase()
            self.index = -1
            self.set_surface()
            if hasattr(self,"vines"):
                del self.vines
            self.col = None
            self.layer.cache_surface = None
            
class Frober(Agent):
    def init(self):
        self.items = []
        self.mapname = None
        self.interactable = FrobberInteractable(self)
    def init_properties(self):
        if hasattr(self,"chest"):
            if not self.chest:
                names = Item.names[:]
                random.sort(names)
                names = names[:4]
            else:
                names = self.chest.split(",")
            for name in names:
                item = Item()
                item.name = name
                self.items.append(item)
    def serialized(self):
        d = {"pos":self.pos,"right":self.right,"bottom":self.bottom,"items":[i.serialized() for i in self.items],"mapname":self.mapname}
        if hasattr(self,"chest"):
            d["chest"] = self.chest
        if hasattr(self,"sign"):
            d["sign"] = self.sign
        if hasattr(self,"stove"):
            d["stove"] = self.stove
        d["layer"] = self.layer
        return d
    @staticmethod
    def unserialize(dict,map):
        f = Frober()
        f.map = map
        f.mapname = dict["mapname"]
        f.pos = dict["pos"]
        f.right = dict["right"]
        f.bottom = dict["bottom"]
        f.items = [Item.unserialize(i) for i in dict["items"]]
        f.layer = dict["layer"]
        if "chest" in dict:
            f.chest = dict["chest"]
        if "sign" in dict:
            f.sign = dict["sign"]
        if "stove" in dict:
            f.stove = dict["stove"]
        return f
    def frobme(self,actor):
        self.interactable.frobme(actor)
    def pickitem(self,actor,item):
        actor.items.append(item)
        self.items.remove(item)
    def collide_point(self,point,flags=None):
        if point[0]>=self.pos[0] and point[0]<=self.right and point[1]>=self.pos[1] and point[1]<=self.bottom:
            return self
    def update(self,world):
        if hasattr(self,"stove"):
            self.stove_draw = "off"
            if self.stove=="on":
                if random.randint(0,100)>20:
                    self.stove_draw = "on"
    def draw(self,engine,offset=[0,0]):
        if hasattr(self,"stove"):
            if not hasattr(self,"stove_tiles"):
                self.stove_tiles = {}
                self.stove_tiles["on"] = Tile()
                self.stove_tiles["off"] = Tile()
                for ti in self.map.tile_properties:
                    if "stove_on" in self.map.tile_properties[ti]:
                        self.stove_tiles["on"].index = ti
                    if "stove_off" in self.map.tile_properties[ti]:
                        self.stove_tiles["off"].index = ti
            stove = self.stove
            t = self.stove_tiles[self.stove_draw]
            t.pos = self.pos[:]
            t.surface = self.map.tileset_list[t.index]
            t.draw(engine,offset)
            
class Light(Agent):
    def draw(self,engine,offset):
        pygame.draw.circle(engine.lightness_layer.surface,[33,33,33,255],[int(self.pos[0]-offset[0]+16),int(self.pos[1]-offset[1]+16)],64)
        pygame.draw.circle(engine.brightness_layer.surface,[33,33,33,255],[int(self.pos[0]-offset[0]+16),int(self.pos[1]-offset[1]+16)],32)
        
class TileLayer(Agent):
    def init(self):
        self.tiles = []
        self.cache_surface = None
        self.lights = []
    def serialized(self):
        return{"tiles":[[x.serialized() for x in row] for row in self.tiles],"layer":self.layer}
    @staticmethod
    def unserialize(d,map):
        tl = TileLayer()
        tl.map = map
        tl.tileset_list = map.tileset_list
        tl.tiles = [[Tile.unserialize(x,tl) for x in row] for row in d["tiles"]]
        tl.layer = d["layer"]
        return tl
    def draw(self,engine,offset):
        if not self.cache_surface:
            self.cache_surface = pygame.Surface([len(self.tiles[0])*32,len(self.tiles)*32]).convert_alpha()
            self.cache_surface.fill([0,0,0,0])
            s = engine.surface
            engine.surface = self.cache_surface
            for row in self.tiles:
                for tile in row:
                    tile.draw(engine,[0,0])
            engine.surface = s
        engine.surface.blit(self.cache_surface,[-offset[0],-offset[1]])
        [l.draw(engine,offset) for l in self.lights]
    def get_tile(self,pos):
        if pos[1]>=0 and pos[1]<len(self.tiles):
            if pos[0]>=0 and pos[0]<len(self.tiles[pos[1]]):
                return self.tiles[pos[1]][pos[0]]

class TileMap(Agent):
    tileset_images = {}
    def init(self):
        self.boundary = None
    def loadetm(self,map):
        import json
        f = open(map)
        s = f.read()
        f.close()
        d = json.loads(s)
        self.unserialize(d)
    def unserialize(self,d):
        self.mapfile = d["mapfile"]
        self.raw_tilesets = []
        self.tileset_list = [None]
        self.tile_properties = {}
        for tileset in d["raw_tilesets"]:
            self.add_tileset("art/tiles/"+tileset["source"],tileset["props"])
        def convrect(r):
            return pygame.Rect([[r[0],r[1]],[r[2],r[3]]])
        self.regions = {}
        for r in d["regions"]:
            self.regions[r] = convrect(d["regions"][r])
        self.warps = {}
        for wn in d["warps"]:
            w = d["warps"][wn]
            w["rect"] = convrect(w["rect"])
            self.warps[wn] = w
        self.frobers = [Frober.unserialize(f,self) for f in d["frobers"]]
        self.destinations = {}
        for dest in d["destinations"]:
            self.destinations[dest] = convrect(d["destinations"][dest])
        self.paths = d["paths"]
        self.npc_spawns = d["npc_spawns"]
        self.map = []
        numlayers = 0
        for layer in d["map"]:
            numlayers+=1
            self.map.append(TileLayer.unserialize(layer,self))
        print self.mapfile
        print "numlayers",numlayers
            
        if d.get("boundary",None):
            self.boundary = convrect(d["boundary"])
        
        self.mapname = d["mapname"]
        self.name = d["name"]
        self.setup()
    def saveetm(self):
        import json
        s = json.dumps(self.serialized())
        f = open(self.mapfile.replace(".tmx",".etm"),"wb")
        f.write(s)
        f.close()
    def serialized(self):
        d = {}
        d["mapfile"] = self.mapfile
        d["raw_tilesets"] = self.raw_tilesets
        def convrect(r):
            return r.left,r.top,r.width,r.height
        d["regions"] = {}
        for reg in self.regions:
            d["regions"][reg] = convrect(self.regions[reg])
        d["warps"] = {}
        for wn in self.warps:
            w = self.warps[wn]
            w2 = {}
            w2.update(w)
            w2["rect"] = convrect(w["rect"])
            d["warps"][wn] = w2
        d["frobers"] = [f.serialized() for f in self.frobers]
        d["destinations"] = {}
        for dest in self.destinations:
            d["destinations"][dest] = convrect(self.destinations[dest])
        d["paths"] = self.paths
        d["npc_spawns"] = self.npc_spawns
        
        if self.boundary:
            d["boundary"] = convrect(self.boundary)
        
        d["map"] = []
        for layer in self.map:
            d["map"].append(layer.serialized())
            
        d["mapname"] = self.mapname
        d["name"] = self.name
        return d
    def add_tileset(self,source,props):
        self.raw_tilesets.append({"source":os.path.split(source)[1],"props":props})
        if source not in self.tileset_images:
            self.tileset_images[source] = pygame.image.load(source).convert_alpha()
        tileset = self.tileset_images[source]
        x = 0
        y = 0
        i = 0
        while y*32<tileset.get_height():
            self.tileset_list.append(tileset.subsurface([[x*32,y*32],[32,32]]))
            if str(i) in props:
                self.tile_properties[len(self.tileset_list)-1] = props[str(i)]
            i += 1
            x+=1
            if x*32>=tileset.get_width():
                x=0
                y+=1
    def loadtmx(self,map):
        from tiledtmxloader import tmxreader
        self.mapfile = map
        raw_map = tmxreader.TileMapParser().parse_decode(self.mapfile)

        self.raw_tilesets = []
        self.tileset_list = [None]
        self.tile_properties = {}
        self.regions = {}   #rectangles
        self.warps = {}    #dicts with a rectangle
        self.frobers = []     #frober objects
        self.destinations = {}    #rects
        self.paths = {}         #points
        self.npc_spawns = []    #dicts
        
        for tileset_raw in raw_map.tile_sets:
            props = {}
            for tile in tileset_raw.tiles:
                props[tile.id] = tile.properties
            self.add_tileset(tileset_raw.images[0].source,props)

        self.map = []
        for layer in raw_map.layers:
            if hasattr(layer,"decoded_content"):
                self.read_tile_layer(layer)
            else:
                self.read_object_layer(layer)
        
        self.saveetm()
        self.setup()
    def load(self,map):
        if android or 0:
            return self.loadetm(map.replace(".tmx",".etm"))
        self.loadtmx(map)
    def read_tile_layer(self,layer):
        maplayer = TileLayer()
        maplayer.map = self
        maplayer.tileset_list = self.tileset_list
        maplayer.layer = len(self.map)
        x=y=0
        row = []
        nulltile = Tile()
        nulltile.index = -1
        for ti in layer.decoded_content:
            if ti==-1:
                row.append(nulltile)
            else:
                tile = Tile()
                tile.layer = maplayer
                tile.index = ti
                tile.set_surface()
                tile.pos = [x*32,y*32]
                for k,v in self.tile_properties.get(ti,{}).items():
                    setattr(tile,k,v)
                if getattr(tile,"light",None):
                    l = Light()
                    l.pos = tile.pos
                    maplayer.lights.append(l)
                row.append(tile)
            x+=1
            if x>=layer.width:
                x=0
                y+=1
                maplayer.tiles.append(row)
                row = []
        self.map.append(maplayer)
    def read_object_layer(self,layer):
        for o in layer.objects:
            r = pygame.Rect([[int(o.x),int(o.y)],[int(o.width),int(o.height)]])
            if o.name=="spawn":
                self.regions["spawn"] = r
            elif o.name=="playerspawn":
                self.regions["playerspawn"] = r
            elif "warp" in o.properties:
                map,target = o.properties["warp"].split("_")
                self.warps[o.name] = {"rect":r,"map":map,"warptarget":target,"direction":o.properties.get("direction","none")}
            elif "destination" in o.properties:
                self.destinations[o.properties["destination"]] = r
            if "path" in o.properties:
                points = o.polyline.split(" ")
                points = [[int(x) for x in y.split(",")] for y in points]
                points = [[x[0]+o.x,x[1]+o.y] for x in points]
                self.paths[o.properties["path"]] = points
            elif "npc" in o.properties:
                self.npc_spawns.append({"pos":[o.x,o.y],"props":o.properties})
            elif "boundary" in o.properties:
                self.boundary = r
            elif "chest" in o.properties or "sign" in o.properties or "stove" in o.properties:
                f = Frober()
                f.name = o.properties.get("name",o.name or "no_name")
                f.mapname = self.mapname
                f.map = self
                f.pos = [r.left,r.top]
                f.right,f.bottom = r.right,r.bottom
                for p in o.properties:
                    setattr(f,p,o.properties[p])
                f.init_properties()
                self.frobers.append(f)
    def setup(self):
        self.world.objects.extend(self.frobers)
        self.collisions = self.map[-1].tiles
        self.map_width = len(self.map[0].tiles[0])
        self.map_height = len(self.map[0].tiles)
        self.build_astar_graph()
        self.entity_map = {}
        self.entities = {}
    def add_entity(self,agent):
        p = agent.pos[0]//32,agent.pos[1]//32
        spot = self.entity_map.get(p,[])
        spot.append(agent)
        self.entities[agent] = spot
        self.entity_map[p] = spot
    def remove_entity(self,agent):
        if agent in self.entities:
            self.entities[agent].remove(agent)
            del self.entities[agent]
    def build_astar_graph(self):
        self.astar_graph = {}
        astar_grid = {}
        layer = self.collisions
        for row in layer:
            for tile in row:
                node = astar.AStarGridNode(tile.pos[0]//32,tile.pos[1]//32)
                node.tile = tile
                node.col = False
                if tile.col:
                    node.col = True
                astar_grid[(node.x,node.y)] = node
        for n in astar_grid:
            node = astar_grid[n]
            self.astar_graph[node] = []
            if node.col:
                continue
            for i in [-1, 0, 1]:
                for j in [-1, 0, 1]:
                    nn = astar_grid.get((node.x+i,node.y+j))
                    if not nn:
                        continue
                    if nn.col:
                        continue
                    self.astar_graph[node].append(nn)
        self.astar_path = astar.AStarGrid(self.astar_graph)
        self.astar_grid = astar_grid
    def reset_astar_graph(self):
        """Clear parents"""
        for n in self.astar_grid:
            node = self.astar_grid[n]
            node.parent = None
            node.h = 0
            node.g = 0
            node.blocked = False
            if self.entity_map.get(n,None):
                node.blocked = True
    def get_path(self,pos,dest):
        #Seems bad to rebuild this on every lookup!
        self.reset_astar_graph()
        y=pos[1]//32
        x=pos[0]//32
        x1=dest[0]//32
        y1=dest[1]//32
        print "search",x,y,"-",x1,y1
        search = self.astar_path.search(self.astar_grid[(x,y)],self.astar_grid[(x1,y1)])
        if not search:
            return []
        return [[n.x*32+16,n.y*32+16] for n in search]
    def collide(self,agent,flags=None):
        r = agent.rect()
        for point in ([r.left,r.top],[r.right,r.top],[r.left,r.bottom],[r.right,r.bottom],[r.right,r.center[1]],[r.left,r.center[1]],[r.center[0],r.top],[r.center[0],r.bottom]):
            col = self.collide_point(point,flags)
            if col:
                return col
    def collide_point(self,point,flags=None):
            x,y = [i//32 for i in point]
            if x<0 or y<0 or x>=self.map_width or y>=self.map_height:
                t = Tile()
                t.pos = [x*32,y*32]
                t.col = "full"
                t.nothing = True
                return t
            col = 0
            if flags=="move" or flags=="trigger":
                for layer in reversed(self.map):
                    tile = layer.tiles[y][x].collide_point(point,flags)
                    if tile:
                        return tile
                tile = self.collisions[y][x].collide_point(point,flags)
                if tile:
                    return tile
                if flags=="trigger":
                    for warp in self.warps.values():
                        r = warp["rect"]
                        if point[0]>=r.left and point[0]<=r.right and point[1]>=r.top and point[1]<=r.bottom:
                            return warp
            if flags=="frobme":
                for frober in self.frobers:
                    if frober.collide_point(point,flags):
                        return frober
    def get_sprites(self):
        return [layer for layer in self.map]
    def rect(self):
        if self.boundary:
            return self.boundary
        return pygame.Rect([self.pos,[self.map_width*32,self.map_height*32]])
    def click(self,world,controller):
        self = world
        self.player.assign_ai(active=True)
        self.player.follow_path=None
        pa = self.player.pos
        pb = [controller.mpos[0]+self.offset[0],controller.mpos[1]+self.offset[1]]
        self.player.following_points = self.maps[self.player.mapname].get_path(pa,pb)[1:]
        if self.player.following_points:
            self.player.follow_path = True