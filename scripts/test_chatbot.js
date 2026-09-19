// Usage: node scripts/test_chatbot.js
const { findAnswer } = require('../assets/chatbot.js');
const fallback = "I'm not totally sure";
const greeting = "Hi there!";
const cases = [
  ['this', a => a.startsWith(fallback)],
  ['which', a => a.startsWith(fallback)],
  ['history', a => a.startsWith(fallback)],
  ['hi', a => a.startsWith(greeting)],
  ['hello', a => a.startsWith(greeting)],
  ['HI!', a => a.startsWith(greeting)],
  ['tell me about advertising', a => a.includes('SEO & Content')],
  ['what are your prices', a => a.includes('Pricing depends')],
];
let fail = 0;
for (const [input, check] of cases) {
  const ans = findAnswer(input);
  const ok = check(ans);
  if (!ok) fail++;
  console.log((ok ? 'PASS' : 'FAIL') + '  "' + input + '" -> ' + ans.slice(0, 40));
}
process.exit(fail ? 1 : 0);
