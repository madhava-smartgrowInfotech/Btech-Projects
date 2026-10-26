// Offline evaluation of the SafePhrase matcher (frontend/src/lib/safephrase.ts) on written transcripts.
// The real matcher is transpiled with the project's own TypeScript and run unchanged. The transcripts are
// hand-written stand-ins for what a speech recogniser could return; no audio and no recogniser is involved,
// so this measures the matching rule only, not speech recognition.
//
//   node scripts/safephrase_eval.mjs      (writes experiments/study/safephrase.json)
import fs from 'node:fs';
import path from 'node:path';
import { createRequire } from 'node:module';
import { fileURLToPath, pathToFileURL } from 'node:url';

const root = path.resolve(path.dirname(fileURLToPath(import.meta.url)), '..');
const require = createRequire(path.join(root, 'frontend', 'package.json'));
const ts = require('typescript');
const src = fs.readFileSync(path.join(root, 'frontend/src/lib/safephrase.ts'), 'utf8');
const js = ts.transpileModule(src, { compilerOptions: { module: ts.ModuleKind.ESNext, target: ts.ScriptTarget.ES2020 } }).outputText;
const tmp = path.join(root, 'experiments', 'study', '_safephrase.mjs');
fs.mkdirSync(path.dirname(tmp), { recursive: true });
fs.writeFileSync(tmp, js);
const { matchSafePhrase, SENSITIVITY_THRESHOLD } = await import(pathToFileURL(tmp).href);
fs.unlinkSync(tmp);

const PHRASES = [
  'help me sheguard',
  'please call my brother now',
];
const phraseItem = (p) => [{ id: 'x', phrase: p, label: 'x', fingerprint: '', enabled: true, createdAt: '' }];

// positives per phrase (each is a transcript that SHOULD trigger an SOS)
const positives = {
  'help me sheguard': {
    exact: ['help me sheguard', 'Help me, SheGuard!', 'HELP ME SHEGUARD'],
    embedded: ['hey um help me sheguard right now', 'oh no help me sheguard please', 'i think help me sheguard is what i should say'],
    one_word_dropped: ['help sheguard', 'me sheguard', 'help me'],
    one_word_misheard: ['help me she guard', 'help me shield guard', 'yelp me sheguard'],
    reordered: ['sheguard help me', 'me help sheguard'],
  },
  'please call my brother now': {
    exact: ['please call my brother now', 'Please, call my brother now.'],
    embedded: ['um please call my brother now okay', 'i said please call my brother now'],
    one_word_dropped: ['please call brother now', 'call my brother now', 'please call my brother'],
    one_word_misheard: ['please call my brothel now', 'please fall my brother now'],
    reordered: ['now please call my brother'],
  },
};
// negatives: ordinary speech that must NOT trigger an SOS
const negatives = [
  'can you help me with my homework', 'please help me find my keys', 'tell me about sheguard', 'is sheguard installed on this phone',
  'help is on the way', 'let me know when you reach home', 'i will call my mother tonight', 'my brother is coming now',
  'please close the door', 'what time is it now', 'she guards the gate every morning', 'the guard asked me to wait',
  'could you call me back later', 'i need to buy milk and bread', 'the bus will arrive in ten minutes', 'see you at the station',
  'please send me the address', 'my phone is almost out of battery', 'let us walk to the market', 'good evening everyone',
  'help me', 'help', 'me', 'sheguard', 'call my brother', 'please call', 'please call me now', 'call my sister now',
  'i am going to the library', 'turn left at the next signal', 'can you hear me', 'nice weather today', 'thank you very much',
  'happy birthday to you', 'where is the nearest pharmacy', 'she called her brother yesterday', 'please wait for me here',
  'my brother lives in another city', 'do not forget the tickets', 'the meeting starts now',
];

const out = { thresholds: SENSITIVITY_THRESHOLD, n_negative_transcripts: negatives.length, by_sensitivity: {} };
for (const sens of Object.keys(SENSITIVITY_THRESHOLD)) {
  const cats = {};
  let tp = 0, pos = 0;
  for (const phrase of PHRASES) {
    for (const [cat, list] of Object.entries(positives[phrase])) {
      for (const t of list) {
        const hit = !!matchSafePhrase(t, phraseItem(phrase), sens);
        cats[cat] = cats[cat] || { hit: 0, n: 0 };
        cats[cat].n++; cats[cat].hit += hit ? 1 : 0;
        pos++; tp += hit ? 1 : 0;
      }
    }
  }
  const fps = [];
  for (const t of negatives) {
    for (const phrase of PHRASES) {
      if (matchSafePhrase(t, phraseItem(phrase), sens)) fps.push({ transcript: t, phrase });
    }
  }
  out.by_sensitivity[sens] = {
    positive_transcripts: pos, triggered: tp, recall: +(tp / pos).toFixed(3), by_category: cats,
    negative_checks: negatives.length * PHRASES.length, false_triggers: fps.length,
    false_trigger_rate: +(fps.length / (negatives.length * PHRASES.length)).toFixed(3), false_trigger_examples: fps.slice(0, 8),
  };
}
// matching cost
const t0 = process.hrtime.bigint();
for (let i = 0; i < 20000; i++) matchSafePhrase('hey um please help me sheguard right now ok', phraseItem('help me sheguard'), 'Medium');
out.match_microseconds = +(Number(process.hrtime.bigint() - t0) / 20000 / 1000).toFixed(2);
fs.writeFileSync(path.join(root, 'experiments', 'study', 'safephrase.json'), JSON.stringify(out, null, 2));
console.log(JSON.stringify(out, null, 1));
