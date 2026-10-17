// TODO-106: the spoken text for representative cases. usage: node archives/agents/TODO-106/speech_samples.js
const R = require("../../../analyzer/static/result.js");
const base = { on_roll: "white", favourite: "white", game_over: false, luck: null, cube: null, moves: null,
  probabilities: { white: { win: 62, gammon: 12 }, black: { win: 38, gammon: 5 } }, pips: { leader: null, difference: 0 } };
const cube = (o) => ({ doubler: "white", taker: "black", value: 1, take: true, double: false, optional: false, too_good: false, rolled: false, question: "double", ...o });
const cases = [
  ["ダイスあり・最善手", { ...base, moves: [{ move: "bar/22* 13/8(2) 6/off" }] }, [5, 3]],
  ["ダイスあり・とても良い目", { ...base, moves: [{ move: "24/18 13/8" }], luck: 0.7 }, [6, 5]],
  ["ダイスあり・悪い目", { ...base, moves: [{ move: "8/5 6/5" }], luck: -0.4 }, [3, 1]],
  ["ダイスあり・動かせない", { ...base, moves: [] }, [6, 6]],
  ["ダイスなし", { ...base }, null],
  ["ダブルする・テイク", { ...base, cube: cube({ double: true }) }, null],
  ["ダブルする・パス", { ...base, cube: cube({ double: true, take: false }) }, null],
  ["してもしなくてもよい", { ...base, cube: cube({ optional: true }) }, null],
  ["まだダブルしない", { ...base, cube: cube({}) }, null],
  ["ギャモン狙いでダブルしない", { ...base, cube: cube({ too_good: true, take: false }) }, null],
  ["リダブル・テイクの質問", { ...base, cube: cube({ question: "take", value: 2, double: true }) }, null],
  ["振る前にダブルすべきだった", { ...base, moves: [{ move: "24/18 13/8" }], cube: cube({ rolled: true, double: true }) }, [6, 5]],
  ["ほぼ勝ち・ギャモン・レース", { ...base, probabilities: { white: { win: 92, gammon: 30 }, black: { win: 8, gammon: 0 } }, pips: { leader: "white", difference: 35 } }, null],
  ["ほぼ互角", { ...base, probabilities: { white: { win: 51, gammon: 10 }, black: { win: 49, gammon: 9 } } }, null],
  ["終局", { ...base, game_over: true }, null],
];
for (const [name, r, dice] of cases) console.log(`- ${name}: ${R.speechText(r, dice)}`);
