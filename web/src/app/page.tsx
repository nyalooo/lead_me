import Link from "next/link";

export default function HomePage() {
  return (
    <div className="flex flex-col min-h-screen">
      {/* Hero */}
      <header className="bg-gradient-to-br from-emerald-600 to-teal-700 text-white">
        <nav className="max-w-6xl mx-auto flex items-center justify-between px-6 py-4">
          <h1 className="text-2xl font-bold tracking-tight">LeadMe</h1>
          <Link
            href="/login"
            className="rounded-lg bg-white/20 px-4 py-2 text-sm font-medium backdrop-blur hover:bg-white/30 transition"
          >
            Login
          </Link>
        </nav>

        <div className="max-w-6xl mx-auto px-6 py-20 text-center">
          <h2 className="text-4xl md:text-5xl font-bold leading-tight mb-6">
            Beat Mumbai Traffic.
            <br />
            Earn XRP Rewards.
          </h2>
          <p className="text-lg md:text-xl text-emerald-100 max-w-2xl mx-auto mb-10">
            LeadMe assigns you the smartest route based on real-time traffic
            load. Follow it, reduce congestion for everyone, and earn crypto
            rewards.
          </p>
          <Link
            href="/login"
            className="inline-block rounded-xl bg-white text-emerald-700 px-8 py-3 text-lg font-semibold shadow-lg hover:shadow-xl hover:scale-105 transition-all"
          >
            Get Started
          </Link>
        </div>
      </header>

      {/* Features */}
      <main className="max-w-6xl mx-auto px-6 py-16 flex-1">
        <div className="grid md:grid-cols-3 gap-8">
          <FeatureCard
            title="Smart Route Assignment"
            description="We don't just show the shortest route — we distribute traffic across all viable routes so everyone gets there faster."
            icon="🗺️"
          />
          <FeatureCard
            title="Schedule Upfront"
            description="Set your daily commute and get your route assigned before you leave. Know your path ahead of time."
            icon="📅"
          />
          <FeatureCard
            title="Earn XRP Rewards"
            description="Follow your assigned route, build streaks, earn Route Coins, and convert them to XRP cryptocurrency."
            icon="💰"
          />
          <FeatureCard
            title="Real-time Traffic Load"
            description="See how busy each route is with our weighted commuter average — clear, moderate, or busy at a glance."
            icon="📊"
          />
          <FeatureCard
            title="Gamification"
            description="Earn badges, climb the leaderboard, and level up from Rookie to Legend. Compete with your area."
            icon="🏆"
          />
          <FeatureCard
            title="Mumbai First"
            description="Built specifically for Mumbai commuters. We understand the Western Express, SV Road, and Link Road like you do."
            icon="🏙️"
          />
        </div>

        {/* How it works */}
        <section className="mt-20">
          <h3 className="text-2xl font-bold text-center mb-12">How It Works</h3>
          <div className="grid md:grid-cols-4 gap-6">
            {[
              { step: "1", title: "Enter Route", desc: "Pick your origin and destination" },
              { step: "2", title: "Get Assigned", desc: "System picks the optimal route for you" },
              { step: "3", title: "Follow Route", desc: "GPS tracks your compliance" },
              { step: "4", title: "Earn Rewards", desc: "Get Route Coins convertible to XRP" },
            ].map((item) => (
              <div key={item.step} className="text-center">
                <div className="w-12 h-12 rounded-full bg-emerald-100 text-emerald-700 font-bold text-xl flex items-center justify-center mx-auto mb-3">
                  {item.step}
                </div>
                <h4 className="font-semibold mb-1">{item.title}</h4>
                <p className="text-sm text-gray-500">{item.desc}</p>
              </div>
            ))}
          </div>
        </section>
      </main>

      {/* Footer */}
      <footer className="bg-gray-900 text-gray-400 text-center py-8 text-sm">
        <p>LeadMe — Reducing Mumbai traffic, one route at a time.</p>
      </footer>
    </div>
  );
}

function FeatureCard({
  title,
  description,
  icon,
}: {
  title: string;
  description: string;
  icon: string;
}) {
  return (
    <div className="rounded-xl border border-gray-200 bg-white p-6 shadow-sm hover:shadow-md transition">
      <div className="text-3xl mb-3">{icon}</div>
      <h3 className="font-semibold text-lg mb-2">{title}</h3>
      <p className="text-sm text-gray-500 leading-relaxed">{description}</p>
    </div>
  );
}
