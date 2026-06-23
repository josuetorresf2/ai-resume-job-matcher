import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: "New Free Talent Pool",
  description: "A free AI-powered recruiting platform for candidates and small companies in underserved markets.",
};

export default function RootLayout({ children }: Readonly<{ children: React.ReactNode }>) {
  return (
    <html lang="en">
      <body>{children}</body>
    </html>
  );
}
