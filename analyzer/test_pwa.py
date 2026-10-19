"""The PWA's static files. The browser-side logic of history.js is checked with Node when it is installed."""

import json
import shutil
import subprocess
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from app import app

client = TestClient(app)
STATIC = Path(__file__).parent / "static"


def test_history_script_is_served_and_cached():
    assert client.get("/history.js").status_code == 200
    assert '<script src="history.js"></script>' in client.get("/").text
    assert '"history.js"' in (STATIC / "sw.js").read_text()


@pytest.mark.skipif(not shutil.which("node"), reason="Node.js is not installed")
def test_history_helpers():
    script = f"""
    const h = require({json.dumps(str(STATIC / "history.js"))});
    const out = {{
      keep: h.KEEP,
      big: h.fitScale(4000, 3000, 2048),
      small: h.fitScale(1000, 800, 2048),
      drop: h.idsToDrop([{{id: "a", time: 1}}, {{id: "b", time: 4}}, {{id: "c", time: 3}}, {{id: "d", time: 2}}], 3),
      dropDefault: h.idsToDrop(Array.from({{length: 102}}, (_, i) => ({{id: "e" + i, time: i}}))),
      none: h.idsToDrop([{{id: "a", time: 1}}, {{id: "b", time: 2}}]),
    }};
    console.log(JSON.stringify(out));
    """
    r = subprocess.run(
        ["node", "-e", script], capture_output=True, text=True, check=True
    )
    out = json.loads(r.stdout)
    assert out["keep"] == 100
    assert out["big"] == pytest.approx(2048 / 4000)
    assert out["small"] == 1
    assert out["drop"] == ["a"]  # the oldest beyond the newest 3
    assert out["dropDefault"] == ["e1", "e0"]  # by default the newest 100 stay
    assert out["none"] == []


def test_result_script_is_served_and_cached():
    assert client.get("/result.js").status_code == 200
    html = client.get("/").text
    assert '<script src="result.js"></script>' in html
    assert html.index('src="result.js"') < html.index(
        'src="app.js"'
    )  # app.js uses BgResult when it loads
    assert '"result.js"' in (STATIC / "sw.js").read_text()


def _result_js(expr: str):
    """Evaluate expr in Node with result.js loaded as R."""
    script = f"const R = require({json.dumps(str(STATIC / 'result.js'))}); console.log(JSON.stringify({expr}));"
    return json.loads(
        subprocess.run(
            ["node", "-e", script], capture_output=True, text=True, check=True
        ).stdout
    )


_RESULT = {
    "summary": "手前が有利",
    "game_over": False,
    "on_roll": "white",
    "favourite": "white",
    "plies": 2,
    "position_id": "4HPwATDgc/ABMA",
    "pips": {"white": 140, "black": 167, "leader": "white", "difference": 27},
    "probabilities": {
        "white": {"win": 80.0, "gammon": 30.0, "backgammon": 1.0},
        "black": {"win": 20.0, "gammon": 3.0, "backgammon": 0.1},
    },
    "equity": {"white": 0.7, "black": -0.7},
    "moves": [{"move": "bar/22* 13/8(2) 6/off", "equity": 0.5}],
    "cube": None,
}


def test_on_roll_label_follows_the_dice():
    # TODO-042: the label app.js rewrites ("振った人" with dice in, "次に振る人" without) is there
    assert (
        '<span class="opt-label" id="onroll-label">次に振る人</span>'
        in client.get("/").text
    )
    assert "BgResult.rollWho(rolled(s))" in (STATIC / "app.js").read_text()


@pytest.mark.skipif(not shutil.which("node"), reason="Node.js is not installed")
def test_result_words():
    out = _result_js("""{
      who: [R.rollWho([3, 1]), R.rollWho(null)],
      esc: R.esc('<a href="x">&</a>'),
      move: R.moveToSpeech("bar/22* 13/8(2) 6/off"),
      kana: R.moveToSpeech("25/20 10/4 17/off"),
      via: ["24/18*/13", "24/18*/13(2)", "24/18*/13*", "6/4*/off"].map(R.moveToSpeech),
    }""")
    assert out["who"] == ["振った", "次に振る"]
    assert out["esc"] == "&lt;a href=&quot;x&quot;&gt;&amp;&lt;/a&gt;"
    assert (
        out["move"]
        == "バーからにじゅうにでヒット、じゅうさんからはちへに枚、ろくから上がり"
    )
    assert (
        out["kana"] == "にじゅうごからにじゅう、じゅうからよん、じゅうななから上がり"
    )  # TODO-132: no bare digits
    # TODO-166: a hit on the way is said at the point, then the move goes on from there
    assert out["via"] == [
        "にじゅうよんからじゅうはちでヒットして、じゅうさんへ",
        "にじゅうよんからじゅうはちでヒットして、じゅうさんへに枚",
        "にじゅうよんからじゅうはちでヒットして、じゅうさんでヒット",
        "ろくからよんでヒットして、上がり",
    ]


@pytest.mark.skipif(not shutil.which("node"), reason="Node.js is not installed")
def test_win_table_splits_gammons():
    # TODO-128: gnubg's gammon includes backgammons; the rows under 勝率 don't overlap and add up to it
    html = _result_js(f"R.html({json.dumps(_RESULT)}, null)")
    assert "うち" not in html
    assert '<td class="sub">シングル勝ち</td><td>50%</td><td>17%</td>' in html
    assert '<td class="sub">ギャモン勝ち</td><td>29%</td><td>2.9%</td>' in html
    assert '<td class="sub">バックギャモン勝ち</td><td>1%</td><td>0.1%</td>' in html
    # rounded like the server (0.4 - 0.1 is not 0.3 in floats), never below 0 (each number is rounded on its own)
    r = {
        **_RESULT,
        "probabilities": {
            **_RESULT["probabilities"],
            "black": {"win": 0.3, "gammon": 0.4, "backgammon": 0.1},
        },
    }
    html = _result_js(f"R.html({json.dumps(r)}, null)")
    assert '<td class="sub">シングル勝ち</td><td>50%</td><td>0%</td>' in html
    assert '<td class="sub">ギャモン勝ち</td><td>29%</td><td>0.3%</td>' in html


@pytest.mark.skipif(not shutil.which("node"), reason="Node.js is not installed")
def test_result_headings_say_when_the_numbers_are_for():
    # TODO-169: the win table is before the roll, the candidate moves are after moving by this roll
    out = _result_js(f"""{{
      rolled: R.html({json.dumps(_RESULT)}, [3, 1]),
      plain: R.html({{...{json.dumps(_RESULT)}, moves: null}}, null),
    }}""")
    rolled, plain = out["rolled"], out["plain"]
    assert (
        rolled.index("<h3>この目で動かした後</h3>")
        < rolled.index('<ol class="moves">')
        < rolled.index("<h3>ダイスを振る前</h3><table>")
    )
    assert "この目で動かした後" not in plain  # no dice: no candidate moves
    assert "<h3>ダイスを振る前</h3><table>" in plain


@pytest.mark.skipif(not shutil.which("node"), reason="Node.js is not installed")
def test_speech_reads_who_rolls_next_first():
    # TODO-052: without a best move, who rolls next ("次は…の番です") is the first thing read aloud
    r = json.dumps(_RESULT)
    out = _result_js(f"""{{
      noDice: R.speechText({r}, null),
      dice: R.speechText({r}, [3, 1]),
      take: R.speechText({{...{r}, moves: null, cube: {{question: "take", doubler: "black", taker: "white", value: 1, take: true, double: true}}}}, null),
      tooGood: R.speechText({{...{r}, moves: null, cube: {{question: "double", doubler: "white", taker: "black", value: 1, take: false, double: false, too_good: true}}}}, null),
      over: R.speechText({{...{r}, game_over: true}}, null),
      double: R.speechText({{...{r}, moves: null, cube: {{question: "double", doubler: "white", taker: "black", value: 1, take: true, double: true}}}}, null),
      noDouble: R.speechText({{...{r}, moves: null, cube: {{question: "double", doubler: "white", taker: "black", value: 1, take: true, double: false}}}}, null),
      none: R.speechText({{...{r}, moves: [], luck: -0.7}}, [6, 6]),
      sure: R.speechText({{...{r}, probabilities: {{...{r}.probabilities, white: {{win: 95, gammon: 10}}}}}}, null),
    }}""")
    # TODO-106: spoken without "の人"; a cube decision names the side itself, so who rolls is not read
    assert out["noDice"].startswith("次は白の番です。")
    assert out["noDice"].count("の番です。") == 1
    assert out["dice"].startswith(
        "白の さん いち の最善手は、バーからにじゅうにでヒット"
    )
    assert "番です" not in out["dice"]
    assert (
        "かなり有利" in out["dice"]
        and "ギャモン勝ちの見込み" in out["dice"]
        and "ピップ数では白が大きくリード" in out["dice"]
    )
    assert out["take"].startswith(
        "ダブル、テイク。黒のダブルに、白はテイクです。"
    )  # TODO-166: the players' words first
    assert out["tooGood"].startswith(
        "トゥーグッド、パス。白はダブルせず、ギャモンを狙うほうがよいです。"
    )
    assert out["over"] == "白の勝ちで、ゲームは終わっています。"
    assert out["double"].startswith(
        "ダブル、テイク。白はダブルすべきで、黒はテイクです。"
    )
    assert out["noDouble"].startswith(
        "ノーダブル、テイク。白はまだダブルしないほうがよいです。"
    )
    assert out["none"].startswith(
        "白の ろく ろく は、とても悪い目です。動かせる手がありません。"
    )
    assert "白がほぼ勝ちです。" in out["sure"]


@pytest.mark.skipif(not shutil.which("node"), reason="Node.js is not installed")
def test_result_html():
    r = json.dumps(_RESULT)
    cube = {
        "question": "double",
        "doubler": "white",
        "taker": "black",
        "value": 1,
        "take": False,
        "double": True,
        "too_good": False,
        "proper": "Double, pass",
        "equity": {"no_double": 0.5, "double_take": 1.2, "double_pass": 1.0},
    }
    lead = {
        "equity": {"no_double": 0.6, "double_take": 0.5, "double_pass": 1.0}
    }  # no double is better
    out = _result_js(f"""{{
      moves: R.html({r}, [3, 1]),
      cube: R.html({{...{r}, moves: null, cube: {json.dumps(cube)}}}, null),
      far: [9.4, 9.6, 25.6, 29.6].map((v) => R.cubeHtml({{...{json.dumps(cube)}, ...{json.dumps(lead)}, double: false, take: true, proper: `No double, take (${{v}}%)`}})),
      redouble: R.cubeHtml({{...{json.dumps(cube)}, value: 2, ...{json.dumps(lead)}, double: false, take: true, proper: "No redouble, take (25.6%)"}}),
      tooGood: R.cubeHtml({{...{json.dumps(cube)}, ...{json.dumps(lead)}, double: false, too_good: true, proper: "Too good, pass (5.0%)"}}),
      takeQ: R.cubeHtml({{...{json.dumps(cube)}, question: "take", take: true}}),
      luck: [0.601, 0.6, 0.3, -0.29, -0.301, -0.6, -0.601].map((x) => R.html({{...{r}, luck: x}}, [3, 1])),
      luckSpeech: R.speechText({{...{r}, luck: -0.65}}, [3, 1]),
      plainSpeech: [0.3, -0.3, 0.301, -0.301].map((x) => R.speechText({{...{r}, luck: x}}, [3, 1])),
      rolled: R.html({{...{r}, cube: {json.dumps(cube | {"rolled": True})}}}, [3, 1]),
      rolledSpeech: R.speechText({{...{r}, cube: {json.dumps(cube | {"rolled": True})}}}, [3, 1]),
    }}""")
    # TODO-166: how far a double is from paying: the lower of double/take and double/pass, minus no double,
    # signed (cube: 0.5 / 1.2 / 1.0 -> 1.0 - 0.5; far, redouble: 0.6 / 0.5 / 1.0 -> 0.5 - 0.6); gnubg's % is no longer used
    assert (
        "ダブルした場合のエクイティ差 +0.500（プラスはダブルが得、マイナスは損）"
        in out["cube"]
    )
    assert (
        "ダブルした場合のエクイティ差 -0.100" in out["far"][2]
        and "gnubg: No double, take (25.6%)" in out["far"][2]
    )
    assert (
        "リダブルした場合のエクイティ差 -0.100" in out["redouble"]
        and "ギャモン" in out["tooGood"]
    )
    assert "ダブルした場合のエクイティ差 -0.100" in out["tooGood"]
    assert all(
        w not in "".join(out["far"]) + out["redouble"] + out["tooGood"]
        for w in ("遠さ", "一歩手前", "少し早い")
    )
    # the cube decision in the players' words, beside the plain answer
    assert (
        "<b>ダブルしない</b>（ノーダブル／テイク）" in out["far"][2]
        and "<b>ダブルしない（ギャモン狙い）</b>（トゥーグッド／パス）"
        in out["tooGood"]
    )
    assert (
        "<b>ダブルする</b>（ダブル／パス）" in out["cube"]
        and "<b>リダブルしない</b>（ノーリダブル／テイク）" in out["redouble"]
    )
    assert (
        "<b>ダブルすべきだった</b>（ダブル／パス）" in out["rolled"]
        and "<b>テイク</b>（ダブル／テイク）" in out["takeQ"]
    )
    assert (
        "gnubg 2-ply（XG の 3-ply 相当）・" in out["moves"]
        and "手読み" not in out["moves"]
    )
    # TODO-098: the roll's luck by gnubg's levels, after the best move's heading; spoken in words only
    assert [h.split("Luck ")[1].split("</p>")[0] for h in out["luck"]] == [
        "+0.601・とても良い目",
        "+0.600・良い目",
        "+0.300・ふつうの目",
        "-0.290・ふつうの目",
        "-0.301・悪い目",
        "-0.600・悪い目",
        "-0.601・とても悪い目",
    ]  # as gnubg: beyond the levels, not at them
    assert (
        out["luck"][0].index("最善手（")
        < out["luck"][0].index("Luck ")
        < out["luck"][0].index('<ol class="moves">')
    )
    assert out["luckSpeech"].startswith(
        "白の さん いち は、とても悪い目です。最善手は、バーからにじゅうにでヒット、じゅうさんからはちへに枚、ろくから上がりです。"
    )
    assert ["目です" in s for s in out["plainSpeech"]] == [
        False,
        False,
        True,
        True,
    ]  # TODO-100: an ordinary roll is not read out
    assert (
        "Luck" not in out["moves"] and "目です" not in out["rolledSpeech"]
    )  # no luck in the result: nothing shown
    # TODO-096: with dice, the double that was due before the roll comes before the best move
    assert out["rolled"].index("<h2>キューブ（振る前）</h2>") < out["rolled"].index(
        "最善手（白・ダイス 3-1）"
    )
    assert "白の人は振る前に <b>ダブルすべきだった</b>" in out["rolled"]
    assert out["rolledSpeech"].startswith(
        "ダブル、パス。白は振る前にダブルすべきでした。ダブルされたら、黒はパスです。白の さん いち の最善手は"
    )
    assert (
        '<ol class="moves"><li data-k="0" class="on">bar/22* 13/8(2) 6/off'
        in out["moves"]
    )
    assert "最善手（白・ダイス 3-1）" in out["moves"]
    assert (
        "ピップ リード" not in out["moves"] and "振ったのは" not in out["moves"]
    )  # TODO-086: the table and the heading say it
    assert (
        "<h2>キューブ</h2>" in out["cube"]
        and "白の人は <b>ダブルする</b>" in out["cube"]
    )
    assert "ダブルされたら、黒の人はパス。" in out["cube"] and "+1.200" in out["cube"]
    assert (
        "振るのは" not in out["cube"]
    )  # with the cube decision, the pip line stands alone
    # TODO-090: the bar of winning chances first (TODO-129: no summary), the best move or the cube decision, then the table
    for html, middle in ((out["moves"], "最善手"), (out["cube"], "<h2>キューブ</h2>")):
        at = [
            html.index(s)
            for s in ('<div class="winbar">', middle, "<table><tr><th></th>")
        ]
        assert at == sorted(at) and at[0] == 0 and "手前が有利" not in html


@pytest.mark.skipif(not shutil.which("node"), reason="Node.js is not installed")
def test_pips():
    # TODO-090: the board's pip counts, the bar counting 25
    out = _board_js(
        """[B.pips(B.start()), B.pips(B.set(B.set(B.set(B.start(), 23, "white", 1), "bar", "black", 1), "bar", "white", 1))]"""
    )
    assert out == [{"white": 167, "black": 167}, {"white": 168, "black": 192}]


def test_moves_script_is_served_and_cached():
    assert client.get("/moves.js").status_code == 200
    assert '<script src="moves.js"></script>' in client.get("/").text
    assert '"moves.js"' in (STATIC / "sw.js").read_text()


def run_moves(expr: str):
    script = f"""
    const m = require({json.dumps(str(STATIC / "moves.js"))});
    const START = [-2, 0, 0, 0, 0, 5, 0, 3, 0, 0, 0, -5, 5, 0, 0, 0, -3, 0, -5, 0, 0, 0, 0, 2];
    const board = (points, bw = 0, bb = 0) => ({{points, bar_white: bw, bar_black: bb}});
    console.log(JSON.stringify({expr}));
    """
    r = subprocess.run(
        ["node", "-e", script], capture_output=True, text=True, check=True
    )
    return json.loads(r.stdout)


@pytest.mark.skipif(not shutil.which("node"), reason="Node.js is not installed")
def test_move_parse():
    assert run_moves('m.parse("24/18/13 6/4*(2) bar/22 3/off")') == [
        {"from": 24, "to": 18, "hit": False},
        {"from": 18, "to": 13, "hit": False},
        {"from": 6, "to": 4, "hit": True},
        {"from": 6, "to": 4, "hit": True},
        {"from": 25, "to": 22, "hit": False},
        {"from": 3, "to": 0, "hit": False},
    ]
    assert run_moves('m.parse("13/x")') is None


@pytest.mark.skipif(not shutil.which("node"), reason="Node.js is not installed")
def test_move_hops_on_the_board():
    # white (手前) 13/8 6/5 from the start: 13 is points[12] with 5 checkers, 8 has 3
    assert run_moves('m.hops(board(START), "white", "13/8 6/5")') == [
        {"from": 12, "to": 7, "fromLevel": 4, "toLevel": 3, "hit": False},
        {"from": 5, "to": 4, "fromLevel": 4, "toLevel": 0, "hit": False},
    ]
    # black (奥) counts from its own side: its 13 is points[11], its 8 is points[16]
    assert run_moves('m.hops(board(START), "black", "13/8(2)")') == [
        {"from": 11, "to": 16, "fromLevel": 4, "toLevel": 3, "hit": False},
        {"from": 11, "to": 16, "fromLevel": 3, "toLevel": 4, "hit": False},
    ]
    # double 1s, one checker four times, hitting on the way; then from the bar and bearing off
    p = [0] * 24
    p[23], p[21] = 1, -1
    assert run_moves(f'm.hops(board({p}), "white", "24/23/22*/21/20")') == [
        {"from": 23, "to": 22, "fromLevel": 0, "toLevel": 0, "hit": False},
        {"from": 22, "to": 21, "fromLevel": 0, "toLevel": 0, "hit": True},
        {"from": 21, "to": 20, "fromLevel": 0, "toLevel": 0, "hit": False},
        {"from": 20, "to": 19, "fromLevel": 0, "toLevel": 0, "hit": False},
    ]
    p = [0] * 24
    p[2], p[21] = -1, -2  # black's 22 and 3
    assert run_moves(f'm.hops(board({p}, 0, 1), "black", "bar/22 3/off")') == [
        {"from": "bar", "to": 2, "fromLevel": 0, "toLevel": 1, "hit": False},
        {"from": 21, "to": "off", "fromLevel": 1, "toLevel": 0, "hit": False},
    ]
    assert run_moves('m.hops(board(START), "white", "5/1")') is None  # no checker there


@pytest.mark.skipif(not shutil.which("node"), reason="Node.js is not installed")
def test_move_hops_from_steps():
    # the API's steps, one per die: "22/15" with 5-2 passes 17 (no hit), drawn as two arrows
    p = [0] * 24
    p[21], p[16] = 1, 0
    assert run_moves(f'm.hops(board({p}), "white", [[22, 17], [17, 15]])') == [
        {"from": 21, "to": 16, "fromLevel": 0, "toLevel": 0, "hit": False},
        {"from": 16, "to": 14, "fromLevel": 0, "toLevel": 0, "hit": False},
    ]
    # "22/17*/15": the hit on the way is on the first hop
    p[16] = -1
    assert (
        run_moves(f'm.hops(board({p}), "white", [[22, 17], [17, 15]])')[0]["hit"]
        is True
    )
    # from the bar and bearing off, for black
    p = [0] * 24
    p[2], p[21] = -1, -2
    assert run_moves(f'm.hops(board({p}, 0, 1), "black", [[25, 22], [3, 0]])') == [
        {"from": "bar", "to": 2, "fromLevel": 0, "toLevel": 1, "hit": False},
        {"from": 21, "to": "off", "fromLevel": 1, "toLevel": 0, "hit": False},
    ]
    assert (
        run_moves('m.hops(board(START), "white", [[24, 18, 13]])') is None
    )  # not a pair
    assert (
        run_moves('m.hops(board(START), "white", [[5, 1]])') is None
    )  # no checker there


def test_cube_script_is_served_and_cached():
    assert client.get("/cube.js").status_code == 200
    assert '<script src="cube.js"></script>' in client.get("/").text
    assert '"cube.js"' in (STATIC / "sw.js").read_text()


@pytest.mark.skipif(not shutil.which("node"), reason="Node.js is not installed")
def test_cube_settings_buttons():
    # TODO-159: the number row and the four choices (held / doubled, 白 / 黒) map to the cube
    script = f"""
    const c = require({json.dumps(str(STATIC / "cube.js"))});
    const apply = (cube, patch) => ({{ ...cube, ...patch }});
    const centre = {{at: "centre", value: 2, offered: true}};
    const held = {{at: "black", value: 4, offered: false}}, doubled = {{at: "white", value: 8, offered: true}};
    const dice = [3, 1];
    console.log(JSON.stringify([
      c.buttons(centre), c.buttons(held), c.buttons(doubled),
      c.numberPatch(centre, "16", "white", null), c.numberPatch(centre, "16", "black", null),
      c.numberPatch(centre, "16", "white", dice), c.numberPatch(centre, "16", "black", dice),
      c.numberPatch(held, "32", "white", null), c.numberPatch(doubled, "centre", "white", null),
      apply(held, c.numberPatch(held, "64", "black", dice)),
      c.request(apply(centre, c.numberPatch(centre, "16", "white", null)), "white", null),
      c.request(apply(centre, c.numberPatch(centre, "16", "black", dice)), "black", dice),
    ]));
    """
    r = subprocess.run(
        ["node", "-e", script], capture_output=True, text=True, check=True
    )
    (
        b_centre,
        b_held,
        b_doubled,
        w_none,
        b_none,
        w_dice,
        b_dice,
        on_side,
        to_centre,
        renumbered,
        req_none,
        req_dice,
    ) = json.loads(r.stdout)
    # what each row shows, under the row's own name: centre has no choice shown
    assert b_centre == {"cubeValue": "centre", "cubeHold": None, "cubeDouble": None}
    assert b_held == {"cubeValue": "4", "cubeHold": "black", "cubeDouble": None}
    assert b_doubled == {"cubeValue": "8", "cubeHold": None, "cubeDouble": "white"}
    # a number from the centre: on the side opposite the one on roll; doubled to it with no dice, held by it with dice
    assert w_none == {"at": "black", "value": 16, "offered": True} and b_none == {
        "at": "white",
        "value": 16,
        "offered": True,
    }
    assert w_dice == {"at": "black", "value": 16, "offered": False} and b_dice == {
        "at": "white",
        "value": 16,
        "offered": False,
    }
    # ... so the side on roll stays, and the dice are still used
    assert req_none["on_roll"] == "white" and req_none["doubled"] is True
    assert req_dice["on_roll"] == "black" and req_dice["doubled"] is False
    # on a side, only the number changes (held stays held)
    assert on_side == {"value": 32} and renumbered == {
        "at": "black",
        "value": 64,
        "offered": False,
    }
    assert to_centre == {"at": "centre"}
    html = (STATIC / "index.html").read_text()
    for name in ("cubeValue", "cubeHold", "cubeDouble"):
        assert f'data-name="{name}"' in html
    assert 'id="cube-value"' not in html and 'id="cube-offered"' not in html
    js = (STATIC / "app.js").read_text()
    assert (
        "{ ...BgCube.buttons(s.cube), onRoll: s.onRoll," in js
    )  # each row shows what buttons() gives under its own name
    assert "BgCube.numberPatch(state.cube, v, state.onRoll, rolled())" in js
    assert (
        """[data-name="cubeValue"] button:not([data-value="centre"])"""
        in js[js.index("function choseInSheet(") :]
    )  # a number keeps the sheet open
    assert (
        "cubeHold: (v) => setCube({ at: v, offered: false })" in js
        and "cubeDouble: (v) => setCube({ at: v, offered: true })" in js
    )


@pytest.mark.skipif(not shutil.which("node"), reason="Node.js is not installed")
def test_cube_request():
    script = f"""
    const c = require({json.dumps(str(STATIC / "cube.js"))});
    console.log(JSON.stringify([
      c.request({{at: "centre", value: 2, offered: true}}, "white", null),
      c.request({{at: "white", value: 2, offered: true}}, "white", null),
      c.request({{at: "black", value: 4, offered: true}}, "black", [3, 1]),
      c.request({{at: "black", value: 4, offered: false}}, "white", null),
      c.fromRead(null), c.fromRead({{at: "black", value: 3}}),
      c.fromRead({{at: "field"}}, "white"), c.fromRead({{at: "field"}}, "black"),
      c.fromRead({{at: "white", value: 16}}), c.fromRead({{at: "field", value: 8}}, "white"),
    ]));
    """
    r = subprocess.run(
        ["node", "-e", script], capture_output=True, text=True, check=True
    )
    centre, offered, with_dice, owned, none, odd, field_w, field_b, read16, field8 = (
        json.loads(r.stdout)
    )
    assert centre == {
        "on_roll": "white",
        "cube_value": 1,
        "cube_owner": None,
        "doubled": False,
    }
    # offered to 手前: 奥 doubled, so 奥 is on roll
    assert offered == {
        "on_roll": "black",
        "cube_value": 2,
        "cube_owner": "white",
        "doubled": True,
    }
    # with dice the cube is owned, not offered
    assert with_dice == {
        "on_roll": "black",
        "cube_value": 4,
        "cube_owner": "black",
        "doubled": False,
    }
    assert owned["doubled"] is False and owned["on_roll"] == "white"
    assert none["at"] == "centre" and odd == {
        "at": "black",
        "value": 2,
        "offered": True,
    }
    # in a playing field (TODO-045): the side on roll doubled, so it is offered to the other side
    assert field_w == {"at": "black", "value": 2, "offered": True}
    assert field_b == {"at": "white", "value": 2, "offered": True}
    # the number read from the photo (TODO-025)
    assert read16 == {"at": "white", "value": 16, "offered": True}
    assert field8 == {"at": "black", "value": 8, "offered": True}


@pytest.mark.skipif(not shutil.which("node"), reason="Node.js is not installed")
def test_no_dice_while_a_double_is_offered():
    # TODO-086: a cube offered on one side ("ダブルされたところ"): dice left in are not used, so it is take or pass
    script = f"""
    const c = require({json.dumps(str(STATIC / "cube.js"))});
    const offered = {{at: "white", value: 2, offered: true}}, owned = {{at: "white", value: 2, offered: false}};
    const centre = {{at: "centre", value: 2, offered: true}};
    console.log(JSON.stringify([
      c.usedDice(offered, [3, 1]), c.usedDice(owned, [3, 1]), c.usedDice(centre, [3, 1]), c.usedDice(owned, null),
      c.request(offered, "white", c.usedDice(offered, [3, 1])),
      [c.offered(offered), c.offered(owned), c.offered(centre)],
    ]));
    """
    r = subprocess.run(
        ["node", "-e", script], capture_output=True, text=True, check=True
    )
    dropped, kept, kept_centre, none, req, flags = json.loads(r.stdout)
    assert dropped is None and kept == [3, 1] and kept_centre == [3, 1] and none is None
    assert req == {
        "on_roll": "black",
        "cube_value": 2,
        "cube_owner": "white",
        "doubled": True,
    }
    assert flags == [True, False, False]
    js = (STATIC / "app.js").read_text()
    assert (
        "const rolled = (s = state) => BgCube.usedDice(s.cube, diceIn(s));" in js
    )  # everything asked goes through it
    assert (
        "const shown = cubeOffered(s) ? [0, 0] : s.dice;" in js
    )  # the row shows none (TODO-150: no longer hidden)
    # dice read from the photo: the cube is owned, as the server took it
    assert (
        "if (dice && cubeOffered({ cube })) patch.cube = { ...cube, offered: false };"
        in js
    )


@pytest.mark.skipif(not shutil.which("node"), reason="Node.js is not installed")
def test_match_request():
    # TODO-066: the match from the header, made whole before it is sent (and when read back from the phone)
    script = f"""
    const c = require({json.dumps(str(STATIC / "cube.js"))});
    console.log(JSON.stringify([
      c.matchRequest(c.fixMatch(null)), c.matchRequest(c.fixMatch({{length: 7, white: 3, black: 5, crawford: true}})),
      c.matchRequest(c.fixMatch({{length: 7, white: 6, black: 2, crawford: true}})), c.matchRequest(c.fixMatch({{length: 7, white: 6, black: 6, crawford: true}})),
      c.fixMatch({{length: 5, white: 9, black: -2}}), c.fixMatch({{length: 99, white: 3}}), c.fixMatch({{length: 0, white: 3, crawford: true}}),
    ]));
    """
    r = subprocess.run(
        ["node", "-e", script], capture_output=True, text=True, check=True
    )
    money, no_crawford, crawford, both, clamped, bad_length, money2 = json.loads(
        r.stdout
    )
    assert money == {
        "match_length": 0,
        "score_white": 0,
        "score_black": 0,
        "crawford": False,
    }
    assert no_crawford == {
        "match_length": 7,
        "score_white": 3,
        "score_black": 5,
        "crawford": False,
    }  # no one 1 away
    assert crawford["crawford"] is True and both["crawford"] is False
    assert clamped == {"length": 5, "white": 4, "black": 0, "crawford": False}
    assert bad_length["length"] == 0 and money2 == {
        "length": 0,
        "white": 0,
        "black": 0,
        "crawford": False,
    }


def test_photo_view_is_a_checkbox():
    # TODO-094: one checkbox instead of 並べる / 隠す
    html = client.get("/").text
    assert (
        '<input type="checkbox" id="photo-side">' in html
        and 'data-name="photoView"' not in html
    )
    js = (STATIC / "app.js").read_text()
    assert 'update({ photoView: $("photo-side").checked ? "side" : "off" })' in js
    assert '$("photo-side").checked = s.photoView === "side";' in js


def test_match_is_in_the_board_settings_and_sent():
    html = client.get("/").text
    board = html[
        html.index('<section id="board"') : html.index('<section id="outcome"')
    ]
    for id_ in ("match-length", "score-white", "score-black", "crawford"):
        assert f'id="{id_}"' in board, (
            id_
        )  # one place, the board screen's settings (TODO-086)
    js = (STATIC / "app.js").read_text()
    assert (
        js.count("BgCube.matchRequest(state.match)") == 2
    )  # /analyze and /analyze-photo
    # Japanese before the server's 422: 「解析する」 greyed out with the reason (TODO-116)
    # TODO-153: no Crawford game with a cube on one side to warn of; a photo or a reading with the cube on one side takes it off
    assert "CRAWFORD_CUBE" not in js
    # (run in test_crawford_and_a_cube_on_one_side_follow_the_later_choice)
    assert '$("analyze").disabled = !!errs.length;' in js and 'id="analyze-why"' in html
    # TODO-093: the corners screen shows the same inputs, moved there while it is open
    corners = html[
        html.index('<section id="corners"') : html.index('<section id="board"')
    ]
    assert '<div id="corners-match"></div>' in corners and "<details" not in corners
    assert (
        '<div id="board-match">\n    <div id="match"' in board
    )  # where it goes back to
    assert (
        '$(s.step === "corners" ? "corners-match" : "board-match").appendChild($("match"));'
        in js
    )


@pytest.mark.skipif(not shutil.which("node"), reason="Node.js is not installed")
def test_match_in_the_result_words():
    m = {"length": 7, "score": {"white": 6, "black": 5}, "crawford": True}
    cube = {
        "question": "double",
        "doubler": "white",
        "taker": "black",
        "value": 1,
        "take": True,
        "double": True,
        "too_good": False,
        "proper": "Double, take",
        "equity": {"no_double": 0.5, "double_take": 0.6, "double_pass": 1.0},
    }
    r = json.dumps(_RESULT | {"match": m})
    money = json.dumps(_RESULT | {"moves": None, "cube": cube})
    out = _result_js(f"""{{
      speech: R.speechText({r}, [3, 1]),
      cubeNote: R.html({{...{r}, moves: null, cube: {json.dumps(cube)}}}, null),
      money: [R.speechText({money}, null), R.html({money}, null)],
      optional: [R.speechText({{...{money}, cube: {{...{json.dumps(cube)}, double: false, optional: true}}}}, null),
                 R.html({{...{money}, cube: {{...{json.dumps(cube)}, double: false, optional: true}}}}, null)],
    }}""")
    assert (
        "ポイントマッチ" not in out["speech"]
    )  # TODO-099: the score is on the board, not read out
    assert "キューブの判断はマッチのスコアで" in out["cubeNote"]
    assert (
        "ポイントマッチ" not in out["money"][0]
        and "アンリミテッド（ジャコビー・ルールあり）" in out["money"][1]
    )
    assert (
        out["optional"][0].startswith("次は白の番です。")
        and "ダブル" not in out["optional"][0]
    )  # TODO-106: not read out
    assert "白の人は <b>ダブルしてもしなくてもよい</b>" in out["optional"][1]


@pytest.mark.skipif(not shutil.which("node"), reason="Node.js is not installed")
def test_names_follow_the_colour():
    # TODO-086: the sides are named by their checkers' colour; 手前 (white) with the darker ones is 黒
    r = json.dumps(_RESULT)
    out = _result_js(f"""(R.setNames(0), {{
      speech: R.speechText({r}, null), html: R.html({r}, [3, 1]),
      back: (R.setNames(1), R.NAME.white),
    }})""")
    assert out["speech"].startswith("次は黒の番です。")
    assert (
        "<th>黒</th><th>白</th>" in out["html"]
        and "最善手（黒・ダイス 3-1）" in out["html"]
    )
    assert out["back"] == "白"


def test_sample_script_is_served_and_cached():
    assert client.get("/sample.js").status_code == 200
    assert '<script src="sample.js"></script>' in client.get("/").text
    assert '"sample.js"' in (STATIC / "sw.js").read_text()


@pytest.mark.skipif(not shutil.which("node"), reason="Node.js is not installed")
def test_sample_truth():
    script = f"""
    const s = require({json.dumps(str(STATIC / "sample.js"))});
    const START = [-2, 0, 0, 0, 0, 5, 0, 3, 0, 0, 0, -5, 5, 0, 0, 0, -3, 0, -5, 0, 0, 0, 0, 2];
    const fixed = START.slice(); fixed[5] = 4; fixed[23] = 0;   // 3 white checkers fewer on the board
    const read = START.slice(); read[5] = 3;
    console.log(JSON.stringify({{
      name: s.baseName(new Date(2026, 9, 4, 9, 5)),
      t: s.truth({{ image: "x.jpg", corners: [[10.4, 20.6], [100, 20], [110, 90], [0, 90]], home: "left", bottomColour: 0,
                   board: {{ points: fixed, bar_white: 1, bar_black: 0 }}, dice: [5, 2],
                   cube: {{ at: "black", value: 4, offered: true }}, read: {{ points: read, bar_white: 0, bar_black: 0 }} }}),
      plain: s.truth({{ image: "y.png", corners: [[0, 0], [1, 0], [1, 1], [0, 1]], home: "right", bottomColour: 1,
                       board: {{ points: START, bar_white: 0, bar_black: 0 }}, dice: null,
                       cube: {{ at: "centre", value: 2, offered: true }}, read: null }}),
    }}));
    """
    r = subprocess.run(
        ["node", "-e", script], capture_output=True, text=True, check=True
    )
    out = json.loads(r.stdout)
    assert out["name"] == "user-20261004-0905"
    t = out["t"]
    assert t["corners_TL_TR_BR_BL"] == [[10, 21], [100, 20], [110, 90], [0, 90]]
    assert (t["home"], t["bottom_colour"], t["dice"]) == ("left", 0, [5, 2])
    assert (t["bar_white"], t["off_white"], t["off_black"]) == (
        1,
        2,
        0,
    )  # 12 on the board + 1 on the bar
    assert t["cube"] == {"at": "black"} and t["cube_value"] == 4
    assert t["fixed_points"] == [6, 24]
    assert t["read"]["points"][5] == 3
    p = out["plain"]
    assert p["cube"] == {"at": "centre"} and "cube_value" not in p
    assert "read" not in p and (p["off_white"], p["off_black"]) == (0, 0)


def test_app_scripts_are_served_cached_and_loaded_before_app_js():
    html = client.get("/").text
    shell = (STATIC / "sw.js").read_text()
    for name in ("board.js", "board-view.js", "corners-view.js", "api.js"):
        assert client.get("/" + name).status_code == 200, name
        assert html.index(f'src="{name}"') < html.index('src="app.js"'), name
        assert f'"{name}"' in shell, name


def _board_js(expr: str):
    script = f"const B = require({json.dumps(str(STATIC / 'board.js'))}); console.log(JSON.stringify({expr}));"
    return json.loads(
        subprocess.run(
            ["node", "-e", script], capture_output=True, text=True, check=True
        ).stdout
    )


@pytest.mark.skipif(not shutil.which("node"), reason="Node.js is not installed")
def test_board_model():
    out = _board_js("""(() => {
      const s = B.start();
      const edited = B.set(B.set(s, 0, "white", 2), "bar", "black", 1);
      return {
        counts: B.counts(s), edited: [edited.points[0], edited.bar_black, edited.bar_white, s.points[0]],
        errors: [B.errors(s), B.errors(B.set(B.set(s, 5, "white", 6), 6, "white", 1)), B.errors({points: Array(24).fill(0), bar_white: 0, bar_black: 0})],
        swapped: B.swapColours(B.set(s, "bar", "white", 1)),
        mirrorTwice: B.mirror(B.mirror(s)).points.join() === s.points.join(),
        mirrored: B.mirror(s).points.slice(0, 12),
        inverse: ["left", "right"].every((home) => [true, false].every((top) =>
          [...Array(12).keys()].every((c) => { const i = B.pointAt(home, top, c), back = B.columnOf(home, i);
                                               return back.top === top && back.c === c; }))),
        clear: B.set(s, 5, "white", 0).points[5], capped: B.set(s, 1, "black", 20).points[1],
        countOf: [B.countOf(s, 0, "black"), B.countOf(s, 0, "white"), B.countOf(edited, "bar", "black")],
        number: [B.number(0, "white"), B.number(23, "white"), B.number(0, "black"), B.number(23, "black"), B.number(5, "black")],
      };
    })()""")
    assert out["counts"] == {"onW": 15, "onB": 15, "offW": 0, "offB": 0}
    assert out["edited"] == [
        2,
        1,
        0,
        -2,
    ]  # 手前's 2 replace 奥's checkers; the start is not changed
    assert out["errors"][0] == [] and out["errors"][1] == [
        "白の駒が 17 個あります（15個まで）"
    ]
    assert out["errors"][2] == ["盤に駒がありません"]
    assert (
        out["swapped"]["points"][5] == -5
        and out["swapped"]["bar_black"] == 1
        and out["swapped"]["bar_white"] == 0
    )
    assert out["mirrorTwice"] and out["mirrored"] == [
        -5,
        0,
        0,
        0,
        3,
        0,
        5,
        0,
        0,
        0,
        0,
        -2,
    ]
    assert out["inverse"]
    assert out["clear"] == 0 and out["capped"] == -15 and out["countOf"] == [2, 0, 1]
    assert out["number"] == [
        1,
        24,
        24,
        1,
        19,
    ]  # each side counts from its own home (TODO-089)


@pytest.mark.skipif(not shutil.which("node"), reason="Node.js is not installed")
def test_board_tap():
    """A tap at a level of a stack (TODO-059): up to there, one fewer on the top checker, one more past 5."""
    out = _board_js("""(() => {
      const s = B.start(), p = (b, i) => b.points[i];
      return {
        emptyWhite: p(B.tap(s, 1, 3, "white"), 1), emptyBlack: p(B.tap(s, 1, 2, "black"), 1),
        keepsColour: p(B.tap(s, 0, 4, "white"), 0),          // 奥's 2 on point 1 stay 奥's
        top: p(B.tap(s, 0, 2, "white"), 0), last: p(B.tap(B.tap(s, 0, 2, "white"), 0, 1, "white"), 0),
        lower: p(B.tap(s, 5, 3, "white"), 5),                 // 手前's 5 down to 3
        more: p(B.tap(s, 5, 5, "white"), 5), more2: p(B.tap(B.tap(s, 5, 5, "white"), 5, 5, "white"), 5),
        upTo5: p(B.tap(B.set(s, 5, "white", 4), 5, 5, "white"), 5), max: p(B.tap(B.set(s, 5, "white", 15), 5, 5, "white"), 5),
        level9: p(B.tap(s, 1, 9, "white"), 1), level0: p(B.tap(s, 1, 0, "white"), 1),
        barBlack: B.tap(s, "bar", 2, "black"), barTop: B.tap(B.set(s, "bar", "white", 1), "bar", 1, "white").bar_white,
      };
    })()""")
    assert (
        out["emptyWhite"] == 3 and out["emptyBlack"] == -2 and out["keepsColour"] == -4
    )
    assert out["top"] == -1 and out["last"] == 0 and out["lower"] == 3
    assert (
        out["more"] == 6
        and out["more2"] == 7
        and out["upTo5"] == 5
        and out["max"] == 15
    )
    assert (
        out["level9"] == 5 and out["level0"] == 1
    )  # levels outside 1..5 are taken as the nearest
    assert (
        out["barBlack"]["bar_black"] == 2
        and out["barBlack"]["bar_white"] == 0
        and out["barTop"] == 0
    )


def test_board_can_be_fixed_on_the_result_screen():
    # TODO-138: the board screen's board and its sheets move to the result screen, and a fix there is analysed again
    html = client.get("/").text
    outcome = html[html.index('<section id="outcome"') :]
    assert '<div id="outcome-board"></div>' in outcome and "result-svg" not in html
    js = (STATIC / "app.js").read_text()
    assert '$(out ? "outcome-board" : "boards").appendChild($("board-pin"));' in js
    assert "reanalyzeTimer = setTimeout(reanalyze, REANALYZE_WAIT);" in js
    assert "if (abort.signal.aborted || inputsKey() !== key" in js


def test_screens_beyond_the_next_can_go_back_to_the_first():
    # TODO-148, TODO-149: 「最初へ」 next to 戻る, where 戻る does not already lead to the photo screen, straight back to it
    html = client.get("/").text
    row = html[html.index('<div class="actrow">') :]
    assert (
        row.index('id="back"')
        < row.index('id="to-start"')
        < row.index('id="recognize"')
    )
    js = (STATIC / "app.js").read_text()
    assert (
        'part((s) => [s.step, s.fromPhoto], () => { $("to-start").hidden = previousStep() === "photo"; });'
        in js
    )
    assert '$("to-start").addEventListener("click", goStart);' in js
    body = js[js.index("function goStart()") :]
    body = body[: body.index("\n}\n")]
    assert (
        'go("photo");' in body and "history.back();" in body
    )  # the history entry is used up too


def test_the_settings_open_beside_the_part_tapped():
    # TODO-150: a tap on the match, the cube or the dice opens its settings above or below that part, not from the bottom
    js = (STATIC / "app.js").read_text()
    assert "below ? r.bottom + gap : r.top - gap - h" in js
    # placed again when the phone turns, the page scrolls or the settings change size
    for hook in [
        'addEventListener("resize", placeSheet);',
        'addEventListener("scroll", placeSheet, { passive: true });',
        "new ResizeObserver(placeSheet);",
        "select, tapPart);\n  placeSheet();",
    ]:
        assert hook in js
    css = (STATIC / "style.css").read_text()
    assert (
        "bottom: var(--bar-h"
        not in css[css.index(".sheet {") : css.index(".sheet[hidden]")]
    )


def test_a_value_chosen_in_the_settings_is_taken_at_once():
    # TODO-150: a choice closes the settings (the dice once both are set), and the result screen does not wait for them
    js = (STATIC / "app.js").read_text()
    assert (
        'if (e.currentTarget.id === "sheet-roll" && halfDie()) return;' in js
    )  # only the dice wait for the other die
    assert '$(`sheet-${k}`).addEventListener("change", choseInSheet);' in js
    gate = js[
        js.index("const REANALYZE_WAIT") : js.index(
            "reanalyzeTimer = setTimeout(reanalyze"
        )
    ]
    assert "s.sheet" not in gate


def test_a_die_chosen_takes_the_double_back():
    # TODO-150: the dice row stays while a double is offered (empty), and a die chosen there clears "ダブルされたところ"
    js = (STATIC / "app.js").read_text()
    assert '$("dice-row").hidden' not in js
    assert "const shown = cubeOffered(s) ? [0, 0] : s.dice;" in js
    assert "const dice = offered ? [0, 0] : state.dice.slice();" in js
    assert (
        "cube: { ...state.cube, offered: false }" in js[js.index("function setDie(") :]
    )


def _crawford_js(cases: str):
    """Run cases in Node with setCube, setMatch, startPhoto and recognize from app.js, on a stub state (TODO-153)."""
    js = (STATIC / "app.js").read_text()
    funcs = "".join(
        js[js.index(a) : js.index(b)]
        for a, b in [
            ("function setCube(", "function setResult("),
            ("function startPhoto(", "async function loadPhoto("),
            ("async function recognize(", "async function analyze("),
        ]
    )
    script = f"""
      const BgCube = require({json.dumps(str(STATIC / "cube.js"))});
      const BgBoard = require({json.dumps(str(STATIC / "board.js"))});
      let state, kept, alerts, overlay = null, failReveal = false;
      const keep = (k, v) => {{ kept.push([k, JSON.parse(v).crawford]); }};
      const update = (p) => {{ state = {{ ...state, ...p }}; }};
      const noop = () => {{}}, el = {{ scrollIntoView: noop, addEventListener: noop, removeEventListener: noop }};
      const $ = () => el, alert = (t) => alerts.push(t), go = noop, persist = noop, guessCorners = noop, stopOverlay = noop;
      const setResult = noop, storedSide = () => ({{}}), stored = (k, a, f) => f, defaultCorners = () => [];
      const startOverlay = () => failReveal ? {{ scan: {{ reveal: async () => {{ throw new Error("cancelled"); }} }} }} : null;
      const withBusy = (t, f) => f(), uploadImage = async () => ({{ blob: null, scale: 1 }}), rolled = () => null;
      const cubeOffered = (s) => BgCube.offered(s.cube), sideSent = () => "", photoId = () => "p";
      class FormData {{ append() {{}} }}
      let reply;
      const BgApi = {{ postStages: async () => reply, scaleGeometry: (g) => g }};
      {funcs}
      const side = {{ at: "black", value: 2, offered: false }}, centre = {{ at: "centre", value: 2, offered: true }};
      const m = (crawford) => ({{ length: 7, white: 6, black: 3, crawford }});
      const fresh = (match, cube) => {{ state = {{ match, cube, corners: [], dice: [0, 0], onRoll: "white", homePick: "auto",
                                                 plies: "2", bottomColour: 1, photo: {{}} }}; kept = []; alerts = []; failReveal = false; }};
      const read = (cubeRead, error) => {{ reply = {{ recognized: {{ points: Array(24).fill(0), bar_white: 0, bar_black: 0 }},
                                                    cube_read: cubeRead, analysis: null, analysis_error: error }}; return recognize(); }};
      const out = (x) => ({{ crawford: state.match.crawford, cubeAt: state.cube.at, cube: state.cube, kept, alerts, board: !!state.board, ...x }});
      (async () => {{ {cases} }})();"""
    r = subprocess.run(
        ["node", "-e", script], capture_output=True, text=True, check=True
    )
    return json.loads(r.stdout)


@pytest.mark.skipif(not shutil.which("node"), reason="Node.js is not installed")
def test_crawford_and_a_cube_on_one_side_follow_the_later_choice():
    # TODO-153: the later choice wins; a photo (reopened or read) with the cube on one side is the later one
    crawford_err = "no doubling in the Crawford game: the cube stays at 1 in the middle"
    out = _crawford_js(f"""const r = [];
      fresh(m(false), side); setMatch({{ crawford: true }}); r.push(out());
      fresh(m(true), centre); setCube({{ at: "white" }}); r.push(out());
      fresh(m(true), side); setCube({{ value: 4 }}); r.push(out());              // one side already, only the number changed
      fresh(m(false), side); setMatch({{ white: 5 }}); r.push(out());
      fresh(m(true), centre); setCube({{ value: 4 }}); r.push(out());
      fresh(m(true), centre); startPhoto(null, null, {{ cube: side }}); r.push(out());
      fresh(m(true), side); startPhoto(null, null, null); r.push(out());          // a new photo: the cube in the centre
      fresh(m(true), centre); await read({{ at: "black", value: 2 }}, {json.dumps(crawford_err)}); r.push(out());
      fresh(m(true), centre); await read({{ at: "black", value: 2 }}, "white has 16 checkers"); r.push(out());
      fresh(m(true), centre); await read(null, "white has 16 checkers"); r.push(out());
      fresh(m(true), centre); failReveal = true; await read({{ at: "black", value: 2 }}, {json.dumps(crawford_err)}); r.push(out());
      console.log(JSON.stringify(r));""")
    (
        crawford_in,
        cube_out,
        value_on_side,
        other_match,
        other_cube,
        reopened,
        new_photo,
        read,
        read_other,
        no_cube,
        cancelled,
    ) = out
    assert crawford_in["crawford"] is True and crawford_in["cube"] == {
        "at": "centre",
        "value": 2,
        "offered": False,
    }
    assert (
        cube_out["crawford"] is False
        and cube_out["cubeAt"] == "white"
        and cube_out["kept"] == [["match", False]]
    )
    assert value_on_side["crawford"] is False and value_on_side["cube"]["value"] == 4
    assert other_match["cubeAt"] == "black"  # no Crawford game: the cube stays
    assert other_cube["crawford"] is True and other_cube["cube"] == {
        "at": "centre",
        "value": 4,
        "offered": True,
    }
    assert (
        reopened["crawford"] is False
        and reopened["cubeAt"] == "black"
        and reopened["kept"] == [["match", False]]
    )
    assert (
        new_photo["crawford"] is True
        and new_photo["cubeAt"] == "centre"
        and new_photo["kept"] == []
    )
    # read: taken off without a word, once the board is in
    assert (
        read["crawford"] is False
        and read["cubeAt"] == "black"
        and read["board"]
        and read["alerts"] == []
    )
    assert (
        read_other["crawford"] is False
        and len(read_other["alerts"]) == 1
        and "16" in read_other["alerts"][0]
    )  # another reason: said
    assert no_cube["crawford"] is True and len(no_cube["alerts"]) == 1
    # the reading cut short before the board is in: the Crawford game stays
    assert (
        cancelled["crawford"] is True
        and not cancelled["board"]
        and cancelled["kept"] == []
    )


@pytest.mark.skipif(not shutil.which("node"), reason="Node.js is not installed")
def test_offered_cube_keeps_clear_of_checkers():
    # TODO-160: the cube just offered lies in the field of the side that doubled, at the middle unless a checker is in the way
    script = f"""
    global.BgBoard = require({json.dumps(str(STATIC / "board.js"))});
    const V = require({json.dumps(str(STATIC / "board-view.js"))});
    const board = (set, fill) => {{
      const points = Array(24).fill(fill || 0);
      for (const [i, n] of Object.entries(set || {{}})) points[i] = n;
      return {{ points, bar_white: 0, bar_black: 0 }};
    }};
    const at = (b, side) => V.offeredCubeCentre(b, "right", side);
    console.log(JSON.stringify({{
      emptyB: at(board(), "black"), emptyW: at(board(), "white"),
      hitB: at(board({{ 20: 3 }}), "black"),        // 手前 doubled: a stack of 3 beside the middle, in the upper row of the right field
      hitW: at(board({{ 9: -3 }}), "white"),        // 奥 doubled: the same in the lower row of the left field
      farB: at(board({{ 20: 1 }}), "black"),        // one checker, not reaching the cube: stays
      barB: at(board({{ 20: 3, 21: 3 }}), "black"),   // both ±1 taken, ±3 free: the one nearer the bar (the left one in the right field)
      barW: at(board({{ 8: -3, 9: -3 }}), "white"),   // the same in the left field: the right one
      full: at(board(null, 5), "black"),
    }}));
    """
    out = json.loads(
        subprocess.run(
            ["node", "-e", script], capture_output=True, text=True, check=True
        ).stdout
    )
    assert out["emptyB"] == {
        "x": 492,
        "y": pytest.approx(220 - 75.25),
    }  # right field's middle, upper half (奥 was doubled)
    assert out["emptyW"] == {
        "x": 164,
        "y": pytest.approx(220 + 75.25),
    }  # left field's middle, lower half
    assert (
        out["hitB"]["x"] == 516 and out["hitW"]["x"] == 188
    )  # one point over (24), the nearest clear place
    assert out["hitB"]["y"] == out["emptyB"]["y"]  # the height does not change
    assert out["farB"]["x"] == 492
    assert (
        out["barB"]["x"] == 492 - 72 and out["barW"]["x"] == 164 + 72
    )  # towards the bar in both fields
    assert out["full"]["x"] == 492  # every place is taken: the middle


@pytest.mark.skipif(not shutil.which("node"), reason="Node.js is not installed")
def test_moves_as_differences_and_match_winning_chances():
    # TODO-167: the best play's own number, the others' as the difference, always signed; in a match, MWC
    moves = [
        {"move": "8/5 6/5", "equity": -0.1234},
        {"move": "24/21 6/5", "equity": -0.3264},
        {"move": "13/10 6/5", "equity": -0.1234},
    ]
    cube = {
        "question": "double",
        "doubler": "white",
        "taker": "black",
        "value": 1,
        "take": True,
        "double": False,
        "too_good": False,
        "proper": "No double, take",
        "equity": {"no_double": 0.5, "double_take": -0.25, "double_pass": 1.0},
    }
    money = _RESULT | {"moves": moves, "equity": {"white": 0.05, "black": -0.05}}
    mwc_moves = [m | {"mwc": v} for m, v in zip(moves, (30.12, 28.7, 30.12))]
    match = money | {
        "moves": mwc_moves,
        "mwc": {"white": 29.1, "black": 70.9},
        "match": {"length": 7, "score": {"white": 3, "black": 5}, "crawford": False},
    }
    mcube = cube | {
        "mwc": {"no_double": 29.67, "double_take": 28.19, "double_pass": 40.05}
    }
    out = _result_js(f"""[R.html({json.dumps(money)}, [3, 1]), R.html({json.dumps(match | {"plies": 3})}, [3, 1]),
      R.html({json.dumps(_RESULT | {"moves": None, "cube": cube})}, null),
      R.html({json.dumps(_RESULT | {"moves": None, "cube": mcube})}, null)]""")
    m, x, mc, xc = out
    assert (
        "<span>エクイティ -0.123</span>" in m
        and "<span>-0.203</span>" in m
        and "<span>+0.000</span>" in m
    )
    assert (
        "<td>キューブレス エクイティ</td><td>+0.050</td><td>-0.050</td>" in m
        and "MWC" not in m
    )
    assert (
        "<span>MWC 30.12%</span>" in x
        and "<span>-1.42%</span>" in x
        and "<span>+0.00%</span>" in x
    )
    assert "<td>キューブレス MWC</td><td>29.10%</td><td>70.90%</td>" in x
    assert (
        "最善手と勝率はキューブなし" in m and "最善手と勝率はキューブなし" in x
    )  # the plays are cubeless too
    assert "<td>キューブレス EMG</td><td>+0.050</td><td>-0.050</td>" in x
    assert (
        "<th>キューブフル エクイティ</th>" in mc
        and "<td>+0.500</td>" in mc
        and "<td>-0.250</td>" in mc
    )
    # TODO-166: the difference in a match is the MWC's, in % with two decimals (min(28.19, 40.05) - 29.67)
    assert (
        "ダブルした場合のMWC差 -1.48%（プラスはダブルが得、マイナスは損）" in xc
        and "エクイティ差" not in xc
    )
    assert "ダブルした場合のエクイティ差 -0.750" in mc
    assert "gnubg 3-ply（XG の 4-ply 相当）" in x
    assert (
        "<th>キューブフル MWC</th>" in xc
        and "<td>29.67%</td>" in xc
        and "<td>40.05%</td>" in xc
        and "+0.500" not in xc
    )
