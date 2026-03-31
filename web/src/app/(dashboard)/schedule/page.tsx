"use client";

import { useEffect, useState } from "react";
import { getSchedules, createSchedule } from "@/lib/api";
import { getToken } from "@/lib/auth";

type ScheduleItem = {
  id: string;
  type: string;
  origin: { lat: number; lng: number; label?: string };
  destination: { lat: number; lng: number; label?: string };
  days?: string[];
  departure_time?: string;
  active: boolean;
};

const DAYS = ["mon", "tue", "wed", "thu", "fri", "sat", "sun"];
const DAY_LABELS: Record<string, string> = {
  mon: "Mon",
  tue: "Tue",
  wed: "Wed",
  thu: "Thu",
  fri: "Fri",
  sat: "Sat",
  sun: "Sun",
};

export default function SchedulePage() {
  const token = getToken();
  const [schedules, setSchedules] = useState<ScheduleItem[]>([]);
  const [showForm, setShowForm] = useState(false);
  const [loading, setLoading] = useState(false);

  // Form state
  const [originLabel, setOriginLabel] = useState("");
  const [destLabel, setDestLabel] = useState("");
  const [selectedDays, setSelectedDays] = useState<string[]>(["mon", "tue", "wed", "thu", "fri"]);
  const [departureTime, setDepartureTime] = useState("08:30");

  useEffect(() => {
    if (!token) return;
    getSchedules(token)
      .then((res) => setSchedules(res.schedules as ScheduleItem[]))
      .catch(console.error);
  }, [token]);

  async function handleCreate(e: React.FormEvent) {
    e.preventDefault();
    if (!token) return;
    setLoading(true);
    try {
      // Demo coordinates (Andheri → BKC)
      await createSchedule(
        {
          type: "recurring",
          origin: { lat: 19.1196, lng: 72.8464, label: originLabel || "Home" },
          destination: { lat: 19.0596, lng: 72.8656, label: destLabel || "Office" },
          days: selectedDays,
          departure_time: departureTime,
        },
        token,
      );
      // Refresh
      const res = await getSchedules(token);
      setSchedules(res.schedules as ScheduleItem[]);
      setShowForm(false);
    } catch (err) {
      console.error(err);
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="max-w-3xl mx-auto space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold">Schedules</h1>
          <p className="text-gray-500 text-sm mt-1">
            Pre-plan your commutes for advance route assignment
          </p>
        </div>
        <button
          onClick={() => setShowForm(!showForm)}
          className="rounded-lg bg-emerald-600 text-white px-4 py-2 text-sm font-medium hover:bg-emerald-700 transition"
        >
          {showForm ? "Cancel" : "+ New Schedule"}
        </button>
      </div>

      {/* Create form */}
      {showForm && (
        <form
          onSubmit={handleCreate}
          className="bg-white rounded-xl border border-gray-200 p-6 space-y-4"
        >
          <h2 className="font-semibold">New Recurring Schedule</h2>
          <div className="grid grid-cols-2 gap-4">
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                Origin Label
              </label>
              <input
                value={originLabel}
                onChange={(e) => setOriginLabel(e.target.value)}
                placeholder="Home"
                className="w-full rounded-lg border border-gray-300 px-3 py-2 text-sm outline-none focus:border-emerald-500"
              />
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                Destination Label
              </label>
              <input
                value={destLabel}
                onChange={(e) => setDestLabel(e.target.value)}
                placeholder="Office"
                className="w-full rounded-lg border border-gray-300 px-3 py-2 text-sm outline-none focus:border-emerald-500"
              />
            </div>
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              Days
            </label>
            <div className="flex gap-2">
              {DAYS.map((day) => (
                <button
                  key={day}
                  type="button"
                  onClick={() =>
                    setSelectedDays((prev) =>
                      prev.includes(day)
                        ? prev.filter((d) => d !== day)
                        : [...prev, day],
                    )
                  }
                  className={`w-10 h-10 rounded-full text-xs font-medium transition ${
                    selectedDays.includes(day)
                      ? "bg-emerald-600 text-white"
                      : "bg-gray-100 text-gray-600 hover:bg-gray-200"
                  }`}
                >
                  {DAY_LABELS[day]}
                </button>
              ))}
            </div>
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              Departure Time
            </label>
            <input
              type="time"
              value={departureTime}
              onChange={(e) => setDepartureTime(e.target.value)}
              className="rounded-lg border border-gray-300 px-3 py-2 text-sm outline-none focus:border-emerald-500"
            />
          </div>

          <button
            type="submit"
            disabled={loading}
            className="rounded-lg bg-emerald-600 text-white px-6 py-2.5 text-sm font-medium hover:bg-emerald-700 transition disabled:opacity-50"
          >
            {loading ? "Creating..." : "Create Schedule"}
          </button>
        </form>
      )}

      {/* Schedule list */}
      {schedules.length === 0 ? (
        <div className="bg-white rounded-xl border border-gray-200 p-12 text-center">
          <p className="text-gray-400 mb-2">No schedules yet</p>
          <p className="text-sm text-gray-400">
            Create a recurring schedule to get routes assigned before you leave
          </p>
        </div>
      ) : (
        <div className="space-y-3">
          {schedules.map((schedule) => (
            <div
              key={schedule.id}
              className="bg-white rounded-xl border border-gray-200 p-4 flex items-center justify-between"
            >
              <div>
                <div className="font-medium text-sm">
                  {schedule.origin.label ?? "Origin"} → {schedule.destination.label ?? "Destination"}
                </div>
                <div className="text-xs text-gray-500 mt-1">
                  {schedule.days?.map((d) => DAY_LABELS[d]).join(", ")} at{" "}
                  {schedule.departure_time}
                </div>
              </div>
              <div className="flex items-center gap-2">
                <span
                  className={`text-xs px-2 py-1 rounded-full ${
                    schedule.active
                      ? "bg-green-100 text-green-700"
                      : "bg-gray-100 text-gray-500"
                  }`}
                >
                  {schedule.active ? "Active" : "Paused"}
                </span>
              </div>
            </div>
          ))}
        </div>
      )}

      {/* Info box */}
      <div className="bg-blue-50 rounded-xl border border-blue-200 p-4 text-sm text-blue-800">
        <strong>Bonus:</strong> Scheduling upfront earns extra Route Coins because it
        helps the system plan better traffic distribution.
      </div>
    </div>
  );
}
