import assert from "node:assert/strict";
import test from "node:test";

function scoreLabel(score) {
  if (score >= 85) return "Strong match";
  if (score >= 65) return "Good match";
  if (score >= 45) return "Partial match";
  return "Needs targeting";
}

test("score labels communicate match quality", () => {
  assert.equal(scoreLabel(92), "Strong match");
  assert.equal(scoreLabel(74), "Good match");
  assert.equal(scoreLabel(50), "Partial match");
  assert.equal(scoreLabel(20), "Needs targeting");
});
