# coding=utf-8
# !/usr/bin/env python
# -*- coding: utf-8 -*-

import pygame
from pygame.locals import *
import re
import os
import sys
import platform
import codecs
from decimal import *

pygame.init()
info = pygame.display.Info()
width = info.current_w
height = info.current_h
base_width = 1920.0
base_height = 1080.0
res_ratio_w = base_width / width # Ces deux lignes servent a redimmensionner les images en fonction de la resolution
res_ratio_h = base_height / height

print(res_ratio_w, res_ratio_h)

class Scene:
    def __init__(self, filename, dict_vn):
        # Variables utiles au dialogue
        self.dialog_name = str()
        # Variables contenant des infos sur la scene
        self.static_variables = dict()
        self.dynamic_variables = dict()
        self.image_dict = dict()# Dictionnaire des images chargees
        self.actors = dict()
        self.dialog_lines = list()
        self.current_directory = os.getcwd()
        self.dialog_list = list()
        self.snippet_dialog = list()
        self.snippet = False
        self.filename = filename
        self.dict_choices = dict()
        self.dict_vn = dict_vn
        self.dimw_cadre_choices = 0
        self.dimh_cadre_choices = 0

    def get_file(self, screen):# Methode qui appelle tour a tour chaque methode afin de recuperer les informations du fichier de dialogue
        dialog_file = codecs.open(self.filename, 'r', encoding='utf8')
        self.dialog_list = dialog_file.readlines()
        for i in range(len(self.dialog_list)):
            # On enleve les sauts de lignes a la fin de chaque ligne du fichier ainsi que les espaces a gauche
            self.dialog_list[i] = self.dialog_list[i].rstrip('\n').rstrip('\r').lstrip()
        self.get_meta()
        self.get_variables()
        self.get_choices()
        self.get_images()
        self.get_actors()
        self.get_dialog()
        self.play_dialog(screen)

    def get_meta(self):#Methode qui recupere les metadonnees et les place dans les variables
        line = 0
        meta_line = str()
        while self.dialog_list[line] != "[Meta]":#On se place a la bonne ligne
            line += 1
        while self.dialog_list[line] != "[/Meta]":
            meta_line = self.dialog_list[line]
            if self.dialog_list[line].endswith(';'):
                m = re.match(r'^\$(?P<id>[\w]+):"(?P<var>[\w]*)";$', meta_line)#Regex pour recup nom de var et variable
                if m != None:
                    if m.groupdict()["id"] == "Name":
                        self.dialog_name = m.groupdict()["var"]#On recup le nom du dialogue
                        self.static_variables["dialog_name"] = m.groupdict()["var"]
                else:
                    print("Error reading file line {0}, {1}".format(line, self.dialog_list[line]))
            line += 1

    #Methode qui recupere les variables et les places dans deux dictionnaires : un pour les variables statiques et un
    #pour les variables dynamiques
    def get_variables(self):
        line = 0
        while self.dialog_list[line] != "[Variables]":#On se place a la bonne ligne
            line += 1
        while self.dialog_list[line] != "[/Variables]":
            if self.dialog_list[line].endswith(';'):
                variable_line = self.dialog_list[line]
                if variable_line.startswith('.'):#Dans le cas d'une variable statique
                    m = re.match(r'^\.(?P<var>[\w]+):(?P<value>[\w]+);$', variable_line)
                    if m != None:
                        self.static_variables[m.groupdict()["var"]] = m.groupdict()["value"]#On place la variable dans le dico
                    else:
                        print("var Error reading file line {0}".format(line))
                elif variable_line.startswith('~'):#Dans le cas d'une variable dynamique
                    m = re.match(r'^~(?P<var>[\w]+):(?P<value>[\w]+);$', variable_line)
                    if m != None:
                        self.dynamic_variables[m.groupdict()["var"]] = m.groupdict()["value"]#On place la variable dans le dico
                    else:
                        print("var Error reading file line {0}".format(line))
            line += 1

    def get_choices(self):
        line = 0
        k = 0
        question = tuple()
        choices_var = list()
        list_choices = list()
        while self.dialog_list[line] != "[Choices]":
            line += 1
        while self.dialog_list[line] != "[/Choices]":
            #if self.dialog_list[line].endswith(';'):
            choice_line = self.dialog_list[line]
            if re.match(r'^\{[\w]*\}$', choice_line) is not None: #Si on est dans la categorie d'un choix
                i = line + 1
                num_choice = self.dialog_list[line]
                choice_line = self.dialog_list[i]
                m = re.match(r'^\$(?P<id>[\w]+):"(?P<var>[\w \-éèêëùàç()?.\'><=:,!]*)";$', choice_line, re.UNICODE)#Regex pour recup nom de var et variable
                if m is not None:
                    question = (m.groupdict()["id"],m.groupdict()["var"])
                else:
                    print("Error reading question")
                while re.match(r'^\{[\w]*\}$', choice_line) is None and choice_line != "[/Choices]":#On parcourt les différents choix
                    choice_line = self.dialog_list[i]
                    if re.match(r'^<(?P<var>[\w]+)>$', choice_line):
                        j = i + 1
                        choice_line = self.dialog_list[j]
                        while re.match(r'^<(?P<var>[\w \-éèêëùàç()?.\'"><=]+)>$', choice_line, re.UNICODE) is None and choice_line != "[/Choices]" and re.match(r'^\{[\w]*\}$', choice_line) is None:
                            choice_line = self.dialog_list[j]
                            if choice_line.endswith(';'):
                                m = re.match(r'^\$(?P<id>[\w]+):("?(?P<var>[\w \-éèêëùàç()?.\'"><=:,!]*)"?);$', choice_line, re.UNICODE)
                                if m is not None:
                                    choices_var.append((m.groupdict()["id"], m.groupdict()["var"].strip('"')))
                                else:
                                    print("Error reading var choices")
                            j += 1
                            choice_line = self.dialog_list[j]
                        list_choices.append(choices_var)
                        choices_var = list()
                        self.dict_choices[num_choice] = (question, list_choices)
                        k += 1
                    i += 1
            list_choices = list()
            line += 1
        for i,j in self.dict_choices.items():
            print("cle:{0} valeur: {1}".format(i,j))


    #Methode qui recupere les images et les ID et les charge dans un dictionnaire
    def get_images(self):
        line = 0
        while self.dialog_list[line] != "[Images]":#On se place a la bonne ligne
            line += 1
        while self.dialog_list[line] != "[/Images]":
            if self.dialog_list[line].endswith(';'):
                image_line = self.dialog_list[line]
                if platform.system() == "Linux":
                    image_line= image_line.replace("\\", "/")
                    m = re.match(r'^\$(?P<id>[\w]+):"(?P<path>(/[\w]+)*\.(png|jpg|gif))";$', image_line)
                else:
                    m = re.match(r'^\$(?P<id>[\w]+):"(?P<path>(\\[_\w]+)*\.(png|jpg|gif))";$', image_line)#Regex qui recup id et path
                if m != None:
                    self.image_dict[m.groupdict()["id"]] = \
                        pygame.image.load(self.current_directory + m.groupdict()["path"]).convert_alpha()#Charge les images dans le dico
                    #Cette ligne redimensionne les images en fonction de la resolution
                    #self.image_dict[m.groupdict()["id"]] = pygame.transform.scale(self.image_dict[m.groupdict()["id"]], ())
                    self.image_dict[m.groupdict()["id"]] = \
                        pygame.transform.smoothscale(self.image_dict[m.groupdict()["id"]],
                                               (int(self.image_dict[m.groupdict()["id"]].get_width() / res_ratio_w),
                                                int(self.image_dict[m.groupdict()["id"]].get_height() / res_ratio_h)))
                else:
                    print("img Error reading file line {0}".format(line))
            line += 1
        self.dimw_cadre_choices = self.image_dict["cadre_choices"].get_width()
        self.dimh_cadre_choices = self.image_dict["cadre_choices"].get_height()

    #Methode qui recupere les informations sur les acteurs et creer les objets Actor necessaires
    def get_actors(self):
        line = 0
        while self.dialog_list[line] != "[Actors]":#On se place a la bonne ligne
            line += 1
        while self.dialog_list[line] != "[/Actors]":
            actor_line = self.dialog_list[line]
            if re.match(r'^\{[\w]*\}$', actor_line) is not None: #Si on est dans la categorie d'un acteur
                actor_name = str()
                actor_image = str()
                actor_icon = str()
                actor_behaviour = dict()
                actor_font = str()
                actor_color = tuple()
                actor_position = tuple()
                actor_id = actor_line
                i = line + 1
                actor_line = self.dialog_list[i]
                while re.match(r'^\{[\w]*\}$', actor_line) is None and actor_line != "[/Actors]":#On parcourt les attributs d'un acteurs et on les stockes
                    if actor_line.count("Name"):
                        m = re.match(r'^\$Name:"(?P<var>[\w]*)";$', actor_line)
                        if m != None:
                            actor_name = m.groupdict()["var"]#On stock le nom de l'acteur actuel
                        else:
                            print("name error reading file")
                    elif actor_line.count("Icon"):
                        m = re.match(r'^\$Icon:\$(?P<id>[\w]+);$', actor_line)
                        if m != None:
                            actor_icon = m.groupdict()["id"]#On stocke son icone
                        else:
                            print("icon Error reading file line {0}".format(i))
                    elif actor_line.count("Behaviour"):
                        split_line = actor_line.split(',')
                        for k in range(0, len(split_line)):
                            m = re.match(r'^(\$Behaviour:\[)?"(?P<var>[\w]+)":\$(?P<value>[\w]+)\]?;?$', split_line[k])
                            if m != None:
                                actor_behaviour[m.groupdict()["var"]] = m.groupdict()["value"]#On stocke les images de ses comportements
                            else:
                                print("behav Error reading file line {0}".format(i))
                    elif actor_line.count("Position"):
                        m = re.match(r'^\$Position:\((?P<x>[0-9]+),(?P<y>[0-9]+)\);$', actor_line)
                        if m != None:
                            actor_position = (int(m.groupdict()["x"]) / res_ratio_w, int(m.groupdict()["y"]) / res_ratio_h)#On stocke sa position de depart
                        else:
                            print("Error reading file line {0}".format(i))
                    elif actor_line.count("Font"):
                        m = re.match(r'^\$Font:"(?P<font>[\w]+)";$', actor_line)
                        if m != None:
                            actor_font = m.groupdict()["font"]#on stocke sa police
                        else:
                            print("font Error reading file line {0}".format(i))
                    elif actor_line.count("Color"):
                        m = re.match(r'^\$Color:\((?P<r>[0-9]{1,3}),(?P<g>[0-9]{1,3}),(?P<b>[0-9]{1,3})\);$', actor_line)
                        if m != None:
                            actor_color = (int(m.groupdict()["r"]),int(m.groupdict()["g"]),int(m.groupdict()["b"]))#On stocke la couleur de sa police
                        else:
                            print("color Error reading file line {0}".format(i))
                    i += 1
                    actor_line = self.dialog_list[i]
                self.actors[actor_id] = Actor(actor_name, actor_image, actor_icon, actor_behaviour, actor_font, actor_color, self.dict_choices, actor_position)#Creation de l'objet acteur
            line += 1

    # Methode qui range les lignes de dialogue dans une liste
    def get_dialog(self):
        line = 0
        while self.dialog_list[line] != "[Dialogue]":
            line += 1
        while self.dialog_list[line] != "[/Dialogue]":
            if self.dialog_list[line].endswith(";"):
                self.dialog_lines.append(self.dialog_list[line])
            line += 1

    # Methode qui lit et interpretre chaque ligne du dialogue, les actions a l'ecran vont partir de cette boucle
    def play_dialog(self, screen):
        lenn = len(self.dialog_lines)
        time_to_sleep = 0
        j = 0
        var = None
        while j < lenn:
            if self.dialog_lines[j].endswith(";"):
                current_line = self.dialog_lines[j]
                if current_line.startswith("Scene"):#Le cas ou une methode de Scene est utilisee
                    m = re.match(r'^Scene(?P<action>\.[\w]+\()(?P<var>("|\{)?[\w]+("|\})?)\);$', current_line)#On recup l'action a faire et les variable
                    if m != None:
                        if m.groupdict(m.groupdict()["action"] == "visible"):
                            self.visible(m.groupdict()["var"])
                    else:
                        print("Error reading dialog")
                    self.update(screen, time_to_sleep)
                elif current_line.startswith('{'):#Le cas ou une methode de Actor est utilisee
                    #La ligne ci dessous recup l'acteur concerne et la methode demandee
                    m = re.match(r'^(?P<id_actor>\{[\w]+\})\.(?P<met>[\w]*)\("?(?P<var>([\w| .?!,\'{}éèàçù]*)*)"?\);$', current_line, re.UNICODE)# a revoir en fonction des caracteres utilises
                    if m != None:
                        if m.groupdict()["met"].count("say") or m.groupdict()["met"].count("think"):#Si l'acteur parle ou pense
                            l = re.match(r'^\.say\("(?P<say>([\w]*[| .?!,\'\\]*)*)"(, ?"[\w]*")?\)$', m.groupdict()["met"])
                            if l != None:
                                word_number = len(l.groupdict()["say"].split(" "))
                                time_to_sleep = word_number * 300 + 700#Calcul du temps d'affichage du texte
                        if m.groupdict()["met"] == "say":
                            var = self.actors[m.groupdict()["id_actor"]].say(m.groupdict()["var"])
                        elif m.groupdict()["met"] == "choice":
                            var = self.actors[m.groupdict()["id_actor"]].choice(m.groupdict()["var"])
                            var.set_cadre(self.image_dict["cadre_choices"])
                            var.set_cadre_hover(self.image_dict["cadre_choices_hover"])
                        elif m.groupdict()["met"] == "free":
                            var = self.actors[m.groupdict()["id_actor"]].free()
                        elif m.groupdict()["met"] == "set_behaviour":
                            var = self.actors[m.groupdict()["id_actor"]].set_behaviour(m.groupdict()["var"])
                        elif m.groupdict()["met"] == "move":
                            var = self.actors[m.groupdict()["id_actor"]].move(m.groupdict()["var"])
                        elif m.groupdict()["met"] == "think":
                            print(m.groupdict()["var"])
                            var = self.actors[m.groupdict()["id_actor"]].think(m.groupdict()["var"])
                        #if var is not None and var.get_object() == "DialogType" and var.get_type() == "choice":

                        self.update(screen, time_to_sleep, m.groupdict()["id_actor"], var)#Affichage des modifications
                        if self.snippet:
                            print("lol")
                            for i in range(0,len(self.snippet_dialog)):
                                self.dialog_lines.insert(j + i + 1, self.snippet_dialog[i])
                            lenn = len(self.dialog_lines)
                            self.snippet = False
                    else:
                        print("Error reading dialog")
                        print(current_line)
            j += 1

    #Fonction qui gere l'affichage des textes et des images
    def update(self, screen, time_to_sleep, speaking_actor = None,  var = None):
        continuer = 1
        time_before = pygame.time.get_ticks()
        time_after = time_before
        #Cette boucle permet l'affichage en continue de toutes les images et l'insertion d'animation, on sort de cette boucle si
        #le temps d'affichage est termine, si l'utilisateur a effectue l'action qu'il devait faire. A chaque etape du dialogue on rentre dans cette boucle
        while continuer:
            screen.blit(self.image_dict["background"], (0,0))
            for actor in self.actors.values():
                if actor.is_visible():
                    screen.blit(self.image_dict[actor.get_image_behaviour()], actor.get_pos())
            screen.blit(self.image_dict["cadre"], (0, height - self.image_dict["cadre"].get_height()))
            if var is not None and var.get_object() == "DialogType" and (self.actors[speaking_actor].is_speaking() or self.actors[speaking_actor].is_thinking()):
                if var.get_type == 'choice' and not var.is_hovering():
                    var.display_line(self.image_dict["cadre"].get_height(), screen)
                if var.get_type != 'choice':
                    var.display_line(self.image_dict["cadre"].get_height(), screen)
                screen.blit(self.image_dict[self.actors[speaking_actor].get_icon()], (0, height - self.image_dict["cadre"].get_height()))
            elif var is not None and var.get_object() == "DialogType" and self.actors[speaking_actor].is_writing():
                screen.blit(self.image_dict[self.actors[speaking_actor].get_icon()], (0, height - self.image_dict["cadre"].get_height()))
            if var != None:
                continuer = self.get_continue(time_to_sleep, time_before, time_after, var, screen)
            else:
                continuer = 0
            pygame.display.update()
            time_after = pygame.time.get_ticks()
        if var is not None and var.get_object() == "DialogType":
            self.actors[speaking_actor].stop_speaking()
            self.actors[speaking_actor].stop_thinking()


    def get_continue(self, time_to_sleep, time_before, time_after, var, screen):
        #continuer_time = True
        line_before = 0
        choice = 0
        #if time_after - time_before > time_to_sleep:
            #continuer_time = False
        events = pygame.event.get()
        for ev in events:
            if ev.type == pygame.KEYDOWN and pygame.key.name(ev.key) == "escape":
                pygame.quit()
                sys.exit(0)
        continue_dialog = self.handle_type(var, events)
        return continue_dialog

    def handle_type(self, var, events):
        continue_dialog = True
        line_before = 0
        action = ""

        if var is not None and var.get_object() == "DialogType":
            if var.get_type() == "normal" or var.get_type() == "think":
                for ev in events:
                    if ev.type == pygame.MOUSEBUTTONDOWN:
                        continue_dialog = False
            elif var.get_type() == "choice":
                var.not_hovering()
                info = var.get_info()
                mouse_pos = pygame.mouse.get_pos()
                mouse_posx = mouse_pos[0]
                mouse_posy = mouse_pos[1]
                for i in range(len(info)):
                    posx = info[i][0]
                    posy = info[i][1]
                    if mouse_posx > posx and mouse_posx < posx + self.dimw_cadre_choices and mouse_posy > posy and mouse_posy < posy + self.dimh_cadre_choices:
                        var.display_line_bright(screen, i, line_before)
                        var.reformat()
                        for ev in events:
                            if ev.type == pygame.MOUSEBUTTONDOWN:
                                continue_dialog = False
                                continuer_time = False
                                self.filename = self.dict_choices[var.get_key()]
                                for l in self.dict_choices[var.get_key()]:
                                    k = l[i]
                                    for u in k:
                                        if u[0] == 'action':
                                            action = u[1]
                                m = re.match(r'^(?P<met>[\w]*)\("(?P<var>[\w.]*)"\)$', action)
                                if m is not None:
                                    if m.groupdict()["met"] == "loadSnippet":
                                        self.loadSnippet(m.groupdict()["var"])
                                        self.snippet = True
                                        continue_dialog = 0
                                m = re.match(r'^(?P<name>[\w]*)=(?P<var>[\w.()"]*)$', action)
                                if m is not None:
                                    print(m.groupdict()["name"], m.groupdict()["var"])
                                    self.dict_vn[m.groupdict()["name"]] = m.groupdict()["var"]
                    line_before += info[i][2]
            elif var.get_type() == "free":
                continue_dialog = var.get_char(events)
                var.display_sentence(self.image_dict["cadre"].get_height(), screen)

        return continue_dialog

    def loadSnippet(self, filename):
        file = codecs.open(filename, 'r', encoding='utf8')
        self.snippet_dialog = file.readlines()
        print(self.snippet_dialog)
        for i in range(0, len(self.snippet_dialog)):
            self.snippet_dialog[i] = self.snippet_dialog[i].rstrip('\n').rstrip('\r')
            if not self.snippet_dialog[i].endswith(";"):
                self.snippet_dialog.pop(i)
        print(self.snippet_dialog)

    def get_new_file(self, filename):
        file = open(filename)
        self.dialog_lines = file.readlines()
        for i in range(len(self.dialog_lines)):
            self.dialog_lines[i] = self.dialog_lines[i].rstrip("\n")

    def visible(self, actor_id):
        self.actors[actor_id].set_visible()

    def get_tuple_choice(self, key):
        return self.dict_choices[key]



class Actor:
    def __init__(self, name, image, icon, behaviour, font, color_font, dict_choices, position = (0,0)):
        self.name = name
        self.image = image
        self.icon = icon#icone
        self.behaviour = behaviour#dictionnaire des comportements propre a l'acteur
        self.current_behaviour = "idle"
        self.font = pygame.font.SysFont(font, 18)
        self.color_font = color_font
        self.visible = False#visible ou pas sur la scene
        self.name_blit = self.font.render(self.name, True, self.color_font)
        self.speaking = False
        self.position = position
        self.max_line_lenght = 112
        self.thinking = False
        self.writing = False
        self.dict_choices = dict_choices

    def set_visible(self):
        self.visible = True

    def set_not_visible(self):
        self.visible = False

    def is_writing(self):
        return self.writing

    def stop_writing(self):
        self.writing = False

    def get_pos(self):
        return self.position

    def get_image(self):
        return self.image

    def get_icon(self):
        return self.icon

    def get_name(self):
        return self.name_blit

    def get_font(self):
        return self.font

    def get_color_font(self):
        return self.color_font

    def is_visible(self):
        return self.visible

    def is_speaking(self):
        return self.speaking

    def stop_speaking(self):
        self.speaking = False

    def set_behaviour(self, behav):
        self.need_fondu = True
        self.current_behaviour = behav
        return None
    def get_need_fondu(self):
        return self.need_fondu
    def get_image_behaviour(self):
        return self.behaviour[self.current_behaviour]

    def say(self, string):
        self.speaking = True
        text = DialogType(self, string, "normal")
        text.format_text()
        return text

    def choice(self, string):
        question = ""
        for i in self.dict_choices[string]:
            if i[0] == 'display':
                question = i[1]

            #Possibilité de rajouter des appels de méthodes ici.
        list_to_send = list()
        for i in self.dict_choices[string][1]:
            for j in  i:
                if j[0] == 'display':
                    list_to_send.append(j[1])
        text = ChoiceType(self, list_to_send, "choice", question, string)
        text.format_text()
        return text

    def free(self):
        self.writing = True
        text = FreeType(self, "", "free")
        return text

    def is_thinking(self):
        return self.thinking

    def stop_thinking(self):
        self.thinking = False

    def think(self, string):
        self.thinking = True
        text = ThinkType(self, string, "think")
        text.format_text()
        return text

    def move(self, string):
        split = string.split(",")
        x = int(split[0]) / res_ratio_w
        y = int(split[1]) / res_ratio_h
        self.position = (x, y)

class DialogType:
    def __init__(self, actor_speaking, text, type, question = None, key = None):
        self.actor_speaking = actor_speaking
        self.speaker_name = self.actor_speaking.get_name()
        self.color_font = self.actor_speaking.get_color_font()
        self.type = type
        self.object = "DialogType"
        if self.type == 'normal':
            self.font = self.actor_speaking.get_font()
            self.font.set_italic(False)
        elif self.type == 'think':
            self.font = self.actor_speaking.get_font()
            self.font.set_italic(True)
        elif self.type == 'free':
            self.font = self.actor_speaking.get_font()
            self.font.set_italic(False)
            self.font = self.actor_speaking.get_font()
            self.color_font = (255,255,255)
        elif self.type == 'choice':
            self.font = pygame.font.SysFont('Arial', 22)
            self.color_font_choices = (143,133,123)
            self.choice_cadre = pygame.Surface
            self.key = key
            self.hovering = False
            self.posx_cadre_choices = 0
            self.choice_cadre_hover = pygame.Surface
        self.text_lines = list()
        self.text = text
        self.max_line_lenght = 112
        self.posx_lines = list()
        self.posy_lines = list()
        self.lines = list()
        self.info_lines = list()
        if question is not None:
            self.question = self.actor_speaking.say(question)

    def split_line(self, string):
        split_line = list()
        i = 0
        split_line.append(string)
        if len(string) > self.max_line_lenght:
            while len(split_line[i]) > self.max_line_lenght:
                max_lenght_prov = self.max_line_lenght
                while not split_line[i][:max_lenght_prov].endswith(" "):
                    max_lenght_prov -= 1
                split_line.append(split_line[i][max_lenght_prov:])
                split_line[i] = split_line[i][:max_lenght_prov]
            i += 1
        return split_line

    def display_line(self, posy_cadre, screen):
        leen = len(self.text_lines)
        self.posx_lines = list(range(leen))
        self.posy_lines = list(range(leen))
        for i in range(leen):
            self.posx_lines[i] = (width / 2 - self.text_lines[i].get_width() / 2)
            self.posy_lines[i] = (height - posy_cadre + 50 + i * 18)
            screen.blit(self.text_lines[i], (self.posx_lines[i], self.posy_lines[i]))
        screen.blit(self.speaker_name, (width / 2 - self.speaker_name.get_width() / 2, height - posy_cadre + 14))

    def format_text(self):
        self.lines = self.split_line(self.text)
        for i in range(len(self.lines)):
            self.text_lines.append(self.font.render(self.lines[i], True, self.color_font))


    def get_type(self):
        return self.type

    def get_object(self):
        return self.object


class ChoiceType(DialogType):

    def display_line(self, posy_cadre, screen):
        leen = len(self.text_lines)
        self.question.display_line(posy_cadre, screen)
        self.posx_lines = list(range(leen))
        self.posy_lines = list(range(leen))
        for i in range(leen):
            self.posx_lines[i] = width / 2 - self.text_lines[i].get_width() / 2
            self.posy_lines[i] = (height - posy_cadre) / 2 + 50 * i
        for i in range(leen):
            screen.blit(self.choice_cadre, (self.posx_cadre_choices, self.posy_lines[i]))
            screen.blit(self.text_lines[i], (self.posx_lines[i], self.posy_lines[i] + (self.choice_cadre.get_height() / 2 - self.text_lines[i].get_height() / 2)))
            #screen.blit(self.text[i], (self.posx_lines[i], self.posy_lines[i]))

        screen.blit(self.speaker_name, (width / 2 - self.speaker_name.get_width() / 2, height - posy_cadre + 14))

    def format_text(self):
        for i in self.text:
            self.lines.append(self.split_line(i))
        for i in self.lines:
            if platform.system() == "Linux":
                i[0] = '• '.decode('utf-8') + i[0]
            else:
                i[0] = '• ' + i[0]

            for j in i:
                self.text_lines.append(self.font.render(j, True, self.color_font_choices))

    def set_cadre(self, cadre):
        self.choice_cadre = cadre
        self.posx_cadre_choices = width / 2 - self.choice_cadre.get_width() / 2

    def set_cadre_hover(self, cadre):
        self.choice_cadre_hover = cadre

    def reformat(self):
        k = 0
        for i in range(len(self.lines)):
            for j in range(len(self.lines[i])):
                self.text_lines[k] = (self.font.render(self.lines[i][j], True, self.color_font_choices))
                k += 1

    def get_info(self):
        k = 0
        self.info_lines = list(range(len(self.lines)))
        for i in range(len(self.lines)):
            self.info_lines[i] = (self.posx_cadre_choices, self.posy_lines[k], len(self.lines[i]))
            k += len(self.lines[i])
        return self.info_lines

    def get_key(self):
        return self.key

    def display_line_bright(self, screen, i, line_before):
        self.hovering = True
        for j in range(len(self.lines[i])):
            screen.blit(self.choice_cadre_hover, (self.posx_cadre_choices, self.posy_lines[line_before + j]))
            self.text_lines[j] = (self.font.render(self.lines[i][j], True, self.color_font_choices))
            screen.blit(self.text_lines[j], (self.posx_lines[line_before + j], self.posy_lines[line_before + j] + (self.choice_cadre.get_height() / 2 - self.text_lines[line_before + j].get_height() / 2)))

    def is_hovering(self):
        return self.hovering

    def not_hovering(self):
        self.hovering = False

class FreeType(DialogType):

    def get_char(self, events):
        key = str()
        for ev in events:
            if ev.type == pygame.KEYDOWN:
                key = pygame.key.name(ev.key)
                if platform.system() == "Windows":
                    if key == "a":
                        key = "q"
                    elif key == "q":
                        key = "a"
                    elif key == "w":
                        key = "z"
                    elif key == "z":
                        key = "w"
                    elif key == ";":
                        key = "m"
                    elif key == "m":
                        key = ","
                if key == "backspace" and len(self.text) >= 1:
                    self.text = self.text[:len(self.text) - 1]
                if key == "space":
                    self.text = self.text + " "
                elif key == "return":
                    return False
        if len(key) is 1:
            if ord(key) >= ord("a") and ord(key) <= ord("z"):
                self.text += key
        elif key >= "[0]" and key <= "[9]":
            self.text += key.lstrip("[").rstrip("]")
        return True


    def display_sentence(self, posy_cadre, screen):
        self.text_lines = self.font.render(self.text, True, self.color_font)
        self.posx_lines = (width / 2 - self.text_lines.get_width() / 2)
        self.posy_lines = (height - posy_cadre + 50)
        screen.blit(self.text_lines, (self.posx_lines, self.posy_lines))
        screen.blit(self.speaker_name, (width / 2 - self.speaker_name.get_width() / 2, height - posy_cadre + 14))

class ThinkType(DialogType):

    def display_line(self, posy_cadre, screen):
        leen = len(self.text_lines)
        self.posx_lines = list(range(leen))
        self.posy_lines = list(range(leen))
        for i in range(leen):
            self.posx_lines[i] = (width / 2 - self.text_lines[i].get_width() / 2)
            self.posy_lines[i] = (height - posy_cadre + 50 + i * 18)
            screen.blit(self.text_lines[i], (self.posx_lines[i], self.posy_lines[i]))



screen = pygame.display.set_mode((width, height), pygame.FULLSCREEN)
dict_vn = dict()
dialog = Scene("vn.msm", dict_vn)
dialog.get_file(screen)
