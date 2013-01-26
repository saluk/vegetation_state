class Quest(object):
    dialogs = ["greet"]
    def init(self,npc):
        self.agent = npc
        self.done = False
    def is_true(self,player,dialog):
        return False
    def conditions(self,actor,dialog):
        if dialog in self.dialogs and self.is_true(actor,dialog):
            return True
    def pre_dialog(self,actor,dialog):
        if self.conditions(actor,dialog):
            q = self.pre(actor,dialog)
            if q:
                return q
            return self.__class__.__name__
    def pre(self,actor,dialog):
        pass
    def post_dialog(self,actor,dialog):
        if self.conditions(actor,dialog):
            self.post(actor,dialog)
            return self.__class__.__name__
    def post(self,actor,dialog):
        pass
    def finish(self):
        self.done = True

class NeedMirror(Quest):
    dialogs = ["greet","mirror"]
    def is_true(self,actor,dialog):
        if "mirror" in actor.items.names():
            return True
    def pre(self,actor,dialog):
        self.agent.items.transfer(actor.items,name="mirror")
        for q in self.agent.quests:
            if isinstance(q,CheckItemDialog):
                if "mirror" not in q.dialogs:
                    q.dialogs.append("mirror")
        return "has_mirror"
    def post(self,actor,dialog):
        self.finish()
    def finish(self):
        super(NeedMirror,self).finish()
        print "set agent mood"
        self.agent.mood = "happy"
        
class CheckItemDialog(Quest):
    dialogs = ["greet","mirror"]
    def init(self,npc):
        super(self.__class__,self).init(npc)
        self.dialogs = npc.items.names()
    def is_true(self,actor,dialog):
        if dialog not in self.agent.items.names():
            return True
    def pre(self,actor,dialog):
        print "setting quest!"
        self.agent.mood = "mad"
        return "missing_item"
    def post(self,actor,dialog):
        self.finish()