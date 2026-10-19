// The analysis result in words: the HTML of the result box and the short text read aloud.
// r is what /analyze returns (sides are "white" = 手前 and "black" = 奥), dice the roll it was
// worked out for, or null.
"use strict";

const BgResult = (() => {
  // The sides by their checkers' colour, as drawn: the lighter ones are 白 (TODO-086). app.js sets it
  // with the setting of 手前's colour (bottomColour 1: 手前's are the lighter, 0: the darker).
  const NAME = { white: "白", black: "黒" };
  function setNames(bottomColour) {
    Object.assign(NAME, bottomColour === 0 ? { white: "黒", black: "白" } : { white: "白", black: "黒" });
  }

  // With dice in, the side on roll has already rolled: "振った人", not "次に振る人" (TODO-042).
  function rollWho(dice) {
    return dice ? "振った" : "次に振る";
  }

  function esc(s) {
    return String(s).replace(/[&<>"]/g, (c) => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;" }[c]));
  }

  // The words for a cube decision: "ダブル" or "リダブル", "テイク" or "パス".
  function cubeWords(c) {
    return { word: c.value > 1 ? "リダブル" : "ダブル", take: c.take ? "テイク" : "パス" };
  }

  // The cube decision in the words players use (gnubg's own, TODO-166): "ノーダブル／テイク",
  // "ダブル／パス", "トゥーグッド／パス", "ノーリダブル／テイク". sep joins the two (spoken: a pause).
  function cubeLabel(c, sep = "／") {
    const { word, take } = cubeWords(c);
    const head = c.too_good ? "トゥーグッド" : c.double ? word : c.optional ? `オプショナル${word}` : `ノー${word}`;
    return head + sep + take;
  }

  // v to d decimals, always signed as gnubg and XG print equities and differences (TODO-167). Rounded first,
  // so a tiny negative shows as +0.000, not -0.000
  function signed(v, d) {
    const x = Math.round(v * 10 ** d) / 10 ** d;
    return (x >= 0 ? "+" : "-") + Math.abs(x).toFixed(d);
  }

  // A play's number (TODO-167): the best play's own, the others' as the difference from it. In a match
  // (the plays carry mwc), the match winning chance in %; in a money game, the cubeless equity.
  function moveValue(m, best) {
    if (m.mwc != null) return m === best ? `MWC ${m.mwc.toFixed(2)}%` : `${signed(m.mwc - best.mwc, 2)}%`;
    return m === best ? `エクイティ ${signed(m.equity, 3)}` : signed(m.equity - best.equity, 3);
  }

  // an indented row of the win table: f(one side's probabilities), to one decimal like the server's.
  // The server rounds each number on its own, so a difference can come out a little below 0.
  const sub = (p, label, f) => `<tr><td class="sub">${label}</td>` +
    ["white", "black"].map((c) => `<td>${Math.max(0, Math.round(10 * f(p[c])) / 10)}%</td>`).join("") + "</tr>";

  // Top to bottom (TODO-090): the winning chances as a bar, the cube decision or the best move, then
  // the table of the numbers. No summary line: it said what these say (TODO-129).
  function html(r, dice) {
    const pips = r.pips;
    let out = "";
    const p = r.probabilities;
    if (!r.game_over) {
      out += `<div class="winbar"><div class="w" style="width:${p.white.win}%">${NAME.white} ${p.white.win}%</div>` +
        `<div class="b" style="width:${p.black.win}%">${NAME.black} ${p.black.win}%</div></div>`;
    }
    // who rolled is in the best move's heading (TODO-086)
    if (r.cube) out += cubeHtml(r.cube);
    else if (!r.moves && !r.game_over) out += `<p>${rollWho(dice)}のは${NAME[r.on_roll]}の人。</p>`;
    if (r.moves) {
      out += `<h2>最善手（${NAME[r.on_roll]}・ダイス ${dice ? dice.join("-") : ""}）</h2>`;
      if (r.luck != null) out += `<p>Luck ${r.luck >= 0 ? "+" : ""}${r.luck.toFixed(3)}・${luckWords(r.luck)}</p>`;
      out += r.moves.length
        ? `<ol class="moves">${r.moves.map((m, k) => `<li data-k="${k}"${k ? "" : ' class="on"'}>${esc(m.move)}<span>${moveValue(m, r.moves[0])}</span></li>`).join("")}</ol>` +
          `<p class="note">番号は盤と同じく${NAME[r.on_roll]}の人から見たもの。行をタップで矢印を切り替え。</p>`
        : "<p>動かせる手がありません。</p>";
    }
    if (!r.game_over) {
      out += `<table><tr><th></th><th>${NAME.white}</th><th>${NAME.black}</th></tr>` +
        `<tr><td>勝率</td><td>${p.white.win}%</td><td>${p.black.win}%</td></tr>` +
        // gnubg's gammon includes backgammons: split the win into parts that add up to it (TODO-128)
        sub(p, "シングル勝ち", (q) => q.win - q.gammon) +
        sub(p, "ギャモン勝ち", (q) => q.gammon - q.backgammon) +
        sub(p, "バックギャモン勝ち", (q) => q.backgammon) +
        // a match: the match winning chance, and the equity by its name there, EMG (TODO-167)
        (r.mwc ? `<tr><td>キューブレス MWC</td><td>${r.mwc.white.toFixed(2)}%</td><td>${r.mwc.black.toFixed(2)}%</td></tr>` : "") +
        `<tr><td>キューブレス ${r.mwc ? "EMG" : "エクイティ"}</td><td>${signed(r.equity.white, 3)}</td><td>${signed(r.equity.black, 3)}</td></tr>` +
        `<tr><td>ピップ数</td><td>${pips.white}</td><td>${pips.black}</td></tr></table>`;
    }
    out += `<p class="note">gnubg ${r.plies}-ply（XG の ${r.plies + 1}-ply 相当）・最善手と勝率はキューブなし${r.cube ? (r.match ? "・キューブの判断はマッチのスコアで" : "・キューブの判断はアンリミテッド（ジャコビー・ルールあり）") : ""}。` +
      `Position ID: <code>${esc(r.position_id)}</code></p>`;
    return out;
  }

  // The roll's luck in words, as gnubg's Luck() (analysis.c): beyond 0.6 and 0.3 (TODO-098).
  function luckWords(x) {
    return x > 0.6 ? "とても良い目" : x > 0.3 ? "良い目" : x < -0.6 ? "とても悪い目" : x < -0.3 ? "悪い目" : "ふつうの目";
  }

  // The cube decision: the answer first, then gnubg's cubeful equities (the doubler's, per cube before the double).
  function cubeHtml(c) {
    const d = NAME[c.doubler], t = NAME[c.taker];
    const { word, take } = cubeWords(c);
    let out = c.rolled ? "<h2>キューブ（振る前）</h2>" : "<h2>キューブ</h2>";
    if (c.rolled) {   // with dice, shown only when a double was due (TODO-096)
      out += `<p class="answer">${d}の人は振る前に <b>${word}すべきだった</b>（${cubeLabel(c)}）</p>`;
      out += `<p>${word}されたら、${t}の人は${take}。</p>`;
    } else if (c.question === "take") {
      out += `<p class="answer">${t}の人は <b>${take}</b>（${cubeLabel(c)}）</p>`;
      out += `<p>${d}の人の${word}は${c.double ? "正しい" : c.optional ? "してもしなくてもよい" : c.too_good ? "ダブルせずギャモンを狙う方がよい局面" : "早すぎる"}。</p>`;
    } else {
      out += `<p class="answer">${d}の人は <b>${c.double ? `${word}する` : c.optional ? `${word}してもしなくてもよい` : c.too_good ? `${word}しない（ギャモン狙い）` : `${word}しない`}</b>（${cubeLabel(c)}）</p>`;
      out += `<p>${word}されたら、${t}の人は${take}。</p>`;
    }
    // a match: the match winning chances in % (TODO-167); money: the equities
    const e = c.mwc || c.equity;
    const row = (name, v) => `<tr><td>${name}</td><td>${c.mwc ? `${v.toFixed(2)}%` : signed(v, 3)}</td></tr>`;
    out += `<table><tr><th>${d}の人から見て</th><th>キューブフル ${c.mwc ? "MWC" : "エクイティ"}</th></tr>` +
      row(`${word}しない`, e.no_double) + row(`${word}・テイク`, e.double_take) + row(`${word}・パス`, e.double_pass) +
      `</table>${distanceHtml(c)}<p class="note">gnubg: ${esc(c.proper)}</p>`;
    return out;
  }

  // How far a double is from paying (TODO-166): the doubler's equity (a match: MWC) if the double is made,
  // minus without it. The other side answers the double as is best for it, so the lower of take and pass
  // counts. Below 0 the double loses; the nearer to 0, the nearer a double. This replaces gnubg's
  // "(25.6%)" (how often the other side would have to pass wrongly), which players do not use.
  function distanceHtml(c) {
    const e = c.mwc || c.equity;
    const g = Math.min(e.double_take, e.double_pass) - e.no_double;
    if (!Number.isFinite(g)) return "";
    const { word } = cubeWords(c);
    return `<p>${word}した場合のエクイティ差 ${c.mwc ? `${signed(g, 2)}%` : signed(g, 3)}（${word}とノーダブルの差。マイナスは${word}すると損）</p>`;
  }

  // A short spoken summary, not the numbers: the screen keeps the percentages and pips. Spoken, the sides
  // are just 白 and 黒, without the screen's "の人" (TODO-106).
  function speechText(r, dice) {
    const parts = [];
    let cubeText = "";
    if (r.cube) {
      const c = r.cube, { word, take } = cubeWords(c), d = NAME[c.doubler], t = NAME[c.taker];
      // a double that may or may not be made is not worth saying (TODO-106)
      const label = cubeLabel(c, "、") + "。";   // the players' words first, then the plain ones
      cubeText = c.rolled ? `${label}${d}は振る前に${word}すべきでした。${word}されたら、${t}は${take}です。`
        : c.question === "take" ? `${label}${d}の${word}に、${t}は${take}です。`
          : c.double ? `${label}${d}は${word}すべきで、${t}は${take}です。`
            : c.optional ? ""
              : c.too_good ? `${label}${d}は${word}せず、ギャモンを狙うほうがよいです。`
                : `${label}${d}はまだ${word}しないほうがよいです。`;
    }
    if (r.cube && r.cube.rolled) parts.push(cubeText);   // as on the screen, before the best move (TODO-096)
    const bestMove = r.moves && dice;   // read early: it is what the player wants to hear
    if (bestMove) {
      const roll = `${NAME[r.on_roll]}の ${kana(dice[0])} ${kana(dice[1])}`;
      const luck = r.luck != null && luckWords(r.luck);
      const lucky = luck && luck !== "ふつうの目";   // an ordinary roll is not worth saying (TODO-100)
      const best = r.moves.length ? `最善手は、${moveToSpeech(r.moves[0].move)}です。` : "動かせる手がありません。";
      parts.push(lucky ? `${roll} は、${luck}です。${best}` : r.moves.length ? `${roll} の${best}` : `${roll} では、${best}`);
    } else if (!r.game_over && !(cubeText && !r.cube.rolled)) {
      // who rolls next is read first (TODO-052); a cube decision names the side itself. With dice there
      // is always a best move (or none to make), unless the game is over
      parts.push(`次は${NAME[r.on_roll]}の番です。`);
    }
    if (cubeText && !r.cube.rolled) parts.push(cubeText);
    parts.push(r.game_over ? `${NAME[r.favourite]}の勝ちで、ゲームは終わっています。` : standingToSpeech(r));
    return parts.join("");
  }

  // The favourite's winning chance in words; a gammon or a big race lead only when it matters.
  function standingToSpeech(r) {
    const fav = r.favourite, p = r.probabilities[fav], pips = r.pips;
    const w = p.win;
    let s = w >= 90 ? `${NAME[fav]}がほぼ勝ちです。`
      : w >= 75 ? `${NAME[fav]}がかなり有利です。`
        : w >= 60 ? `${NAME[fav]}が有利です。`
          : w >= 53 ? `${NAME[fav]}がやや有利です。`
            : "ほぼ互角です。";
    if (w >= 53 && p.gammon >= 25) s += "ギャモン勝ちの見込みも十分あります。";
    if (pips.leader && pips.difference >= 20) s += `ピップ数では${NAME[pips.leader]}が大きくリードしています。`;
    return s;
  }

  // Numbers are spoken as kana: the voices read a bare "2" as に or ツー, "4" and "7" two ways too (TODO-132)
  const DIGIT = ["", "いち", "に", "さん", "よん", "ご", "ろく", "なな", "はち", "きゅう"];
  function kana(n) {
    n = Number(n);
    return n < 10 ? DIGIT[n] : (n >= 20 ? DIGIT[Math.floor(n / 10)] : "") + "じゅう" + DIGIT[n % 10];
  }

  // "bar/22* 13/8(2) 6/off" -> "バーからにじゅうにでヒット、じゅうさんからはちへに枚、ろくから上がり".
  // A hit on the way, "24/18*/13", is "にじゅうよんからじゅうはちでヒットして、じゅうさんへ" (TODO-166)
  function moveToSpeech(move) {
    return move.trim().split(/\s+/).map((step) => {
      const m = step.match(/^(.*?)(?:\((\d+)\))?$/);
      const pts = m[1].split("/").map((x) => {
        const n = x.replace("*", "").toLowerCase();
        return { name: n === "bar" ? "バー" : n === "off" ? "上がり" : kana(n), hit: x.endsWith("*") };
      });
      const last = pts.length - 1;
      let s = pts[0].name;
      for (let i = 1; i <= last; i++) {
        const { name, hit } = pts[i];
        s += pts[i - 1].hit ? "、" : "から";
        s += name + (hit ? (i < last ? "でヒットして" : "でヒット") : "");
        if (i === last && pts[i - 1].hit && !hit && !m[2]) s += "へ";
      }
      return s + (m[2] ? `へ${kana(m[2])}枚` : "");
    }).join("、");
  }

  return { NAME, setNames, rollWho, esc, html, cubeHtml, speechText, moveToSpeech };
})();

if (typeof module !== "undefined") module.exports = BgResult;
