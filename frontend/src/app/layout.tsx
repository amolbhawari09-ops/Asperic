import type { Metadata, Viewport } from "next";
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

  // 1. FIX: Title is now Asperic (fixes "Create Next App")
  title: {
    default: "Asperic",
    template: "%s | Asperic",
  },

  description:
    "Asperic is a reasoning-first AI system designed for precision, logic, and deterministic intelligence.",

  applicationName: "Asperic",

  // 2. FIX: Connects to your specific logo file from the screenshot
  icons: {
    icon: "/asperic-logo.png",
    apple: "/asperic-logo.png", 
  },

  // 3. FIX: Links to the manifest file for the "Install App" popup
  manifest: "/manifest.json",

  openGraph: {
    type: "website",
    siteName: "Asperic",
    title: "Asperic — Reasoning-First AI",
    description: "A professional-grade AI assistant.",
    url: "https://asperic.com",
    images: [
      {
        url: "/asperic-logo.png",
        width: 1200,
        height: 630,
        alt: "Asperic AI",
      },
    ],
  },
};

/* ---------------- VIEWPORT (Mobile Settings) ---------------- */

// 4. FIX: Correct way to handle mobile zooming and colors in Next.js
export const viewport: Viewport = {
  width: "device-width",
  initialScale: 1,
  maximumScale: 1,
  themeColor: "#000000",
  colorScheme: "dark",
};

/* ---------------- ROOT LAYOUT ---------------- */

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="en" suppressHydrationWarning>
      <body
        className={`${geistSans.variable} ${geistMono.variable} antialiased bg-black text-gray-200`}
      >
        {children}
      </body>
    </html>
  );
}
