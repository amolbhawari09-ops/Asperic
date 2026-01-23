import type { Metadata } from "next";
import { Geist, Geist_Mono } from "next/font/google";
import "./globals.css";

/* ---------------- FONTS ---------------- */

const geistSans = Geist({
  variable: "--font-geist-sans",
  subsets: ["latin"],
});

const geistMono = Geist_Mono({
  variable: "--font-geist-mono",
  subsets: ["latin"],
});

/* ---------------- SEO METADATA ---------------- */

export const metadata: Metadata = {
  metadataBase: new URL("https://asperic.com"),

  title: {
    default: "Asperic — Reasoning-First AI",
    template: "%s | Asperic",
  },

  description:
    "Asperic is a reasoning-first AI system designed for precision, logic, and deterministic intelligence. Built for engineers, founders, and thinkers.",

  keywords: [
    "Asperic AI",
    "Reasoning AI",
    "Deterministic AI",
    "AI for engineers",
    "Logic-based AI",
    "AI assistant",
    "Artificial Intelligence",
  ],

  authors: [{ name: "Asperic Labs" }],
  creator: "Asperic Labs",
  applicationName: "Asperic",

  robots: {
    index: true,
    follow: true,
  },

  openGraph: {
    type: "website",
    siteName: "Asperic",
    title: "Asperic — Reasoning-First AI",
    description:
      "A professional-grade AI assistant focused on logic, accuracy, and deterministic reasoning.",
    url: "https://asperic.com",
    images: [
      {
        url: "/og.png",
        width: 1200,
        height: 630,
        alt: "Asperic AI",
      },
    ],
  },

  twitter: {
    card: "summary_large_image",
    title: "Asperic — Reasoning-First AI",
    description: "Precision-focused AI built for reasoning, not guessing.",
    images: ["/og.png"],
  },

  category: "technology",
};

/* ---------------- ROOT LAYOUT ---------------- */

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="en" suppressHydrationWarning>
      <head>
        {/* Mobile / Responsive */}
        <meta
          name="viewport"
          content="width=device-width, initial-scale=1, viewport-fit=cover"
        />

        {/* Mobile browser UI */}
        <meta name="theme-color" content="#000000" />
        <meta name="color-scheme" content="dark" />
      </head>

      <body
        className={`${geistSans.variable} ${geistMono.variable} antialiased bg-black text-gray-200`}
      >
        {children}
      </body>
    </html>
  );
}