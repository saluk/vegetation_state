import random

class Interactable(object):
    def __init__(self,agent):
        self.agent = agent
    def frobme(self,actor):
        actor.say(self.agent.description)
        
class FrobberInteractable(Interactable):
    def frobme(self,actor):
        parent = self.agent
        if hasattr(parent,"chest"):
            self.frob_chest(actor)
        if hasattr(parent,"sign"):
            self.frob_sign(actor)
        if hasattr(parent,"stove"):
            self.frob_stove(actor)
    def frob_chest(self,actor):
        parent = self.agent
        if actor.menu:
            options = []
            for i in parent.items:
                options.append( (i.name,parent.items.transfer,(actor.items,i)) )
            actor.menu.setup(options)
    def frob_sign(self,actor):
        actor.say(self.agent.sign)
    def frob_stove(self,actor):
        parent = self.agent
        if parent.stove=="off":
            parent.stove = "on"
        else:
            parent.stove = "off"

class CharacterInteractable(Interactable):
    def frobme(self,actor):
        parent = self.agent
        if actor.menu:
            options = []
            if parent.following==actor:
                options.append( ("'Stop'",parent.unfollow,(actor,)) )
            else:
                options.append( ("'follow me!'",parent.follow,(actor,)) )
                options.append( ("pickpocket",self.action_pickpocket,(actor,)) )
                options.append( ("slip in pocket",self.action_putpocket,(actor,)) )
                options.append( ("greet",self.action_dialog,(actor,"greet")) )
                options.append( ("ask",self.action_ask,(actor,)) )
            actor.menu.setup(options,label="Options for "+parent.name)
    def action_ask(self,actor):
        parent = self.agent
        if actor.menu:
            options = []
            on = set()
            for t in actor.topics:
                on.add(t)
                options.append( (t,self.action_dialog,(actor,t)) )
            for n in actor.items:
                if n.name not in on:
                    on.add(n.name)
                    options.append( (n.name,self.action_dialog,(actor,n.name)) )
            if not options:
                actor.say("You can't think of anything to ask.")
                return
            actor.menu.setup(options,label="Ask "+parent.name+" about:")
    def action_dialog(self,actor,dialog):
        parent = self.agent
        matched_quest = None
        quest = ""
        for q in parent.quests:
            quest = q.pre_dialog(actor,dialog)
            if quest:
                matched_quest = q
                break
        if not isinstance(quest,str):
            quest = ""
        cd = parent.world.dialogs
        moods = {"happy":"e_h","normal":"e_n","mad":"e_m"}
        match = [dialog,parent.name,moods[parent.mood],quest]
        while match:
            print match
            ms = " ".join(match)
            print ms
            d = cd.get(ms,None)
            if not d:
                match = match[:-1]
                continue
            parent.say_many(d,actor,[parent])
            if matched_quest:
                matched_quest.post(actor,dialog)
            parent.aicontroller.walk_toward(actor.pos)
            return
    def action_pickpocket(self,actor):
        parent = self.agent
        if actor.menu:
            options = [ ("S",self.action_takeitem,(actor,)) ]
            for i in range(random.randint(10,20)):
                options.append( ("F",self.action_fail,(actor,)) )
            random.shuffle(options)
            actor.menu.setup(options,pause=True,label="Pickpocket",ttl=random.randint(3,6)*30)
    def action_takeitem(self,actor):
        parent = self.agent
        if actor.menu:
            options = []
            for i in parent.items:
                options.append( (i.name,actor.items.transfer,(parent.items,i)) )
            if not options:
                return actor.say("empty pockets")
            actor.menu.setup(options,pause=True,label="Choose Reward")
    def action_fail(self,actor):
        actor.say("What are you trying?")
    def action_putpocket(self,actor):
        parent = self.agent
        if actor.menu:
            options = []
            for i in actor.items:
                options.append( (i.name,parent.items.transfer,(actor.items,i)) )
            actor.menu.setup(options,label="Slip item in "+parent.name+"'s pocket")