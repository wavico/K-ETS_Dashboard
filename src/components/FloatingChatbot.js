import React from "react";
import styled, { keyframes } from "styled-components";

// 애니메이션 정의
const bounce = keyframes`
  0%, 20%, 50%, 80%, 100% {
    transform: translateY(0);
  }
  40% {
    transform: translateY(-10px);
  }
  60% {
    transform: translateY(-5px);
  }
`;

// 스타일드 컴포넌트
const FloatingButton = styled.button`
  position: fixed;
  bottom: 32px;
  right: 32px;
  width: 64px;
  height: 64px;
  border-radius: 50%;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  color: white;
  border: none;
  font-size: 32px;
  cursor: pointer;
  box-shadow: 0 4px 15px rgba(0, 0, 0, 0.2);
  z-index: 10000;
  transition: all 0.3s ease;
  animation: ${bounce} 2s infinite;
  display: ${(props) => (props.isOpen ? "none" : "block")};

  &:hover {
    background: linear-gradient(135deg, #764ba2 0%, #667eea 100%);
    transform: scale(1.1);
    box-shadow: 0 6px 20px rgba(0, 0, 0, 0.3);
  }

  &:active {
    transform: scale(0.95);
  }
`;

const FloatingChatbot = ({ isOpen, onToggle }) => {
  return (
    <FloatingButton onClick={onToggle} title="AI 챗봇 열기" isOpen={isOpen}>
      🤖
    </FloatingButton>
  );
};

export default FloatingChatbot;
