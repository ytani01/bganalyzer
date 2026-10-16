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

  // The match in words (TODO-066), as in the server's summary: "7 ポイントマッチ 白 3 対 黒 5（クロフォード）".
  function matchText(m) {
    return `${m.length} ポイントマッチ ${NAME.white} ${m.score.white} 対 ${NAME.black} ${m.score.black}` + (m.crawford ? "（クロフォード）" : "");
  }

  // The words for a cube decision: "ダブル" or "リダブル", "テイク" or "パス".
  function cubeWords(c) {
    return { word: c.value > 1 ? "リダブル" : "ダブル", take: c.take ? "テイク" : "パス" };
  }

  // Top to bottom (TODO-090): the summary, the winning chances as a bar, the cube decision or the
  // best move, then the table of the numbers.
  function html(r, dice) {
    const pips = r.pips;
    let out = `<p class="summary">${esc(r.summary)}</p>`;
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
      out += r.moves.length
        ? `<ol class="moves">${r.moves.map((m, k) => `<li data-k="${k}"${k ? "" : ' class="on"'}>${esc(m.move)}<span>エクイティ ${m.equity.toFixed(3)}</span></li>`).join("")}</ol>` +
          `<p class="note">番号は盤と同じく${NAME[r.on_roll]}の人から見たもの。行をタップで矢印を切り替え。</p>`
        : "<p>動かせる手がありません。</p>";
    }
    if (!r.game_over) {
      out += `<table><tr><th></th><th>${NAME.white}</th><th>${NAME.black}</th></tr>` +
        `<tr><td>勝率</td><td>${p.white.win}%</td><td>${p.black.win}%</td></tr>` +
        `<tr><td>うちギャモン勝ち</td><td>${p.white.gammon}%</td><td>${p.black.gammon}%</td></tr>` +
        `<tr><td>うちバックギャモン勝ち</td><td>${p.white.backgammon}%</td><td>${p.black.backgammon}%</td></tr>` +
        `<tr><td>エクイティ</td><td>${r.equity.white.toFixed(3)}</td><td>${r.equity.black.toFixed(3)}</td></tr>` +
        `<tr><td>ピップ数</td><td>${pips.white}</td><td>${pips.black}</td></tr></table>`;
    }
    out += `<p class="note">gnubg ${r.plies}手読み・勝率とエクイティはキューブなし${r.cube ? (r.match ? "・キューブの判断はマッチのスコアで" : "・キューブの判断はマネーゲーム（ジャコビー・ルールあり）") : ""}。` +
      `Position ID: <code>${esc(r.position_id)}</code></p>`;
    return out;
  }

  // The cube decision: the answer first, then gnubg's cubeful equities (the doubler's, per cube before the double).
  function cubeHtml(c) {
    const d = NAME[c.doubler], t = NAME[c.taker];
    const { word, take } = cubeWords(c);
    let out = "<h2>キューブ</h2>";
    if (c.question === "take") {
      out += `<p class="answer">${t}の人は <b>${take}</b></p>`;
      out += `<p>${d}の人の${word}は${c.double ? "正しい" : c.optional ? "してもしなくてもよい" : c.too_good ? "ダブルせずギャモンを狙う方がよい局面" : "早すぎる"}。</p>`;
    } else {
      out += `<p class="answer">${d}の人は <b>${c.double ? `${word}する` : c.optional ? `${word}してもしなくてもよい` : c.too_good ? `${word}しない（ギャモン狙い）` : `${word}しない`}</b></p>`;
      out += `<p>${word}されたら、${t}の人は${take}。</p>`;
    }
    const e = c.equity;
    const row = (name, v) => `<tr><td>${name}</td><td>${v >= 0 ? "+" : ""}${v.toFixed(3)}</td></tr>`;
    out += `<table><tr><th>${d}の人から見て</th><th>エクイティ</th></tr>` +
      row(`${word}しない`, e.no_double) + row(`${word}・テイク`, e.double_take) + row(`${word}・パス`, e.double_pass) +
      `</table><p class="note">gnubg の判断: ${esc(c.proper)}</p>`;
    return out;
  }

  // A short spoken summary, not the numbers: the screen keeps the percentages and pips.
  function speechText(r, dice) {
    const parts = [];
    const bestMove = r.moves && dice;   // read first: it is what the player wants to hear
    if (!bestMove) {   // without a best move, who rolls next is read first (TODO-052)
      parts.push(`${rollWho(dice)}のは${NAME[r.on_roll]}の人です。`);
    } else {
      const who = `${NAME[r.on_roll]}の人、ダイス ${dice[0]} ${dice[1]}`;
      parts.push(r.moves.length
        ? `${who}の最善手は、${moveToSpeech(r.moves[0].move)}。`
        : `${who}では動かせる手がありません。`);
    }
    if (r.cube) {
      const c = r.cube, { word, take } = cubeWords(c);
      parts.push(c.question === "take"
        ? `${NAME[c.taker]}の人は${take}です。`
        : c.double ? `${NAME[c.doubler]}の人は${word}、${NAME[c.taker]}の人は${take}です。`
          : c.optional ? `${NAME[c.doubler]}の人は${word}してもしなくてもよいです。`
            : `${NAME[c.doubler]}の人はまだ${word}しません。`);
    }
    parts.push(r.game_over ? `${NAME[r.favourite]}の勝ちで終局しています。` : standingToSpeech(r));
    if (r.match) parts.push(`${matchText(r.match)}です。`);
    return parts.join("");
  }

  // The favourite's winning chance in words; a gammon or a big race lead only when it matters.
  function standingToSpeech(r) {
    const fav = r.favourite, p = r.probabilities[fav], pips = r.pips;
    const w = p.win;
    let s = w >= 90 ? `${NAME[fav]}がほぼ勝ちの局面です。`
      : w >= 75 ? `${NAME[fav]}がかなり有利です。`
        : w >= 60 ? `${NAME[fav]}が有利です。`
          : w >= 53 ? `${NAME[fav]}がやや有利です。`
            : "ほぼ互角です。";
    if (w >= 53 && p.gammon >= 25) s += "ギャモン勝ちも十分ありえます。";
    if (pips.leader && pips.difference >= 20) s += `レースは${NAME[pips.leader]}が大きくリードしています。`;
    return s;
  }

  // "bar/22* 13/8(2) 6/off" -> "バーから22でヒット、13から8を2つ、6から上がり"
  function moveToSpeech(move) {
    return move.trim().split(/\s+/).map((step) => {
      const m = step.match(/^(.*?)(?:\((\d+)\))?$/);
      const pts = m[1].split("/").map((x) => {
        const hit = x.endsWith("*");
        const n = x.replace("*", "").toLowerCase();
        return (n === "bar" ? "バー" : n === "off" ? "上がり" : n) + (hit ? "でヒット" : "");
      });
      return pts.join("から") + (m[2] ? `を${m[2]}つ` : "");
    }).join("、");
  }

  return { NAME, setNames, rollWho, esc, matchText, html, cubeHtml, speechText, moveToSpeech };
})();

if (typeof module !== "undefined") module.exports = BgResult;
