export function scoreLabel(score: number): string {
  if (score >= 85) return "Strong match";
  if (score >= 65) return "Good match";
  if (score >= 45) return "Partial match";
  return "Needs targeting";
}

export function scoreTone(score: number): string {
  if (score >= 85) return "excellent";
  if (score >= 65) return "good";
  if (score >= 45) return "medium";
  return "low";
}
