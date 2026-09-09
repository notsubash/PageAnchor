import type { Metadata } from "next";
import type { ReactNode } from "react";
import { Azeret_Mono, Barlow, Barlow_Condensed } from "next/font/google";

import "./globals.css";

const barlow = Barlow({
  subsets: ["latin"],
  weight: ["400", "500", "600"],
  variable: "--font-barlow",
});

const condensed = Barlow_Condensed({
  subsets: ["latin"],
  weight: ["500", "600", "700"],
  variable: "--font-condensed",
});

const mono = Azeret_Mono({
  subsets: ["latin"],
  weight: ["400", "500", "600"],
  variable: "--font-mono",
});

export const metadata: Metadata = {
  title: "PageAnchor",
  description: "Every answer cites a verifiable page region, or it refuses.",
};

const CONTRACT = `<!--
THESIS: The page is a film frame in a lighted gate; a citation is a matte finder reticle; a refusal is NO FRAME. This refuses equal three-column chat / PDF / sources cards.
OWN-WORLD: Charcoal flocked hood, olive-gray enamel bezels, putty catalog insets, sprocket edges, tabular frame counters, matte cadmium reticle. Condensed industrial sans on the machine; mono only for measurements.
STORY: Load a query on the left bezel, prove it in the gate, read the index strip. Believe a boxed quote or a stamped refuse.
FIRST VIEWPORT: Top enamel wordmark and frame counter. Left catalog ~22%. Center gate dominates. Right TRACE strip. Primary action is LOAD FRAME.
FORM: Microfilm reader, grounded list #7, seed key f9aa56ba.
FINISH: finish review disposition fix (round 2). DESIGN.md recorded. Remaining: stamp LOAD FRAME into the plate raster; labeled ANSWER plate raster; STRICT latch that does not read as a UI slider; NO FRAME as a stamp on the gate, not a nested card with caption.
-->`;

export default function RootLayout({ children }: { children: ReactNode }) {
  return (
    <html lang="en" className={`${barlow.variable} ${condensed.variable} ${mono.variable}`}>
      <body>
        <div dangerouslySetInnerHTML={{ __html: CONTRACT }} />
        {children}
      </body>
    </html>
  );
}
