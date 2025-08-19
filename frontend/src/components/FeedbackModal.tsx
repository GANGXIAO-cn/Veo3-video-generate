import { useEffect, useState } from "react";

type Feedback = {
  id: string;
  nickname: string;
  message: string;
  created_at: string; // ISO
};

export default function FeedbackModal({
  apiBase,
  open,
  onClose,
}: {
  apiBase: string;
  open: boolean;
  onClose: () => void;
}) {
  const [list, setList] = useState<Feedback[]>([]);
  const [nickname, setNickname] = useState("");
  const [message, setMessage] = useState("");
  const [posting, setPosting] = useState(false);
  const [loading, setLoading] = useState(false);

  // 拉取留言列表
  useEffect(() => {
    if (!open) return;
    setLoading(true);
    fetch(`${apiBase}/feedback`)
      .then((r) => r.json())
      .then((data) => setList(data))
      .catch(() => {})
      .finally(() => setLoading(false));
  }, [open, apiBase]);

  const submit = async () => {
    if (!message.trim()) return alert("请填写留言内容");
    const body = {
      nickname: nickname.trim() || "匿名用户",
      message: message.trim(),
    };
    setPosting(true);
    try {
      const r = await fetch(`${apiBase}/feedback`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(body),
      });
      if (!r.ok) {
        const t = await r.text();
        throw new Error(t || "提交失败");
      }
      const created = await r.json(); // 返回新留言
      // 置顶显示
      setList((prev) => [created, ...prev]);
      setMessage("");
    } catch (e: any) {
      alert("提交失败：" + e.message);
    } finally {
      setPosting(false);
    }
  };

  if (!open) return null;

  return (
    <div className="fixed inset-0 z-[999] flex items-center justify-center">
      {/* 背景遮罩 */}
      <div
        className="absolute inset-0 bg-black/60"
        onClick={onClose}
        aria-hidden
      />
      {/* 弹窗 */}
      <div className="relative z-10 w-[92%] max-w-2xl rounded-2xl bg-gray-800 border border-gray-700 shadow-xl">
        <div className="flex items-center justify-between p-4 border-b border-gray-700">
          <h3 className="text-lg font-semibold">💬 公开留言板</h3>
          <button
            onClick={onClose}
            className="rounded px-2 py-1 text-gray-300 hover:bg-gray-700"
            aria-label="关闭"
          >
            ✕
          </button>
        </div>

        {/* 发布区 */}
        <div className="p-4 space-y-3">
          <div className="flex gap-3">
            <input
              value={nickname}
              onChange={(e) => setNickname(e.target.value)}
              placeholder="昵称（可留空为匿名）"
              className="flex-1 rounded bg-gray-900 border border-gray-700 px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
            />
          </div>
          <textarea
            value={message}
            onChange={(e) => setMessage(e.target.value)}
            placeholder="想反馈什么问题、建议或吐槽？所有人都能看到哦～"
            rows={4}
            maxLength={800}
            className="w-full rounded bg-gray-900 border border-gray-700 px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
          />
          <div className="flex items-center justify-between">
            <div className="text-xs text-gray-400">
              已登录/未登录都可留言；请勿发布违法违规内容。
            </div>
            <button
              onClick={submit}
              disabled={posting}
              className={`px-4 py-2 rounded font-semibold ${
                posting ? "bg-blue-400 cursor-not-allowed" : "bg-blue-600 hover:bg-blue-700"
              }`}
            >
              {posting ? "提交中..." : "发布留言"}
            </button>
          </div>
        </div>

        {/* 列表区 */}
        <div className="px-4 pb-4">
          {loading ? (
            <div className="text-gray-400 text-sm">加载留言中...</div>
          ) : list.length === 0 ? (
            <div className="text-gray-500 text-sm">还没有留言，来当第一个吧！</div>
          ) : (
            <ul className="space-y-3 max-h-[40vh] overflow-auto pr-1">
              {list.map((it) => (
                <li key={it.id} className="rounded-lg border border-gray-700 bg-gray-900 p-3">
                  <div className="flex items-center justify-between text-xs text-gray-400">
                    <span className="font-semibold text-gray-300">{it.nickname}</span>
                    <time dateTime={it.created_at}>
                      {new Date(it.created_at).toLocaleString()}
                    </time>
                  </div>
                  <p className="mt-2 whitespace-pre-wrap leading-relaxed text-gray-200 text-sm">
                    {it.message}
                  </p>
                </li>
              ))}
            </ul>
          )}
        </div>
      </div>
    </div>
  );
}
