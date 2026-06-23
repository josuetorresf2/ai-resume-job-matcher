export function scoreLabel(score: number, language: "en" | "es" = "en"): string {
  if (language === "es") {
    if (score >= 85) return "Alta coincidencia";
    if (score >= 65) return "Buena coincidencia";
    if (score >= 45) return "Coincidencia parcial";
    return "Necesita enfoque";
  }
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
