"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
import { requestOtp, verifyOtp } from "@/lib/api";
import { setAuth } from "@/lib/auth";

export default function LoginPage() {
  const router = useRouter();
  const [phone, setPhone] = useState("+91");
  const [otp, setOtp] = useState("");
  const [step, setStep] = useState<"phone" | "otp">("phone");
  const [devOtp, setDevOtp] = useState<string | null>(null);
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);

  async function handleRequestOtp(e: React.FormEvent) {
    e.preventDefault();
    setError("");
    setLoading(true);
    try {
      const res = await requestOtp(phone);
      if (res.dev_otp) setDevOtp(res.dev_otp);
      setStep("otp");
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to send OTP");
    } finally {
      setLoading(false);
    }
  }

  async function handleVerifyOtp(e: React.FormEvent) {
    e.preventDefault();
    setError("");
    setLoading(true);
    try {
      const res = await verifyOtp(phone, otp);
      setAuth(res.access_token, res.user);
      router.push("/dashboard");
    } catch (err) {
      setError(err instanceof Error ? err.message : "Invalid OTP");
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="min-h-screen flex items-center justify-center bg-gradient-to-br from-emerald-600 to-teal-700 px-4">
      <div className="w-full max-w-sm bg-white rounded-2xl shadow-xl p-8">
        <h1 className="text-2xl font-bold text-center mb-2">LeadMe</h1>
        <p className="text-gray-500 text-center text-sm mb-8">
          Login with your phone number
        </p>

        {step === "phone" ? (
          <form onSubmit={handleRequestOtp} className="space-y-4">
            <div>
              <label htmlFor="phone" className="block text-sm font-medium text-gray-700 mb-1">
                Phone Number
              </label>
              <input
                id="phone"
                type="tel"
                value={phone}
                onChange={(e) => setPhone(e.target.value)}
                placeholder="+919876543210"
                className="w-full rounded-lg border border-gray-300 px-4 py-2.5 text-sm focus:border-emerald-500 focus:ring-1 focus:ring-emerald-500 outline-none"
                required
              />
            </div>
            {error && <p className="text-red-500 text-sm">{error}</p>}
            <button
              type="submit"
              disabled={loading}
              className="w-full rounded-lg bg-emerald-600 text-white py-2.5 font-medium hover:bg-emerald-700 transition disabled:opacity-50"
            >
              {loading ? "Sending..." : "Send OTP"}
            </button>
          </form>
        ) : (
          <form onSubmit={handleVerifyOtp} className="space-y-4">
            <p className="text-sm text-gray-500">
              OTP sent to <strong>{phone}</strong>
            </p>
            {devOtp && (
              <p className="text-xs bg-amber-50 border border-amber-200 rounded-lg px-3 py-2 text-amber-700">
                Dev mode OTP: <strong>{devOtp}</strong>
              </p>
            )}
            <div>
              <label htmlFor="otp" className="block text-sm font-medium text-gray-700 mb-1">
                Enter OTP
              </label>
              <input
                id="otp"
                type="text"
                value={otp}
                onChange={(e) => setOtp(e.target.value)}
                placeholder="123456"
                maxLength={6}
                className="w-full rounded-lg border border-gray-300 px-4 py-2.5 text-sm text-center tracking-widest focus:border-emerald-500 focus:ring-1 focus:ring-emerald-500 outline-none"
                required
              />
            </div>
            {error && <p className="text-red-500 text-sm">{error}</p>}
            <button
              type="submit"
              disabled={loading}
              className="w-full rounded-lg bg-emerald-600 text-white py-2.5 font-medium hover:bg-emerald-700 transition disabled:opacity-50"
            >
              {loading ? "Verifying..." : "Verify & Login"}
            </button>
            <button
              type="button"
              onClick={() => { setStep("phone"); setError(""); }}
              className="w-full text-sm text-gray-500 hover:text-gray-700"
            >
              Change phone number
            </button>
          </form>
        )}
      </div>
    </div>
  );
}
