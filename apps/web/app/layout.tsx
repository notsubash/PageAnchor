import type { Metadata } from "next";
import type { ReactNode } from "react";
import { Geist, Geist_Mono } from "next/font/google";

import "./globals.css";

const sans = Geist({
  subsets: ["latin"],
  variable: "--font-sans",
});

const mono = Geist_Mono({
  subsets: ["latin"],
  variable: "--font-mono",
});

export const metadata: Metadata = {
  title: "PageAnchor",
  description: "Every answer cites a verifiable page region, or it refuses.",
};

const CONTRACT = `<!--
THESIS: PageAnchor is a dark operator workbench: ask on the left, prove it on the page, inspect Trace on the right. This refuses the microfilm reader and equal chat / PDF / sources cards.
OWN-WORLD: Near-black zinc panels, 1px hairlines, 6px corners, Geist and Geist Mono, white Ask, blue only for selection and verified. No enamel, sprockets, putty, or cadmium chrome.
STORY: Type a question, Ask, believe a boxed region on the page or a refusal. Citations select the region. Trace is the index.
FIRST VIEWPORT: 48px top bar with wordmark, thesis, page readout, Receipt. Left ~22% Ask and citations. Center document canvas dominates. Right ~22% Trace. Primary action is Ask.
FORM: Platform workbench, Linear + Vercel canon, user-pinned. No concept-seed roll.
FINISH: unreviewed and undocumented is unfinished; this build ends with the finish review, the verdict, and DESIGN.md
-->`;

export default function RootLayout({ children }: { children: ReactNode }) {
  return (
    <html lang="en" className={`${sans.variable} ${mono.variable}`}>
      <body>
        <div dangerouslySetInnerHTML={{ __html: CONTRACT }} />
        {children}
      </body>
    </html>
  );
}
