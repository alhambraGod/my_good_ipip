import type { Metadata } from "next";
import { Geist, Geist_Mono } from "next/font/google";
import "./globals.css";
import { ToastProvider } from "@/components/Toast";

const geistSans = Geist({
  variable: "--font-geist-sans",
  subsets: ["latin"],
});

const geistMono = Geist_Mono({
  variable: "--font-geist-mono",
  subsets: ["latin"],
});

const SITE_URL = (process.env.NEXT_PUBLIC_SITE_URL || "http://localhost:3000").replace(/\/$/, "");

export const metadata: Metadata = {
  metadataBase: new URL(SITE_URL),
  title: {
    default: "CareerDNA India — Find your archetype in 5 minutes",
    template: "%s | CareerDNA India",
  },
  description:
    "Holland RIASEC + Big Five (OCEAN) career mapping built for Indian Gen-Z. 45 questions, 5 minutes, archetype + career match in lakh-based salary ranges.",
  keywords: [
    "career test India",
    "personality test India",
    "Holland RIASEC",
    "Big Five OCEAN",
    "IPIP-NEO",
    "Indian career guidance",
    "WhatsApp share quiz",
  ],
  openGraph: {
    title: "CareerDNA India — Find your archetype in 5 minutes",
    description:
      "Holland + OCEAN, India-tuned. Archetype + careers + share lines, in 45 questions.",
    url: SITE_URL,
    type: "website",
    siteName: "CareerDNA India",
  },
  twitter: {
    card: "summary_large_image",
    title: "CareerDNA India",
    description: "Holland + OCEAN, India-tuned. Find your archetype in 5 minutes.",
  },
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html
      lang="en"
      className={`${geistSans.variable} ${geistMono.variable} h-full antialiased scroll-smooth`}
    >
      <head>
        <meta
          name="viewport"
          content="width=device-width, initial-scale=1, viewport-fit=cover"
        />
      </head>
      <body className="min-h-full flex flex-col bg-cream text-navy-text selection:bg-saffron-200/60">
        <ToastProvider>{children}</ToastProvider>
      </body>
    </html>
  );
}
