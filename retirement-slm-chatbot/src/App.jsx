import React, { useState, useRef, useEffect } from "react";
import axios from "axios";

const SECTION_LABELS = {
  "1줄 요약": "요약",
  "핵심 안내": "주요 안내",
  "세부 절차/조건/유의사항": "세부 절차/조건/유의사항",
  "출처": "출처",
  "연관 추가 질문 제안": "연관 추가 질문",
  "연관 추가 질문": "연관 추가 질문"
};

const SECTION_LABEL_STYLE = "font-bold text-[1.1em] mb-1 mt-2";
const SECTION_VALUE_STYLE = "text-[1em] mb-1";
const SECTION_LABEL_STYLE_SOURCE = "font-semibold text-xs text-gray-400 mb-0 mt-2"; // 출처 항목명 스타일
const SECTION_VALUE_STYLE_SOURCE = "text-xs text-gray-500 mb-1"; // 출처 본문 스타일

function parseBotText(text) {
  const lines = text.split("\n").filter(Boolean);
  const sections = [];
  for (let line of lines) {
    const m = line.match(/^\[(.*?)\]:\s*(.*)/);
    if (m) {
      const key = m[1].trim();
      const val = m[2].trim();
      sections.push({ key, val });
    } else {
      sections.push({ key: "", val: line });
    }
  }
  return sections;
}

// 텍스트에서 **볼드** 마크다운을 <span class="font-bold">볼드</span>로 변환
function parseBold(text) {
  const regex = /\*\*(.+?)\*\*/g;
  const result = [];
  let lastIndex = 0;
  let match;
  let key = 0;

  while ((match = regex.exec(text)) !== null) {
    if (match.index > lastIndex) {
      const normal = text.substring(lastIndex, match.index);
      normal.split('\n').forEach((chunk, idx, arr) => {
        if (chunk) result.push(chunk);
        if (idx < arr.length - 1) result.push(<br key={`br-normal-${key}-${idx}`} />);
      });
    }
    match[1].split('\n').forEach((chunk, idx, arr) => {
      if (chunk) result.push(
        <span key={`bold-${key}-${idx}`} className="font-bold">{chunk}</span>
      );
      if (idx < arr.length - 1) result.push(<br key={`br-bold-${key}-${idx}`} />);
    });
    lastIndex = regex.lastIndex;
    key++;
  }
  if (lastIndex < text.length) {
    const normal = text.substring(lastIndex);
    normal.split('\n').forEach((chunk, idx, arr) => {
      if (chunk) result.push(chunk);
      if (idx < arr.length - 1) result.push(<br key={`br-tail-${key}-${idx}`} />);
    });
  }
  return result;
}

function extractRelatedQuestions(val) {
  return val
    .replace(/[\n\r]+/g, " ")
    .split(",")
    .map(q => q.trim())
    .filter(q => q.length > 4);
}

function App() {
  const [messages, setMessages] = useState([
    { type: "bot", text: "안녕하세요! 퇴직연금 상담을 도와드릴 AI입니다. 궁금한 점을 입력해 주세요.", streaming: false }
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

  // ✨ 스트리밍+마크다운 동시지원 핵심
  function streamText(text, callback, speed = 24) {
    let i = 0;
    function next() {
      if (i <= text.length) {
        // 콜백에서 isFinal(마지막) 전달
        callback(text.slice(0, i), i === text.length);
        i++;
        setTimeout(next, speed);
      }
    }
    next();
  }

  const handleRelatedQuestionClick = async (question) => {
    if (loading) return;
    setInput("");
    const userMsg = { type: "user", text: question };
    setMessages(msgs => [...msgs, userMsg]);
    setLoading(true);
    try {
      const minWait = new Promise(res => setTimeout(res, 700));
      const responsePromise = axios.post("/chat", {
        message: question,
        session_id: getSessionId(),
        rag_type: "full"
      });
      const [response] = await Promise.all([responsePromise, minWait]);
      const botText = response?.data?.response || "❌ 답변 생성 중 오류가 발생했습니다.";

      setMessages(msgs => [...msgs, { type: "bot", text: "", streaming: true }]);
      streamText(
        botText,
        (t, isFinal) => setMessages(msgs => {
          const newMsgs = [...msgs];
          if (isFinal) {
            newMsgs[newMsgs.length - 1] = { type: "bot", text: botText, streaming: false };
          } else {
            newMsgs[newMsgs.length - 1] = { type: "bot", text: t, streaming: true };
          }
          return newMsgs;
        }),
        24
      );
    } catch (e) {
      setMessages(msgs => [
        ...msgs,
        { type: "bot", text: "❌ 서버와 통신 중 오류가 발생했습니다.", streaming: false }
      ]);
    } finally {
      setLoading(false);
    }
  };

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
        session_id: getSessionId(),
        rag_type: "full"
      });
      const [response] = await Promise.all([responsePromise, minWait]);
      const botText = response?.data?.response || "❌ 답변 생성 중 오류가 발생했습니다.";

      setMessages(msgs => [...msgs, { type: "bot", text: "", streaming: true }]);
      streamText(
        botText,
        (t, isFinal) => setMessages(msgs => {
          const newMsgs = [...msgs];
          if (isFinal) {
            newMsgs[newMsgs.length - 1] = { type: "bot", text: botText, streaming: false };
          } else {
            newMsgs[newMsgs.length - 1] = { type: "bot", text: t, streaming: true };
          }
          return newMsgs;
        }),
        24
      );
    } catch (e) {
      setMessages(msgs => [
        ...msgs,
        { type: "bot", text: "❌ 서버와 통신 중 오류가 발생했습니다.", streaming: false }
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
              >
                {msg.type === "bot"
                  ? (
                    <div>
                      {parseBotText(msg.text).map((s, i) => {
                        // 연관 추가 질문(버튼)
                        if (s.key && (s.key === "연관 추가 질문" || s.key === "연관 추가 질문 제안")) {
                          const questions = extractRelatedQuestions(s.val);
                          return (
                            <div key={i} className="mb-2">
                              <div className={SECTION_LABEL_STYLE}>
                                {SECTION_LABELS[s.key] || s.key}
                              </div>
                              <div className="flex flex-wrap gap-2 mt-1">
                                {questions.map((q, qidx) => (
                                  <button
                                    key={qidx}
                                    type="button"
                                    className="px-3 py-1 rounded-xl border border-blue-400 bg-blue-50 text-blue-800 text-sm hover:bg-blue-100 transition-colors"
                                    style={{ cursor: "pointer" }}
                                    onClick={() => handleRelatedQuestionClick(q)}
                                    disabled={loading}
                                  >
                                    {q}
                                  </button>
                                ))}
                              </div>
                            </div>
                          );
                        }
                        // 출처
                        if (s.key === "출처") {
                          return (
                            <div key={i} className="mb-2">
                              <div className={SECTION_LABEL_STYLE_SOURCE}>
                                {SECTION_LABELS[s.key] || s.key}
                              </div>
                              <div className={SECTION_VALUE_STYLE_SOURCE}>
                                {s.val}
                              </div>
                            </div>
                          );
                        }
                        // 기타(일반 항목)
                        return s.key ? (
                          <div key={i} className="mb-2">
                            <div className={SECTION_LABEL_STYLE}>
                              {SECTION_LABELS[s.key] || s.key}
                            </div>
                            <div className={SECTION_VALUE_STYLE}>
                              {msg.streaming ? s.val : parseBold(s.val)}
                            </div>
                          </div>
                        ) : (
                          <div key={i} className="mb-1">{msg.streaming ? s.val : parseBold(s.val)}</div>
                        );
                      })}

                    </div>
                  )
                  : msg.text
                }
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
