export default function GlobalLoading() {
  return (
    <main className="min-h-screen bg-india-radial flex items-center justify-center">
      <div className="flex items-center gap-3 text-navy-text/70">
        <div className="w-10 h-10 border-4 border-saffron-200 border-t-saffron-600 rounded-full animate-spin" />
        <span className="font-medium">Loading…</span>
      </div>
    </main>
  );
}
