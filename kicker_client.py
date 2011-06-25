#!/usr/bin/env python
# -*- coding: utf-8 -*-

import re, os, codecs, sys, time, StringIO, textwrap, platform, webbrowser, shutil, datetime, time
import wx, wx.grid, wx.py.editor, wx.py.editwindow, wx.html, wx.lib.hyperlink
sys.path.append("/home/bronger/src/chantal_ipv/current/remote_client")
import chantal_remote


class Player(object):
    def __init__(self, shortkey):
        self.username, self.nickname = chantal_remote.connection.open("kicker/player?shortkey={0}".format(shortkey))


class Frame(wx.Frame):

    def __init__(self, *args, **keyw):
        super(Frame, self).__init__(None, wx.ID_ANY, size=(600, 600), title="Kicker", *args, **keyw)
        panel = wx.Panel(self, wx.ID_ANY, size=(0, 0))
        panel.Bind(wx.EVT_CHAR, self.OnKeyPress)
        panel.SetFocusIgnoringChildren()
        self.reset()
        self.update()

    def reset(self):
        self.players = []
        self.match_id = None
        self.goals_a = self.goals_b = 0

    def update(self):
        vbox_main = wx.BoxSizer(wx.VERTICAL)
        vbox_main.Add(wx.StaticText(self, wx.ID_ANY, "Super"), flag=wx.ALIGN_CENTER)
        hbox_top = wx.BoxSizer(wx.HORIZONTAL)
        hbox_top.Add(vbox_main, flag=wx.ALL | wx.ALIGN_CENTER)
        self.SetSizer(hbox_top)
        self.Fit()

    def OnKeyPress(self, event):
        character = unichr(event.GetUniChar())
        if character == u"Q":
            sys.exit()
        elif character == u"G":
            self.reset()
        elif character == u"\x08":
            if self.players:
                del self.players[-1]
        elif len(self.players) < 4:
            self.players.append(Player(character))
        elif character == u"\x10":
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


class App(wx.App):

    def OnInit(self):
        chantal_remote.login("kicker", "o843zegzeisztutw7", testserver=True)
        self.frame = Frame()
        self.frame.Show()
        self.SetTopWindow(self.frame)
        return True


app = App()
app.MainLoop()
