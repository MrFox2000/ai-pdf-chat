import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: "AI PDF Chat — ask your documents anything",
  description:
    "Upload a PDF and ask questions about it. Answers stream token by token and cite the page they came from.",
};

export default function RootLayout({
  children,
}: Readonly<{ children: React.ReactNode }>) {
  return (
    <html lang="en">
      <body className="min-h-dvh antialiased">{children}</body>
    </html>
  );
}
