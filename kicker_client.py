#!/usr/bin/env python
# -*- coding: utf-8 -*-

import re, os, codecs, sys, time, StringIO, textwrap, platform, webbrowser, shutil, datetime, time
import wx, wx.grid, wx.py.editor, wx.py.editwindow, wx.html, wx.lib.hyperlink
sys.path.append("/home/bronger/src/chantal_ipv/current/remote_client")
import chantal_remote


class Player(object):
    def __init__(self, shortkey):
        self.username, self.nickname = chantal_remote.connection.open("kicker/player?shortkey={0}".format(shortkey))
    def __unicode__(self):
        return self.nickname
    def __eq__(self, other):
        return self.username == other.username


class Frame(wx.Frame):

    def __init__(self, *args, **keyw):
        super(Frame, self).__init__(None, wx.ID_ANY, size=wx.DisplaySize(), title="Kicker", *args, **keyw)
        self.ShowFullScreen(True)
        panel = wx.Panel(self, wx.ID_ANY, size=(0, 0))
        panel.Bind(wx.EVT_CHAR, self.OnKeyPress)
        panel.SetFocusIgnoringChildren()

        font = wx.Font(96, wx.DEFAULT, wx.NORMAL, wx.NORMAL)
        vbox_top = wx.BoxSizer(wx.VERTICAL)
        vbox_top.Add((10, 10), 1)
        hbox_players = wx.BoxSizer(wx.HORIZONTAL)
        self.team_a = wx.StaticText(self, wx.ID_ANY, "")
        self.team_a.SetFont(font)
        hbox_players.Add((10, 10), 1)
        hbox_players.Add(self.team_a, flag=wx.ALIGN_TOP)
        hbox_players.Add((10, 10), 1)
        colon = wx.StaticText(self, wx.ID_ANY, ":")
        colon.SetFont(font)
        hbox_players.Add(colon, flag=wx.ALIGN_CENTER)
        hbox_players.Add((10, 10), 1)
        self.team_b = wx.StaticText(self, wx.ID_ANY, "")
        self.team_b.SetFont(font)
        hbox_players.Add(self.team_b, flag=wx.ALIGN_TOP)
        hbox_players.Add((10, 10), 1)
        vbox_top.Add(hbox_players, flag=wx.ALL | wx.ALIGN_CENTER | wx.EXPAND)
        vbox_top.Add((10, 10), 1)
        hbox_score = wx.BoxSizer(wx.HORIZONTAL)
        self.score = wx.StaticText(self, wx.ID_ANY, "")
        font = wx.Font(192, wx.DEFAULT, wx.NORMAL, wx.NORMAL)
        self.score.SetFont(font)
        hbox_score.Add((10, 10), 1)
        hbox_score.Add(self.score, flag=wx.ALIGN_CENTER)
        hbox_score.Add((10, 10), 1)
        vbox_top.Add(hbox_score, flag=wx.ALL | wx.ALIGN_CENTER | wx.EXPAND)
        vbox_top.Add((10, 10), 1)
        self.SetSizer(vbox_top)

        self.reset()

    def reset(self):
        self.players = []
        self.match_id = None
        self.goals_a = self.goals_b = 0
        self.update()

    def update(self):
        self.team_a.SetLabel(u"\n".join(unicode(player) for player in self.players[:2]))
        self.team_b.SetLabel(u"\n".join(unicode(player) for player in self.players[2:]))
        self.score.SetLabel(u"{self.goals_a}:{self.goals_a}".format(self=self))
        self.Fit()

    def OnKeyPress(self, event):
        character = unichr(event.GetUniChar())
        print repr(character)
        if character == u"Q":
            sys.exit()
        elif character == u"G":
            self.reset()
        elif character == u"\x08":
            if self.players:
                del self.players[-1]
        elif len(self.players) < 4:
            try:
                player = Player(character)
            except chantal_remote.ChantalError:
                return
            if player not in self.players or True:
                self.players.append(player)
        elif character == u"\r":
            if self.match_id:
                chantal_remote.connection.open("kicker/matches/add/{0}".format(self.match_id), {
                        "player_a_1": self.players[0].username,
                        "player_a_2": self.players[1].username,
                        "player_b_1": self.players[2].username,
                        "player_b_2": self.players[3].username,
                        "goals_a": self.goals_a,
                        "goals_b": self.goals_b,
                        "seconds": int(time.time() - self.start_time),
                        "timestamp": datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                        "finished": True
                        })
                self.reset()
            else:
                self.match_id = chantal_remote.connection.open("kicker/matches/add/", {
                        "player_a_1": self.players[0].username,
                        "player_a_2": self.players[1].username,
                        "player_b_1": self.players[2].username,
                        "player_b_2": self.players[3].username,
                        "goals_a": self.goals_a,
                        "goals_b": self.goals_b,
                        "seconds": 0,
                        "timestamp": datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                        "finished": False
                        })
                self.start_time = time.time()
        elif self.match_id:
            if character == u"s":
                self.goals_a += 1
            elif character == u"y":
                self.goals_a -= 1
            elif character == u"k":
                self.goals_b += 1
            elif character == u"m":
                self.goals_b -= 1

            if self.goals_a < 0:
                self.goals_a = 0
            if self.goals_b < 0:
                self.goals_b = 0
        self.update()


class App(wx.App):

    def OnInit(self):
        chantal_remote.login("kicker", "o843zegzeisztutw7", testserver=True)
        self.frame = Frame()
        self.frame.Show()
        self.SetTopWindow(self.frame)
        return True


app = App()
app.MainLoop()
