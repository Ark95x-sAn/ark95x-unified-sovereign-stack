import type { Metadata } from "next";
import type { ReactNode } from "react";
import "./globals.css";

export const metadata: Metadata = { title: "DM Calling — Local Demo", description: "Local-first Next.js DM voice/video calling demo modeled on X's DM flow. Sample data only." };

export default function RootLayout({ children }: { children: ReactNode }) {
  return (<html lang="en"><body>{children}</body></html>);
}
