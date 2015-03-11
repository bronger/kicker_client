#!/usr/bin/env python
# -*- coding: utf-8 -*-

from __future__ import division

import sys, time, datetime, urllib2, urllib, contextlib
import wx
sys.path.append("/windows/T/Internes/Chantal/remote_client")
from remote_client import chantal_remote


class Player(object):
    def __init__(self, shortkey):
        while True:
            try:
                with connection_sentry():
                    self.username, self.nickname = chantal_remote.connection.open("kicker/player?shortkey={0}".format(
                        urllib.quote_plus(shortkey.encode("utf-8"))))
                break
            except ReloginNecessary:
                pass
    def __unicode__(self):
        return self.nickname if len(self.nickname) < 10 else self.nickname[:8] + "."
    def __eq__(self, other):
        return self.username == other.username
    def __ne__(self, other):
        return not self.__eq__(other)


class ReloginNecessary(Exception):
    pass


@contextlib.contextmanager
def connection_sentry(parent=None):
    def show_error_dialog(error_message):
        dialog = wx.MessageDialog(parent, error_message, caption="Fehler", style=wx.OK | wx.ICON_ERROR)
        dialog.ShowModal()
        dialog.Destroy()
    try:
        yield
    except chantal_remote.ChantalError as error:
        show_error_dialog(u"#{0.error_code}: {0.error_message}".format(error))
        wx.GetApp().ExitMainLoop()
        raise
    except urllib2.URLError as error:
        if error.code == 401:
            # One of those odd logouts
            print "Re-login"
            chantal_remote.login(login, password)
            raise ReloginNecessary
        else:
            show_error_dialog(unicode(error))
        wx.GetApp().ExitMainLoop()
        raise


class Frame(wx.Frame):

    def __init__(self, *args, **keyw):
        super(Frame, self).__init__(None, wx.ID_ANY, size=wx.DisplaySize(), title="Kicker", *args, **keyw)
        self.ShowFullScreen(True)
        panel = wx.Panel(self, wx.ID_ANY, size=(0, 0))
        panel.Bind(wx.EVT_CHAR, self.OnKeyPress)
        panel.SetFocusIgnoringChildren()

        font = wx.Font(48, wx.DEFAULT, wx.NORMAL, wx.NORMAL)
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
        hbox_kicker_numbers = wx.BoxSizer(wx.HORIZONTAL)
        self.kicker_numbers = wx.StaticText(self, wx.ID_ANY, "")
        font = wx.Font(32, wx.DEFAULT, wx.NORMAL, wx.NORMAL)
        self.kicker_numbers.SetFont(font)
        hbox_kicker_numbers.Add((10, 10), 1)
        hbox_kicker_numbers.Add(self.kicker_numbers, flag=wx.ALIGN_CENTER)
        hbox_kicker_numbers.Add((10, 10), 1)
        vbox_top.Add(hbox_kicker_numbers, flag=wx.ALL | wx.ALIGN_CENTER | wx.EXPAND)
        vbox_top.Add((10, 10), 1)
        hbox_goal_value = wx.BoxSizer(wx.HORIZONTAL)
        self.goal_value_text = wx.StaticText(self, wx.ID_ANY, "")
        font = wx.Font(24, wx.DEFAULT, wx.NORMAL, wx.NORMAL)
        self.goal_value_text.SetFont(font)
        hbox_goal_value.Add((10, 10), 1)
        hbox_goal_value.Add(self.goal_value_text, flag=wx.ALIGN_CENTER)
        hbox_goal_value.Add((10, 10), 1)
        vbox_top.Add(hbox_goal_value, flag=wx.ALL | wx.ALIGN_CENTER | wx.EXPAND)
        vbox_top.Add((10, 10), 1)
        self.SetSizer(vbox_top)

        self.timer = wx.Timer(self)
        self.Bind(wx.EVT_TIMER, self.OnTimer, self.timer)
        
        self.match_id = None
        self.reset()
        self.update()

    def reset(self):
        self.players = []
        if self.match_id:
            self.timer.Stop()
            while True:
                try:
                    with connection_sentry(self):
                        chantal_remote.connection.open("kicker/matches/{0}/cancel/".format(self.match_id), {})
                    break
                except ReloginNecessary:
                    pass
        self.match_id = None
        self.goals_a = self.goals_b = 0
        self.error_estimate = 0
        self.goal_value = 0
        self.current_win_team_1 = 0
        self.start_time = None

    def update(self):
        self.team_a.SetLabel(u"\n".join(unicode(player) for player in self.players[:2]))
        self.team_b.SetLabel(u"\n".join(unicode(player) for player in self.players[2:]))
        self.score.SetLabel(u"{self.goals_a}:{self.goals_b}".format(self=self))
        if self.current_win_team_1 is None:
            self.kicker_numbers.SetLabel(u"")
            self.goal_value_text.SetLabel(u"")
        else:
            self.kicker_numbers.SetLabel(u"                {0:+.1f} : {1:+.1f}       ± {2:.1f}".format(
                self.current_win_team_1, -self.current_win_team_1, self.error_estimate))
            self.goal_value_text.SetLabel(u"Torwert: {:.1f}".format(self.goal_value))
        self.Fit()

    def player_allowed(self, player):
        assert len(self.players) <= 3
        if len(self.players) <= 1:
            return True
        two_player_match = self.players[0] == self.players[1]
        if two_player_match:
            if len(self.players) == 2:
                return player not in self.players
            else:
                return player == self.players[2]
        else:
            return player not in self.players

    def get_current_score(self, seconds_ahead=0, goals_ahead=0):
        while True:
            try:
                with connection_sentry(self):
                    current_win_team_1 = \
                            chantal_remote.connection.open("kicker/matches/{0}/edit/".format(self.match_id), {
                                "player_a_1": self.players[0].username,
                                "player_a_2": self.players[1].username,
                                "player_b_1": self.players[2].username,
                                "player_b_2": self.players[3].username,
                                "goals_a": self.goals_a + goals_ahead,
                                "goals_b": self.goals_b,
                                "seconds": int(time.time() - self.start_time) + seconds_ahead,
                                "timestamp": datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                                "finished": False
                            })[2]
                break
            except ReloginNecessary:
                pass
        return current_win_team_1
        
    def OnTimer(self, event):
        future_score = self.get_current_score(seconds_ahead=20)
        plus_one_goal_score = self.get_current_score(goals_ahead=1)
        self.current_win_team_1 = self.get_current_score()
        self.error_estimate = abs(future_score - self.current_win_team_1)
        self.goal_value = abs(plus_one_goal_score - self.current_win_team_1)
        self.update()

    def OnKeyPress(self, event):
        character = unichr(event.GetUniChar())
        if character == u"Q":
            self.reset()
            sys.exit()
        elif character == u"G":
            self.reset()
        elif character == u"!":
            if self.match_id:
                self.timer.Stop()
                while True:
                    try:
                        with connection_sentry(self):
                            delta = chantal_remote.connection.open("kicker/matches/{0}/edit/".format(self.match_id), {
                                    "player_a_1": self.players[0].username,
                                    "player_a_2": self.players[1].username,
                                    "player_b_1": self.players[2].username,
                                    "player_b_2": self.players[3].username,
                                    "goals_a": self.goals_a,
                                    "goals_b": self.goals_b,
                                    "seconds": int(time.time() - self.start_time),
                                    "timestamp": datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                                    "finished": True
                                    })[2]
                        break
                    except ReloginNecessary:
                        pass
                if delta is not None:
                    dialog = wx.MessageDialog(
                        self, u"Die Änderung der Kickernummern der ersten Mannschaft ist {0:+.1f}.".format(delta),
                        caption=u"Änderung Kickernummer", style=wx.OK)
                    dialog.ShowModal()
                    dialog.Destroy()
                self.match_id = None
                self.reset()
        elif character == u"\x1b":  # ESC
            self.reset()
        elif character == u"\x08":  # Backspace
            players = self.players[:-1]
            self.reset()
            self.players = players
        elif self.start_time is not None:
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
        elif len(self.players) < 4:
            try:
                player = Player(character)
            except chantal_remote.ChantalError:
                return
            except urllib2.URLError:
                wx.GetApp().ExitMainLoop()
                raise
            if self.player_allowed(player):
                self.players.append(player)
            if len(self.players) == 4:
                while True:
                    try:
                        with connection_sentry(self):
                            self.match_id, expected_goal_difference = chantal_remote.connection.open("kicker/matches/add/", {
                                    "player_a_1": self.players[0].username,
                                    "player_a_2": self.players[1].username,
                                    "player_b_1": self.players[2].username,
                                    "player_b_2": self.players[3].username,
                                    "goals_a": self.goals_a,
                                    "goals_b": self.goals_b,
                                    "seconds": 0,
                                    "timestamp": datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                                    "finished": False
                                    })[:2]
                        break
                    except ReloginNecessary:
                        pass
                self.update()
                pre_message = u"Die erwartete Tordifferenz ist {0:+.1f}.  ". \
                    format(expected_goal_difference) if expected_goal_difference else u""
                dialog = wx.MessageDialog(self, pre_message + u"Mit „OK“ startet das Spiel.", caption="Spiel starten",
                                          style=wx.OK)
                dialog.ShowModal()
                dialog.Destroy()
                self.timer.Start(5000)
                self.start_time = time.time()
        self.update()


class LoginDialog(wx.Dialog):

    def __init__(self):
        super(LoginDialog, self).__init__(None, wx.ID_ANY, "Login", size=(300, 100))

        vbox_top = wx.BoxSizer(wx.VERTICAL)

        textfields_sizer = wx.FlexGridSizer(2, 2, 5, 5)
        textfields_sizer.Add(wx.StaticText(self, wx.ID_ANY, "Login:"), flag=wx.ALIGN_RIGHT | wx.ALIGN_CENTER_VERTICAL)
        self.login_field = wx.TextCtrl(self)
        self.login_field.SetFocus()
        textfields_sizer.Add(self.login_field, flag=wx.EXPAND)
        textfields_sizer.Add(wx.StaticText(self, wx.ID_ANY, "Passwort:"), flag=wx.ALIGN_RIGHT | wx.ALIGN_CENTER_VERTICAL)
        self.password_field = wx.TextCtrl(self, style=wx.PASSWORD)
        textfields_sizer.Add(self.password_field, flag=wx.EXPAND)
        textfields_sizer.AddGrowableCol(1)
        vbox_top.Add(textfields_sizer, flag=wx.EXPAND | wx.ALL, border=5)

        button_sizer = wx.StdDialogButtonSizer()
        ok_button = wx.Button(self, wx.ID_OK, "Login", pos=(15, 15))
        ok_button.SetDefault()
        cancel_button = wx.Button(self, wx.ID_CANCEL)
        button_sizer.AddButton(ok_button)
        button_sizer.AddButton(cancel_button)
        button_sizer.Realize()
        vbox_top.Add(button_sizer, flag=wx.EXPAND | wx.ALL, border=5)

        self.SetSizer(vbox_top)
        self.Fit()


app = wx.App()

login_dialog = LoginDialog()
result = login_dialog.ShowModal()
if result == wx.ID_OK:
    login, password = login_dialog.login_field.GetValue(), login_dialog.password_field.GetValue()
    login_dialog.Destroy()
    with connection_sentry():
        chantal_remote.login(login, password)
    frame = Frame()
    frame.Show()
    app.SetTopWindow(frame)
    app.MainLoop()
