import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: "AI Resume & Job Matcher",
  description: "Analyze resume fit against job descriptions with AI.",
};

export default function RootLayout({ children }: Readonly<{ children: React.ReactNode }>) {
  return (
    <html lang="en">
      <body>{children}</body>
    </html>
  );
}
