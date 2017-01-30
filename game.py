# -*- coding: utf-8 -*-
from  __future__ import unicode_literals
import random
import uuid

class GameConfig:
    def __init__(self, wolfCnt, vilCnt, witchEn, guardEn, hunterEn, proEn, metric):
        self.wolfCnt = wolfCnt
        self.vilCnt  = vilCnt
        self.witchEn = witchEn
        self.guardEn = guardEn
        self.hunterEn = hunterEn
        self.proEn = proEn
        self.metric = metric

class Role:
    WOLF = 0
    VILLAGER = 1
    WITCH = 2 
    GUARD = 3
    HUNTER = 4
    PROPHET = 5
    EMPTY = 6

    Role2Str = {WOLF: "狼人", VILLAGER: "普通村民", WITCH: "女巫",
               GUARD: "守卫", HUNTER: "猎人", PROPHET: "预言家" }

class PlayerDatabase:
    def __init__(self):
        self.players = {}

    def exist(self, username):
        return self.players.get(username) != None

    def addPlayer(self, username, password):
        self.players[username] = Player(username, password)

    def check(self, username, password):
        return self.players[username].password == password

    def get(self, username):
        return self.players[username]

    def __repr__(self):
        for pl in self.players:
            print (pl.username, pl.password)

class Player:
    PST_WAIT = 0
    PST_INGAME = 1
    PST_HOST = 2

    def __init__(self, username, password):
        self.username = username
        self.password = password
        self.state = Player.PST_WAIT
        self.role  = Role.EMPTY

    def setRole(self, role):
        self.role = role
        self.alive = True

    def isAlive(self):
        return self.alive

    def die(self, deathCause):
        self.alive = False
        self.deathCause = deathCause

    def doDie(self):
        self.alive = False
    def undoDie(self):
        self.alive = True

    def getCause(self):
        return self.deathCause
    def getRole(self):
        return Role.Role2Str[self.role]

class Engine:
    def __init__(self):
        self.log = []
        self.counter = 0

class Deliver:
    def __init__(self):
        self.to = {}
        self.his = {}

    def add(self, username, msg):
        if (self.to.get(username) == None):
            self.to[username] = []
            self.his[username] = []
        self.to[username].append(msg)
        self.his[username].append(msg)

    def reloadHistory(self, username):
        self.to[username] = self.his[username]

    def addMany(self, users, msg):
        for item in users:
            self.add(item, msg)

    def fetch(self, username):
        if (self.to.get(username) == None):
            return []
        else:
            tmp = self.to[username]
            self.to[username] = []
            return tmp

class Game:
    GST_NEWGAME   = 0
    GST_WAIT_JOIN = 1
    GST_START     = 2
    GST_SEND_CLOSE_EYE = 3
    GST_WAIT_CLOSE_EYE = 4
    GST_SEND_GUARD = 5
    GST_WAIT_GUARD = 6
    GST_SEND_PRO   = 7
    GST_WAIT_PRO   = 8
    GST_SEND_WOLF  = 9
    GST_WAIT_WOLF  = 10
    GST_SEND_WITCH = 11
    GST_WAIT_WITCH = 12
    GST_DAWN       = 13
    GST_SEND_ELECT  = 14
    GST_WAIT_ELECT  = 15
    GST_SEND_DOWN_WATER = 16
    GST_WAIT_DOWN_WATER = 17
    GST_SEND_POLICE_VOTE = 18
    GST_WAIT_POLICE_VOTE = 19
    GST_SEND_DEATH    = 20
    GST_SEND_HANDOVER = 21
    GST_WAIT_HANDOVER = 22
    GST_SEND_EXILE = 23
    GST_WAIT_EXILE = 24
    GST_SEND_EXILE_VOTE = 25
    GST_WAIT_EXILE_VOTE = 26
    GST_SEND_EXILE_INFO = 27
    GST_SEND_HUNTER = 28
    GST_WAIT_HUNTER = 29
    GST_SOMEONE_DIE = 30

    GST_GAME_OVER = 98
    GST_ROOM_CLOSED = 99

    WIN_GOOD = 0
    WIN_WOLF = 1

    def __init__(self):
        self.state = Game.GST_NEWGAME
        self.host  = None
        self.wolves = []
        self.vils  = []
        self.guard = self.witch = self.pro = self.hunter = None
        self.canPoison = self.canMedicine = True
        self.players = {}
        self.lastGuard = None
        self.police = None
        self.beGuarded = self.bePoisoned = self.beMedicined = None
        self.cfg = None
        self.playerNum = 0
        self.deliver = Deliver()
        self.his = {}
        self.day = 0

    # GAME CONFIG
    def setConfig(self, cfg):
        self.cfg = cfg
        self.playerNum = cfg.wolfCnt + cfg.vilCnt
        if (cfg.witchEn):
            self.playerNum += 1
        if (cfg.guardEn):
            self.playerNum += 1
        if (cfg.hunterEn):
            self.playerNum += 1
        if (cfg.proEn):
            self.playerNum += 1

    def setHost(self, pl):
        self.host = pl.username
        self.players[pl.username] = pl
        self.sendPlayer(pl.username, {"type":"host-control-panel"})

    def addPlayer(self, pl):
        if self.isFull():
            return False
        self.players[pl.username] = pl

        self.sendPlayer(pl.username, {"type":"player-control-panel"})
        if self.isFull():
            self.sendHost({'type': 'start-button'})
        return True

    # UTILITY
    def isFull(self):
        return len(self.players) == self.playerNum

    def checkHost(self, name):
        return (self.host == name)
    def checkPlayer(self, name):
        return name in self.players

    def sendHost(self, msg):
        self.deliver.add(self.host, msg)
    def sendPlayer(self, name, msg):
        self.deliver.add(name, msg)
    def sendMany(self, many, msg):
        for item in many:
            self.deliver.add(item, msg)
    def sendAll(self, msg):
        for item in self.players:
            self.deliver.add(item, msg)

    def getPlayers(self):
        names = []
        for item in self.players:
            names.append(item)

        return names

    # GAME PROCEDURE
    def enterRoom(self, name):
        self.sendAll({'type': 'player-info', 'players': self.getPlayers()})
        self.deliver.reloadHistory(name)

    def quitRoom(self, name):
        del self.players[name]
        self.sendAll({'type': 'player-info', 'players': self.getPlayers()})

    def start(self):
        self.allocateRole()
        self.state = Game.GST_START
        self.doStage(self.host, None)

    def allocateRole(self):
        pls = self.getPlayers()
        random.shuffle(pls)
        cfg = self.cfg;

        i = 0
        while (i < cfg.wolfCnt):
            self.players[pls[i]].setRole(Role.WOLF)
            self.wolves.append(pls[i])
            i += 1
        team = "队友： " + self.wolves[0]
        for j in range(1,len(self.wolves)):
            team += "， " + (self.wolves[j])

        self.sendMany(self.wolves, {'type':'role', 'role': '狼人（' +team+ '）'})
        while (i < cfg.wolfCnt + cfg.vilCnt):
            self.players[pls[i]].setRole(Role.VILLAGER)
            self.vils.append(pls[i])
            self.sendPlayer(pls[i], {'type':'role', 'role':'普通村民'})
            i += 1
        if (cfg.witchEn):
            self.players[pls[i]].setRole(Role.WITCH)
            self.witch = pls[i]
            self.sendPlayer(pls[i], {'type':'role', 'role':'女巫'})
            i += 1
        if (cfg.guardEn):
            self.players[pls[i]].setRole(Role.GUARD)
            self.guard = pls[i]
            self.sendPlayer(pls[i], {'type':'role', 'role':'守卫'})
            i += 1
        if (cfg.hunterEn):
            self.players[pls[i]].setRole(Role.HUNTER)
            self.hunter = pls[i]
            self.sendPlayer(pls[i], {'type':'role', 'role':'猎人'})
            i += 1
        if (cfg.proEn):
            self.players[pls[i]].setRole(Role.PROPHET)
            self.pro = pls[i]
            self.sendPlayer(pls[i], {'type':'role', 'role':'预言家'})
            i += 1

        self.sendHost({'type': 'role-info', 'info': self.printRoles()})
        self.sendHost({'type':'ingame-button'})

        '''self.guard = self.host
        self.witch = self.host
        self.pro   = self.host'''

    def getAlive(self):
        names = []
        for item in self.players:
            if self.players[item].isAlive():
                names.append(item)
        return names
    def getAliveWolves(self):
        names = []
        for item in self.wolves:
            if self.players[item].isAlive():
                names.append(item)
        return names
    def getGuardList(self):
        names = []
        for item in self.players:
            if (self.players[item].isAlive() and item != self.lastGuard):
                names.append(item)
        return names
    def getHunterList(self):
        names = []
        for item in self.players:
            if (self.players[item].isAlive() and item != self.hunter):
                names.append(item)
        return names

    def doStage(self, name, data):

        again = True
        while (again):
            print("in state", self.state)
            again = False
            if (self.state == Game.GST_START):
                self.state = Game.GST_SEND_CLOSE_EYE
                #self.state = Game.GST_SEND_EXILE
                #self.state = Game.GST_GAME_OVER
                #for item in self.vils:
                    #self.players[item].die("")
                again = True
            
            #====== CLOSE EYE ======#
            elif (self.state == Game.GST_SEND_CLOSE_EYE):
                self.sendHost({"type": "close-eye-button"})
                self.beGuarded = self.bePoisoned = self.beMedicined = None
                self.state = Game.GST_WAIT_CLOSE_EYE
            elif (self.state == Game.GST_WAIT_CLOSE_EYE):
                if (data.get("type") == "close-eye" and self.checkHost(name)):
                    self.state = Game.GST_SEND_GUARD
                    again = True

            #====== NIGHT ======#
            # GUARD
            elif (self.state == Game.GST_SEND_GUARD):
                self.sendAll({"type": "night-come"})
                if (self.cfg.guardEn and self.players[self.guard].isAlive()):
                    self.sendPlayer(self.guard, {"type": "guard-button",
                        "players": self.getGuardList()})
                    self.state = Game.GST_WAIT_GUARD
                else:
                    self.state = Game.GST_SEND_PRO
                    again = True
            elif (self.state == Game.GST_WAIT_GUARD):
                if (data.get("type") == "choose-guard" and self.guard == name
                        and (data.get("name") in self.getGuardList())):
                    self.beGuarded = data.get("name")
                    self.lastGuard = self.beGuarded
                    self.state = Game.GST_SEND_PRO
                    print(self.beGuarded, "be guarded")
                    again = True
            # PROPHET
            elif (self.state == Game.GST_SEND_PRO):
                if (self.cfg.proEn and self.players[self.pro].isAlive()):
                    self.sendPlayer(self.pro, {"type": "pro-button",
                        "players": self.getAlive()})
                    self.state = Game.GST_WAIT_PRO
                else:
                    self.state = Game.GST_SEND_WOLF
                    again = True
            elif (self.state == Game.GST_WAIT_PRO):
                if (data.get("type") == "choose-pro" and self.pro == name
                        and (data.get("name") in self.getAlive())):
                    self.state = Game.GST_SEND_WOLF
                    name = data.get("name")
                    ans = "狼人" if (name in self.wolves) else "好人"
                    self.sendPlayer(self.pro, {"type": "pro-info",
                        "name": name, "role": ans})
                    print(name, "is", ans)
                    again = True
            # WOLF
            elif (self.state == Game.GST_SEND_WOLF):
                kl = self.getAlive()
                vt = self.getAliveWolves()

                self.sendMany(vt, {"type": "kill-button", "players": kl})

                self.vote = self.newVote(vt, kl)
                self.state = Game.GST_WAIT_WOLF
            elif (self.state == Game.GST_WAIT_WOLF):
                if (data.get("type") == "choose-kill" and name in self.voters):
                    allVote = self.setVote(name, data.get("name"))
                    print(name, "vote to", data.get("name"))
                    if (allVote):
                        self.beKilled, tie = self.getVoteResult()
                        self.sendMany(self.voters, {"type": "vote-result",
                            "tie": tie, "ballot": self.ballot,
                            "select": self.beKilled, "msg": "被杀" })
                        if (tie):
                            print("tie in kill vote")
                            self.state = Game.GST_SEND_WOLF
                        else:
                            print(self.beKilled, "be chosen to kill")
                            self.state = Game.GST_SEND_WITCH

                        # do death for check win
                        self.players[self.beKilled].doDie()
                        gg, winner = self.checkWin()
                        if (gg):
                            self.players[self.beKilled].die("夜里")
                            self.state = Game.GST_GAME_OVER
                        else:
                            self.players[self.beKilled].undoDie()
                            self.state = Game.GST_SEND_WITCH
                        again = True

            # WITCH
            elif (self.state == Game.GST_SEND_WITCH):
                if (self.cfg.witchEn and self.players[self.witch].isAlive()):
                    self.sendPlayer(self.witch, {"type": "witch-button",
                        "canPoison": self.canPoison,
                        "canMedicine": self.canMedicine,
                        "beKilled": self.beKilled if self.canPoison else "",
                        "players": self.getAlive()})
                    self.state = Game.GST_WAIT_WITCH
                else:
                    self.state = Game.GST_DAWN
                    again = True
            elif (self.state == Game.GST_WAIT_WITCH):
                if (data.get("type") == "choose-witch" and self.witch == name):
                    action = self.witchAction = data.get("action")
                    if (action == "poison" and self.canPoison):
                        self.bePoisoned = data.get("name")
                        self.canPoison = False
                        print(self.bePoisoned, "be poisoned")
                    elif (action == "medicine" and self.canMedicine):
                        self.beMedicined = self.beKilled
                        self.canMedicine = False
                        print(self.beMedicined, "be medicined")
                    else:
                        print("witch pass")

                    self.state = Game.GST_DAWN
                    again = True
            # JUDGE IN THE DAWN
            elif (self.state == Game.GST_DAWN):
                self.die = [self.beKilled]
                if ((self.beKilled == self.beGuarded or self.beKilled ==
                    self.beMedicined) and self.beGuarded != self.beMedicined):
                    self.die = []

                if (self.bePoisoned != None):
                    self.die += [self.bePoisoned]
                if (len(self.die) == 2 and self.die[0] == self.die[1]):
                    self.die = [self.die[0]]

                self.day += 1
                if (self.day == 1):  # 第一天竞选警长
                    self.state = Game.GST_SEND_ELECT
                else:
                    self.state = Game.GST_SEND_DEATH
                again = True

                # send info to hunter
                if (self.hunter in self.die and self.hunter != self.bePoisoned):
                    self.sendPlayer(self.hunter, {"type": "hunter-enable"})

                self.sendAll({"type":"day-info", "day": self.day})

            #====== DAY ======#
            elif (self.state == Game.GST_SEND_ELECT): # 是否竞选警长
                self.candidates = []
                self.decided = {}
                self.sendAll({"type": "elect-button"})
                self.state = Game.GST_WAIT_ELECT
                again = True
            elif (self.state == Game.GST_WAIT_ELECT):
                if (data.get("type")=="choose-elect" and name in self.players):
                    if (data.get("action") == "up"): # 参加竞选
                        self.decided[name] = True
                        self.candidates.append(name)
                    elif (data.get("action") == "down"): # 不参加
                        self.decided[name] = True

                    if (len(self.decided) == len(self.players)):
                        self.state = Game.GST_SEND_DOWN_WATER
                        again = True

            elif (self.state == Game.GST_SEND_DOWN_WATER): # 退水，开始投票
                self.sendAll({"type": "elect-info", "players": self.candidates})
                self.sendMany(self.candidates, {"type": "down-water-button"})
                self.sendHost({"type": "start-elect-button"})
                self.state = Game.GST_WAIT_DOWN_WATER
                again = True
            elif (self.state == Game.GST_WAIT_DOWN_WATER):
                if (data.get("type")=="down-water" and name in self.candidates):
                    self.sendAll({"type": "down-water-info", "name": name})
                    self.candidates.remove(name)
                elif (data.get("type") == "start-elect" and name == self.host):
                    # host开始竞选投票
                    self.state = Game.GST_SEND_POLICE_VOTE
                    again = True

            elif (self.state == Game.GST_SEND_POLICE_VOTE): # 警长投票
                if (len(self.candidates) == 0):
                    self.police = None
                    self.sendAll({"type": "no-police-info"})
                    self.state = Game.GST_SEND_DEATH
                    again = True
                elif (len(self.candidates) == 1):
                    self.police = self.candidates[0]
                    self.sendAll({"type": "one-police-info",
                                  "name": self.police})
                    self.state = Game.GST_SEND_DEATH
                    again = True
                else:
                    vt = []
                    for item in self.players:
                        if (not item in self.candidates):
                            vt.append(item)
                    self.sendMany(vt, {"type": "elect-vote",
                                        "players": self.candidates})

                    self.vote = self.newVote(vt, self.candidates)
                    self.state = Game.GST_WAIT_POLICE_VOTE
            elif (self.state == Game.GST_WAIT_POLICE_VOTE):
                if (data.get("type") == "elect-vote" and name in self.voters):
                    allVote = self.setVote(name, data.get("name"))
                    print(name, "vote to", data.get("name"))
                    if (allVote):
                        self.police, tie = self.getVoteResult()
                        self.sendMany(self.players, {"type": "vote-result",
                            "tie": tie, "ballot": self.ballot,
                            "select": self.police, "msg": "当选警长" })
                        if (tie):
                            print("tie in elect vote")
                            self.state = Game.GST_SEND_POLICE_VOTE
                        else:
                            print(self.police, "be chosen to be police")
                            self.state = Game.GST_SEND_DEATH
                        again = True

            elif (self.state == Game.GST_SEND_DEATH):
                self.sendAll({"type": "death-info", "death": self.die,
                              "day" : self.day})
                for item in self.die:
                    self.players[item].die("夜里")

                gg, winner = self.checkWin()
                if (gg):
                    self.state = Game.GST_GAME_OVER
                else:
                    # backup state after hunter and police handover
                    self.normalState = Game.GST_SEND_EXILE
                    self.state = Game.GST_SEND_HUNTER # 结算猎人和警徽
                again = True

            # HUNTER
            elif (self.state == Game.GST_SEND_HUNTER):
                if (self.cfg.hunterEn and self.hunter in self.die):
                    self.sendPlayer(self.hunter, {"type":"choose-hunter",
                            "players" : self.getHunterList()})
                    self.state = Game.GST_WAIT_HUNTER
                    again = True
                else:
                    self.state = Game.GST_SEND_HANDOVER
                    again = True
            elif (self.state == Game.GST_WAIT_HUNTER):
                if (data.get("type") == "choose-hunter" and name==self.hunter):
                    if (data.get("action") == "hunter"):
                        to = data.get("name")
                        self.die.append(to)
                        self.players[to].die("猎杀")
                        self.sendAll({"type": "hunter-info", "from":self.hunter,
                                                             "to": to})
                        gg, winner = self.checkWin()
                        if (gg):
                            self.state = Game.GST_GAME_OVER
                        else:
                            self.state = Game.GST_SEND_HANDOVER
                    else:
                        self.state = Game.GST_SEND_HANDOVER
                    again = True

            # HANDOVER OF POLICE
            elif (self.state == Game.GST_SEND_HANDOVER): # 移交/撕毁警徽
                if (self.police in self.die):
                    print("police", self.police, "die")
                    self.sendPlayer(self.police, {"type": "handover-button",
                        "players": self.getAlive()})
                    self.state = Game.GST_WAIT_HANDOVER
                else:
                    print("police", self.police, "alive")
                    self.state = self.normalState
                    again = True
            elif (self.state == Game.GST_WAIT_HANDOVER):
                if (data.get("type")=="choose-handover" and name==self.police):
                    if (data.get("action") == "handover"):
                        self.police = data.get("name")
                        self.sendAll({"type": "handover-info", "tear": False,
                                      "name": self.police})
                    elif (data.get("action") == "tear"):
                        self.police = None
                        self.sendAll({"type": "handover-info", "tear": True})
                    self.state = self.normalState
                    again = True

            elif (self.state == Game.GST_SEND_EXILE):  # host开始放逐投票按钮
                number = []; name   = []; status = []; color =[];
                i = 1
                for item in self.players:
                    number.append(i)
                    name.append(item)
                    if (self.players[item].isAlive()):
                        if (item == self.police):
                            status.append("警长")
                            color.append("success")
                        else:
                            status.append("普通")
                            color.append("default")
                    else:
                        color.append("danger")
                        status.append("死亡（" + self.players[item].getCause()
                                                                    + "）")
                    i = i + 1

                self.sendAll({"type": "status-table", "number": number,
                    "name": name, "status": status, "color": color})
                self.sendMany(self.getAliveWolves(), {"type": "boom-button"})
                self.sendHost({"type": "start-exile-button"})
                self.state = Game.GST_WAIT_EXILE
            elif (self.state == Game.GST_WAIT_EXILE):
                if (data.get("type")=="start-exile" and name==self.host):
                    self.state = Game.GST_SEND_EXILE_VOTE
                    again = True
                elif (data.get("type") == "choose-boom" and
                                                    name in self.wolves):
                    self.die = [name]
                    self.players[name].die("自爆")
                    self.sendAll({"type": "boom-info", "name":name})
                    gg, winner = self.checkWin()
                    if (gg):
                        self.state = Game.GST_GAME_OVER
                    else:
                        self.normalState = Game.GST_SEND_GUARD # 直接进入晚上
                        self.state = Game.GST_SEND_HANDOVER
                    again = True

            elif (self.state == Game.GST_SEND_EXILE_VOTE): # 放逐投票
                vt = self.getAlive()
                ops = self.getAlive()
                self.sendMany(vt, {"type": "exile-vote", "players": ops})
                self.vote = self.newVote(vt, ops)
                self.state = Game.GST_WAIT_EXILE_VOTE
            elif (self.state == Game.GST_WAIT_EXILE_VOTE):
                if (data.get("type") == "exile-vote" and name in self.voters):
                    allVote = self.setVote(name, data.get("name"))
                    print (name, "vote to", data.get("name"))
                    if (allVote):
                        self.beExiled, tie = self.getVoteResult()
                        if (tie and self.police != None and  # 警长1.5票
                                self.ballot[self.police] in self.beExiled):
                            self.beExiled = self.ballot[self.police]
                            tie = False
                        self.sendMany(self.getAlive(), {"type": "vote-result",
                            "tie": tie, "ballot": self.ballot,
                            "select": self.beExiled, "msg": "被票死" })
                        if (tie):
                            print("tie in exile vote")
                            self.state = Game.GST_SEND_EXILE_VOTE
                        else:
                            print(self.beExiled, "be choosen to exile")
                            self.state = Game.GST_SEND_EXILE_INFO
                        again = True

            elif (self.state == Game.GST_SEND_EXILE_INFO):
                #self.sendAll({"type": "exile-info", "name": self.beExiled})
                self.die = [self.beExiled]
                self.players[self.beExiled].die("投票")

                gg, winner = self.checkWin()
                if (gg):
                    self.state = Game.GST_GAME_OVER
                else:
                    self.normalState = Game.GST_SEND_CLOSE_EYE # backup state
                    self.state = Game.GST_SEND_HUNTER # 结算猎人和警徽
                again = True

            elif (self.state == Game.GST_GAME_OVER):
                gg, winner = self.checkWin()
                if (winner == Game.WIN_GOOD):
                    winner_msg = "好人"
                else:
                    winner_msg = "狼人"
                self.sendAll({"type": "game-over", "winner": winner_msg})

                # STATISTIC
                number = []; name = []; status = []; color =[]; role = []
                i = 1
                for item in self.players:
                    number.append(i)
                    name.append(item)
                    if (self.players[item].isAlive()):
                        if (item == self.police):
                            status.append("警长")
                        else:
                            status.append("普通")
                    else:
                        status.append("死亡（" + self.players[item].getCause()
                                                                    + "）")
                    if ((winner == Game.WIN_WOLF and item in self.wolves) or
                        (winner == Game.WIN_GOOD and (not item in self.wolves))):
                        color.append("success")
                    else:
                        color.append("default")
                    role.append(self.players[item].getRole())
                    i = i + 1

                self.sendAll({"type": "game-statistic", "number": number,
                    "name":name, "status":status, "color":color, "role":role})

    # CHECK WIN
    def checkWin(self):
        numWolf = numVil = numGod = 0
        for item in self.players:
            if (self.players[item].isAlive()):
                if (item in self.wolves):
                    numWolf += 1
                elif (item in self.vils):
                    numVil  += 1
                else:
                    numGod  += 1
        # death
        if (numWolf == 0):
            return True, Game.WIN_GOOD
        if (self.cfg.metric == "side"):
            if (numVil == 0 or numGod == 0):
                return True, Game.WIN_WOLF
        else:
            if (numVil + numGod == 0):
                return True, Game.WIN_WOLF
        # vote
        voteWolf = numWolf; voteGood = numVil + numGod;
        if (self.police != None and self.players[self.police].isAlive()):
            if (self.police in self.wolves):
                voteWolf += 0.5
            else:
                voteGood += 0.5
        if (voteWolf >= voteGood):
            return True, Game.WIN_WOLF
        return False, -1

    # UTILITY FOR VOTE
    def newVote(self, voters, options):
        self.voters = voters
        self.options = options
        self.ballot = {}
    def setVote(self, name, to):
        if ((not name in self.voters) or (not to in self.options)):
            return False
        self.ballot[name] = to
        if (len(self.ballot) == len(self.voters)):
            return True
    def getVoteResult(self):
        acc = {}
        for item in self.options:
            acc[item] = 0
        for item in self.ballot:
            acc[self.ballot[item]] += 1

        maxi = -1
        for item in acc:
            if acc[item] == maxi:
                ret = [ret, item]
                tie = True
            elif acc[item] > maxi:
                tie = False
                maxi = acc[item]
                ret = item

        return ret, tie

    def printRoles(self):
        info = ""
        info += "wolf: " + str(self.wolves) + '\n'
        info += "vil: " + str(self.vils) + '\n'
        info += "guard: " + str(self.guard) + '\n'
        info += "hunter: " + str(self.hunter) + '\n'
        info += "witch: " + str(self.witch) + '\n'
        info += "prophet: " + str(self.pro) + '\n'
        print(info)
        return info

    def close(self):
        print("send room closed")
        self.sendAll({"type": "room-closed"})
        self.state = Game.GST_ROOM_CLOSED
