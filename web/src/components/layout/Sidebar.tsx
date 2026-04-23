"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";

const NAV_ITEMS = [
  { href: "/dashboard", label: "Dashboard", icon: "📍" },
  { href: "/schedule", label: "Schedule", icon: "📅" },
  { href: "/challenges", label: "Challenges", icon: "🎯" },
  { href: "/referrals", label: "Invite", icon: "👥" },
  { href: "/cashout", label: "Cashout", icon: "💰" },
  { href: "/leaderboard", label: "Leaderboard", icon: "🏆" },
  { href: "/profile", label: "Profile", icon: "👤" },
];

export default function Sidebar() {
  const pathname = usePathname();

  return (
    <aside className="w-64 bg-white border-r border-gray-200 flex flex-col min-h-screen">
      <div className="px-6 py-5 border-b border-gray-200">
        <Link href="/dashboard" className="text-xl font-bold text-emerald-600">
          LeadMe
        </Link>
      </div>

      <nav className="flex-1 px-3 py-4 space-y-1">
        {NAV_ITEMS.map((item) => {
          const active = pathname === item.href;
          return (
            <Link
              key={item.href}
              href={item.href}
              className={`flex items-center gap-3 rounded-lg px-3 py-2.5 text-sm font-medium transition ${
                active
                  ? "bg-emerald-50 text-emerald-700"
                  : "text-gray-600 hover:bg-gray-50 hover:text-gray-900"
              }`}
            >
              <span className="text-lg">{item.icon}</span>
              {item.label}
            </Link>
          );
        })}
      </nav>

      <div className="px-3 py-4 border-t border-gray-200">
        <Link
          href="/login"
          className="flex items-center gap-3 rounded-lg px-3 py-2.5 text-sm font-medium text-gray-600 hover:bg-gray-50 hover:text-gray-900 transition"
          onClick={() => {
            if (typeof window !== "undefined") {
              localStorage.removeItem("leadme_token");
              localStorage.removeItem("leadme_user");
            }
          }}
        >
          <span className="text-lg">🚪</span>
          Logout
        </Link>
      </div>
    </aside>
  );
}
