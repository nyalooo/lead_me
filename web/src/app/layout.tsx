import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: "LeadMe - Smart Traffic Routing for Mumbai",
  description:
    "Get assigned the best route, earn XRP rewards for reducing Mumbai traffic.",
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="en" className="h-full antialiased">
      <body className="min-h-full flex flex-col bg-gray-50 text-gray-900 font-sans">
        {children}
      </body>
    </html>
  );
}
