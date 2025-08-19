export default function FeedbackFab({ onClick }: { onClick: () => void }) {
  return (
    <button
      onClick={onClick}
      className="fixed right-4 bottom-4 z-[998] rounded-full bg-emerald-600 hover:bg-emerald-700 shadow-lg px-4 py-3 text-sm font-semibold"
      aria-label="问题反馈"
      title="问题反馈 / 留言板"
    >
      📝 问题反馈
    </button>
  );
}
