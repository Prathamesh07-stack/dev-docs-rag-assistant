import type { Metadata } from "next";
import { Geist, Geist_Mono } from "next/font/google";
import { Sidebar } from "@/components/Sidebar";
import "./globals.css";

const geistSans = Geist({ variable: "--font-geist-sans", subsets: ["latin"] });
const geistMono = Geist_Mono({ variable: "--font-geist-mono", subsets: ["latin"] });

export const metadata: Metadata = {
  title: "RAG Documentation Assistant",
  description: "Ask questions about your engineering docs — grounded answers with citations.",
};

export default function RootLayout({ children }: Readonly<{ children: React.ReactNode }>) {
  return (
    <html lang="en">
      <body className={`${geistSans.variable} ${geistMono.variable}`} style={{
        margin: 0, height: "100%", display: "grid",
        gridTemplateColumns: "220px 1fr",
        background: "var(--bg-base)", color: "var(--text-primary)",
        fontFamily: "var(--font-geist-sans), system-ui, sans-serif",
      }}>
        <Sidebar />
        <main style={{ overflow: "hidden", display: "flex", flexDirection: "column", height: "100vh" }}>
          {children}
        </main>
      </body>
    </html>
  );
}
