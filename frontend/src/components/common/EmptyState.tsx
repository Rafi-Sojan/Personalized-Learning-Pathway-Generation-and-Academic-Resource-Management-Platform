/** Render a consistent neutral message when a collection has no entries. */
export function EmptyState({ message }: { message: string }) {
  return <div className="empty-state">{message}</div>
}
