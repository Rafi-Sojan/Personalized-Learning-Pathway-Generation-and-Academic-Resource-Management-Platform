/** Format a date in the browser's local calendar for activity grouping. */
export function getLocalDayKey(value: Date): string {
  return `${value.getFullYear()}-${String(value.getMonth() + 1).padStart(2, '0')}-${String(value.getDate()).padStart(2, '0')}`
}

/** Count consecutive active local-calendar days, allowing activity today or yesterday. */
export function calculateCurrentStreak(activityTimestamps: string[], today = new Date()): number {
  const activeDays = new Set(activityTimestamps.map((timestamp) => getLocalDayKey(new Date(timestamp))))
  const cursor = new Date(today.getFullYear(), today.getMonth(), today.getDate())

  if (!activeDays.has(getLocalDayKey(cursor))) cursor.setDate(cursor.getDate() - 1)
  let streak = 0
  while (activeDays.has(getLocalDayKey(cursor))) {
    streak += 1
    cursor.setDate(cursor.getDate() - 1)
  }
  return streak
}
