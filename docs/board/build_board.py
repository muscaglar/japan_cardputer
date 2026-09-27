#!/usr/bin/env python3
"""Builds the concept board page: real screen renders, pronunciation, looks, facts and questions.

Usage: python3 docs/board/build_board.py   (writes docs/board/cardputer-nihongo.html)
"""
import base64
import html
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, "..", "..", "tools"))
import concept_screens as cs  # noqa: E402
SCALE = 4


def png(screen):
    return "data:image/png;base64," + base64.b64encode(screen.png_bytes(SCALE)).decode("ascii")


SCREENS = {name: png(build()) for name, build in cs.IDEAS}
SCREENS.update({name: png(build()) for name, build in cs.PRONUNCIATION})
ROUND2 = {key: [png(cs.themed_home(key)), png(cs.themed_catcher(key)), png(cs.themed_sign(key))] for key in cs.ROUND_TWO}
if cs.problems:
    raise SystemExit("screen problems: %s" % cs.problems)

data = json.load(open(os.path.join(HERE, "content.json"), encoding="utf-8"))


def esc(text):
    return html.escape(text, quote=True)


def lcd(src, alt):
    return '<div class="lcd"><img src="%s" width="240" height="135" alt="%s"></div>' % (src, esc(alt))


def idea_card(idea):
    tags = "".join('<li class="tag tag-%s">%s</li>' % (esc(kind), esc(label)) for kind, label in idea["tags"])
    picks = "".join(
        '<label class="pick"><input type="radio" name="idea-%s" id="idea-%s-%s" value="%s"><span>%s</span></label>'
        % (esc(idea["id"]), esc(idea["id"]), value, value, label)
        for value, label in (("yes", "Want"), ("maybe", "Maybe"), ("no", "Skip")))
    return (
        '<article class="idea" data-idea="%s">%s'
        '<div class="idea-body">'
        '<p class="verdict verdict-%s">%s</p>'
        '<h3><span class="jp" lang="ja">%s</span> %s</h3>'
        '<p class="pitch">%s</p>'
        '<ul class="tags">%s</ul>'
        '<fieldset class="picks"><legend class="sr">Your pick for %s</legend>%s</fieldset>'
        '</div></article>'
    ) % (esc(idea["id"]), lcd(SCREENS[idea["screen"]], idea["alt"]), esc(idea["tier"]), esc(idea["tierLabel"]),
         esc(idea["jp"]), esc(idea["en"]), esc(idea["pitch"]), tags, esc(idea["en"]), picks)


def group_block(group):
    cards = "".join(idea_card(i) for i in data["ideas"] if i["group"] == group["id"])
    return (
        '<section class="line line-%s" aria-labelledby="g-%s">'
        '<header class="line-head"><span class="line-mark" aria-hidden="true"></span>'
        '<div><h3 class="line-title" id="g-%s"><span class="jp" lang="ja">%s</span> %s</h3><p>%s</p></div></header>'
        '<div class="ideas">%s</div></section>'
    ) % (esc(group["id"]), esc(group["id"]), esc(group["id"]), esc(group["jp"]), esc(group["en"]), esc(group["blurb"]), cards)


def question_block(q):
    qid = q["id"]
    parts = ['<div class="q" data-q="%s"><h3 id="q-%s-label">%s</h3>' % (esc(qid), esc(qid), esc(q["ask"]))]
    if q.get("why"):
        parts.append('<p class="why">%s</p>' % esc(q["why"]))
    kind = q["kind"]
    if kind in ("one", "many"):
        input_type = "radio" if kind == "one" else "checkbox"
        parts.append('<div class="opts" role="group" aria-labelledby="q-%s-label">' % esc(qid))
        for value, label in q["options"]:
            parts.append(
                '<label class="opt"><input type="%s" name="q-%s" id="q-%s-%s" value="%s"><span>%s</span></label>'
                % (input_type, esc(qid), esc(qid), esc(value), esc(value), esc(label)))
        parts.append("</div>")
    if q.get("text"):
        parts.append(
            '<label class="free"><span>%s</span><textarea id="q-%s-text" name="q-%s-text" rows="%d" placeholder="%s"></textarea></label>'
            % (esc(q["text"]), esc(qid), esc(qid), q.get("rows", 2), esc(q.get("placeholder", ""))))
    parts.append("</div>")
    return "".join(parts)


def questions(place):
    return "".join(question_block(q) for q in data["questions"] if q.get("place") == place)


def fact_row(fact):
    return '<tr><th scope="row">%s</th><td>%s</td><td class="so">%s</td></tr>' % (
        esc(fact["topic"]), esc(fact["fact"]), esc(fact["means"]))


def stop_block(stop):
    return (
        '<li class="stop"><span class="stop-dot" aria-hidden="true"></span>'
        '<p class="stop-when"><span class="jp" lang="ja">%s</span> %s</p>'
        '<p class="stop-meta">%s</p><p class="stop-what">%s</p></li>'
    ) % (esc(stop["jp"]), esc(stop["en"]), esc(stop["meta"]), esc(stop["what"]))


def layer_block(layer):
    return (
        '<li class="layer"><p class="layer-name"><span class="jp" lang="ja">%s</span> %s</p>'
        '<p class="layer-when">%s</p><p class="layer-what">%s</p></li>'
    ) % (esc(layer["jp"]), esc(layer["en"]), esc(layer["when"]), esc(layer["what"]))


def shot_block(shot):
    return (
        '<figure class="shot">%s<figcaption><strong>%s</strong><span>%s</span></figcaption></figure>'
    ) % (lcd(SCREENS[shot["screen"]], shot["alt"]), esc(shot["title"]), esc(shot["note"]))


def round2_block(look):
    names = ("home screen", "word catcher", "sign drill")
    shots = "".join(lcd(src, "%s look, %s" % (look["en"], names[i])) for i, src in enumerate(ROUND2[look["id"]]))
    return (
        '<section class="look2" aria-labelledby="look2-%s"><header><h3 id="look2-%s"><span class="jp" lang="ja">%s</span> %s</h3>'
        '<p>%s</p></header><div class="look2-shots">%s</div></section>'
    ) % (esc(look["id"]), esc(look["id"]), esc(look["jp"]), esc(look["en"]), esc(look["note"]), shots)


pron = data["pronunciation"]
template = open(os.path.join(HERE, "template.html"), encoding="utf-8").read()
page = (template
        .replace("{{HERO}}", SCREENS["pron_card"])
        .replace("{{STOPS}}", "".join(stop_block(s) for s in data["stops"]))
        .replace("{{LAYERS}}", "".join(layer_block(l) for l in pron["layers"]))
        .replace("{{PRON_SHOTS}}", "".join(shot_block(s) for s in pron["screens"][1:]))
        .replace("{{PRON_OPTIONS}}", "".join(shot_block(s) for s in pron["options"]))
        .replace("{{PRON_QUESTIONS}}", questions("pron"))
        .replace("{{ROUND2}}", "".join(round2_block(l) for l in data["round2"]))
        .replace("{{LOOK_QUESTIONS}}", questions("look"))
        .replace("{{GROUPS}}", "".join(group_block(g) for g in data["groups"]))
        .replace("{{FACTS}}", "".join(fact_row(f) for f in data["facts"]))
        .replace("{{QUESTIONS}}", questions("form"))
        .replace("{{IDEA_IDS}}", json.dumps([i["id"] for i in data["ideas"]]))
        .replace("{{QUESTION_IDS}}", json.dumps([[q["id"], q["kind"], bool(q.get("text"))] for q in data["questions"]]))
        .replace("{{DEFAULTS}}", json.dumps(data["defaults"], ensure_ascii=False)))

if "{{" in page:
    raise SystemExit("unfilled placeholder: " + page[page.index("{{"):page.index("{{") + 40])
out = os.path.join(HERE, "cardputer-nihongo.html")
open(out, "w", encoding="utf-8").write(page)
print(out, "%.0f KB" % (len(page.encode("utf-8")) / 1024))
