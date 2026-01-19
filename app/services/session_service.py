import json
from uuid import uuid4
from sqlmodel import Session
from app.core.db import engine
from app.models.session import ChatSession
from app.core.logging import logger

class SessionService:
    def create_session(self, title: str = "新对话") -> ChatSession:
        """创建新会话"""
        with Session(engine) as session:
            new_session = ChatSession(
                id=str(uuid4()),
                title=title,
                history="[]" # 初始为空列表
            )
            session.add(new_session)
            session.commit()
            session.refresh(new_session)
            return new_session

    def get_session(self, session_id: str) -> ChatSession | None:
        """获取会话详情"""
        with Session(engine) as session:
            return session.get(ChatSession, session_id)

    def append_message(self, session_id: str, role: str, content: str):
        """追加消息到历史记录 (如果会话不存在则自动创建)"""
        with Session(engine) as session:
            chat_session = session.get(ChatSession, session_id)
            
            # 自动创建逻辑
            if not chat_session:
                logger.info(f"Session {session_id} not found, creating new one.")
                chat_session = ChatSession(
                    id=session_id,
                    title="新对话",
                    history="[]"
                )
                session.add(chat_session)
                # 注意：这里不需要 commit，下面会统一 commit

            # 反序列化 -> 追加 -> 序列化
            try:
                history = json.loads(chat_session.history)
            except Exception:
                history = []
            
            history.append({"role": role, "content": content})
            
            chat_session.history = json.dumps(history, ensure_ascii=False)
            session.add(chat_session)
            session.commit()
            logger.debug(f"Appended {role} message to session {session_id}")

    def update_title(self, session_id: str, title: str):
        """更新会话标题"""
        with Session(engine) as session:
            chat_session = session.get(ChatSession, session_id)
            if chat_session:
                chat_session.title = title
                session.add(chat_session)
                session.commit()

session_service = SessionService()
