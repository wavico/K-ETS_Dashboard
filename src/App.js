import React, { useState, useEffect, useRef } from "react";
import styled from "styled-components";
import FloatingChatbot from "./components/FloatingChatbot";

const AppContainer = styled.div`
  width: 100vw;
  height: 100vh;
  overflow: hidden;
  position: relative;
  margin: 0;
  padding: 0;
`;

const StreamlitFrame = styled.iframe`
  width: ${(props) => (props.isChatbotOpen ? "calc(100% - 400px)" : "100%")};
  height: 100vh;
  border: none;
  transition: width 0.3s ease;
  overflow: auto;
`;

const ChatbotOverlay = styled.div`
  position: fixed;
  top: 0;
  right: 0;
  width: 400px;
  height: 100vh;
  background: white;
  box-shadow: -4px 0 15px rgba(0, 0, 0, 0.1);
  z-index: 1000;
  transform: translateX(${(props) => (props.isOpen ? "0" : "100%")});
  transition: transform 0.3s ease;
`;

const ChatbotFrame = styled.iframe`
  width: 100%;
  height: 100%;
  border: none;
`;

const CloseButton = styled.button`
  position: absolute;
  top: 16px;
  right: 16px;
  width: 32px;
  height: 32px;
  border-radius: 50%;
  background: #764ba2;
  color: white;
  border: none;
  font-size: 18px;
  cursor: pointer;
  z-index: 1001;
  display: flex;
  align-items: center;
  justify-content: center;
  transition: all 0.2s ease;

  &:hover {
    background: #e74c3c;
    transform: scale(1.1);
  }
`;

function App() {
  const [isChatbotOpen, setIsChatbotOpen] = useState(false);
  const streamlitFrameRef = useRef(null);

  const toggleChatbot = () => {
    const newState = !isChatbotOpen;
    setIsChatbotOpen(newState);

    // Streamlit에 사이드바 상태 변경 메시지 전송
    if (streamlitFrameRef.current) {
      const message = {
        type: "TOGGLE_SIDEBAR",
        sidebarState: newState ? "collapsed" : "expanded",
      };
      streamlitFrameRef.current.contentWindow.postMessage(
        message,
        "http://localhost:8501"
      );
    }
  };

  const closeChatbot = () => {
    setIsChatbotOpen(false);

    // Streamlit에 사이드바 확장 메시지 전송
    if (streamlitFrameRef.current) {
      const message = {
        type: "TOGGLE_SIDEBAR",
        sidebarState: "expanded",
      };
      streamlitFrameRef.current.contentWindow.postMessage(
        message,
        "http://localhost:8501"
      );
    }
  };

  return (
    <AppContainer>
      {/* 메인 Streamlit 대시보드 */}
      <StreamlitFrame
        ref={streamlitFrameRef}
        src="http://localhost:8501"
        title="탄소배출권 대시보드"
        isChatbotOpen={isChatbotOpen}
      />

      {/* 우측 챗봇 오버레이 */}
      <ChatbotOverlay isOpen={isChatbotOpen}>
        <CloseButton onClick={closeChatbot} title="닫기">
          ×
        </CloseButton>
        <ChatbotFrame src="http://localhost:8502" title="AI 챗봇" />
      </ChatbotOverlay>

      {/* 플로팅 챗봇 버튼 */}
      <FloatingChatbot isOpen={isChatbotOpen} onToggle={toggleChatbot} />
    </AppContainer>
  );
}

export default App;
