import React, { useState, useRef, useEffect } from "react";
import axios from "axios";

function App() {
  const [messages, setMessages] = useState([
    { type: "bot", text: "안녕하세요! 퇴직연금 상담을 도와드릴 AI입니다. 궁금한 점을 입력해 주세요." }
  ]);
  const [input, setInput] = useState("");
  const [loading, setLoading] = useState(false);
  const chatRef = useRef(null);
  const textareaRef = useRef(null);

  useEffect(() => {
    if (chatRef.current) {
      chatRef.current.scrollTop = chatRef.current.scrollHeight;
    }
  }, [messages, loading]);

  useEffect(() => {
    if (textareaRef.current) textareaRef.current.focus();
  }, [messages]);

  const getSessionId = () => {
    let sessionId = localStorage.getItem("chat_session_id");
    if (!sessionId) {
      sessionId = String(Date.now());
      localStorage.setItem("chat_session_id", sessionId);
    }
    return sessionId;
  };

  // 1) 스트리밍 함수
  function streamText(text, callback, speed = 30) {
    let i = 0;
    function next() {
      if (i <= text.length) {
        callback(text.slice(0, i));
        i++;
        setTimeout(next, speed);
      }
    }
    next();
  }

  // 2) sendMessage 함수 교체
  const sendMessage = async () => {
    if (!input.trim() || loading) return;
    const userMsg = { type: "user", text: input };
    setMessages(msgs => [...msgs, userMsg]);
    setInput("");
    setLoading(true);
    try {
      const minWait = new Promise(res => setTimeout(res, 700));
      const responsePromise = axios.post("/chat", {
        message: input,
        session_id: getSessionId()
      });
      const [response] = await Promise.all([responsePromise, minWait]);
      const botText = response?.data?.response || "❌ 답변 생성 중 오류가 발생했습니다.";

      setMessages(msgs => [...msgs, { type: "bot", text: "" }]);
      streamText(
        botText,
        t => setMessages(msgs => {
          const newMsgs = [...msgs];
          newMsgs[newMsgs.length - 1] = { type: "bot", text: t };
          return newMsgs;
        }),
        24 // ms, 필요시 조절
      );
    } catch (e) {
      setMessages(msgs => [
        ...msgs,
        { type: "bot", text: "❌ 서버와 통신 중 오류가 발생했습니다." }
      ]);
    } finally {
      setLoading(false);
    }
  };

  const handleKeyDown = e => {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      sendMessage();
    }
  };

  // ⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐
  // 반드시 return을 붙여주세요!
  // 기존 return ( ... ) JSX 부분을 모두 살려야 합니다.
  // ⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐

  return (
    <div className="min-h-screen bg-white flex flex-col items-center">
      {/* 헤더 */}
      <header className="w-full max-w-md px-4 py-3 flex items-center justify-between border-b border-gray-200 bg-white sticky top-0 z-10">
        <span className="text-lg font-bold text-[#103D82]">퇴직연금 상담</span>
        <span className="text-xs text-gray-400">AI SLM 챗봇</span>
      </header>
      {/* 채팅 영역 */}
      <main className="flex-1 w-full max-w-md mx-auto flex flex-col" style={{ background: "#fff" }}>
        <div
          ref={chatRef}
          className="flex-1 overflow-y-auto px-2 py-4 space-y-2"
          style={{ minHeight: "76vh", maxHeight: "80vh" }}
        >
          {messages.map((msg, idx) => (
            <div
              key={idx}
              className={`flex ${msg.type === "user" ? "justify-end" : "justify-start"} items-end`}
            >
              <div
                className={`
                  px-4 py-2 text-base leading-relaxed max-w-[80%] break-words
                  ${msg.type === "user"
                    ? "bg-[#103D82] text-white rounded-2xl rounded-br-sm ml-8"
                    : "bg-white text-black border border-blue-100 rounded-2xl rounded-bl-sm mr-8"
                  }
                  shadow-sm
                `}
                style={{
                  wordBreak: "break-all",
                  whiteSpace: "pre-wrap"
                }}
              >
                {msg.text}
              </div>
            </div>
          ))}
          {loading && (
            <div className="flex justify-start items-end">
              <div className="rounded-2xl rounded-bl-sm px-4 py-2 bg-white text-black border border-blue-100 shadow-sm max-w-[80%] text-base animate-pulse">
                답변 생성 중...
              </div>
            </div>
          )}
        </div>
      </main>
      {/* 입력창 */}
      <form
        className="w-full max-w-md px-2 py-3 flex items-center gap-2 bg-white sticky bottom-0 border-t border-gray-200"
        onSubmit={e => {
          e.preventDefault();
          sendMessage();
        }}
        style={{ zIndex: 20 }}
      >
        <textarea
          ref={textareaRef}
          className="flex-1 resize-none rounded-2xl border border-gray-300 px-4 py-2 focus:outline-[#103D82] text-base bg-[#f7fafd]"
          style={{ minHeight: 44, maxHeight: 120 }}
          placeholder="궁금한 점을 입력하세요"
          value={input}
          onChange={e => setInput(e.target.value)}
          onKeyDown={handleKeyDown}
          disabled={loading}
        />
        <button
          type="submit"
          disabled={loading || !input.trim()}
          className="bg-[#103D82] text-white px-4 py-2 rounded-2xl font-semibold shadow-sm hover:bg-blue-900 transition-colors"
        >
          보내기
        </button>
      </form>
    </div>
  );
}

export default App;
