import json
from uuid import uuid4

from langchain_core.messages import AIMessage, HumanMessage
from sqlmodel import Session, select

from app.core.db import engine
from app.core.logging import logger
from app.models.session import ChatSession


class SessionService:
    def list_sessions(self, user_id: str | None = None) -> list[ChatSession]:
        """获取所有会话，按时间倒序"""
        with Session(engine) as session:
            statement = select(ChatSession).order_by(ChatSession.created_at.desc())
            if user_id:
                statement = statement.where(ChatSession.user_id == user_id)
            results = session.exec(statement)
            return list(results.all())

    def delete_session(self, session_id: str, user_id: str | None = None) -> bool:
        """删除会话"""
        with Session(engine) as session:
            chat_session = session.get(ChatSession, session_id)
            if chat_session:
                # 权限检查
                if user_id and chat_session.user_id and chat_session.user_id != user_id:
                    return False
                session.delete(chat_session)
                session.commit()
                return True
            return False

    def delete_all_sessions(self, user_id: str | None = None) -> bool:
        """删除用户的所有会话 (必须指定 user_id)"""
        if not user_id:
            logger.warning("Attempted to delete ALL sessions without user_id. Action blocked.")
            return False

        with Session(engine) as session:
            statement = select(ChatSession).where(ChatSession.user_id == user_id)
            results = session.exec(statement)
            for chat_session in results:
                session.delete(chat_session)
            session.commit()
            return True

    def create_session(self, title: str = "新对话", user_id: str | None = None) -> ChatSession:
        """创建新会话"""
        with Session(engine) as session:
            new_session = ChatSession(id=str(uuid4()), title=title, history="[]", user_id=user_id)
            session.add(new_session)
            session.commit()
            session.refresh(new_session)
            return new_session

    def get_session(self, session_id: str, user_id: str | None = None) -> dict | None:
        """获取会话详情并确保 history 是解析后的对象"""
        with Session(engine) as session:
            chat_session = session.get(ChatSession, session_id)
            if not chat_session:
                return None

            # 如果指定了 user_id，则检查归属权
            if user_id and chat_session.user_id and chat_session.user_id != user_id:
                return None

            # 将 SQLModel 对象转为字典，并手动处理 history
            data = chat_session.model_dump()
            if isinstance(data["history"], str):
                try:
                    data["history"] = json.loads(data["history"])
                except Exception:
                    data["history"] = []
            return data

    def get_chat_history(self, session_id: str, limit: int = 10) -> list:
        """获取 LangChain 格式的最近历史记录"""
        session_data = self.get_session(session_id)
        if not session_data or not session_data.get("history"):
            return []

        try:
            # get_session 已经处理过 json.loads 了，这里直接用
            raw_history = session_data["history"]
            recent_history = raw_history[-limit:]

            messages = []
            for msg in recent_history:
                if msg["role"] == "user":
                    messages.append(HumanMessage(content=msg["content"]))
                elif msg["role"] == "assistant":
                    messages.append(AIMessage(content=msg["content"]))
            return messages
        except Exception as e:
            logger.error(f"Error parsing history for session {session_id}: {e}")
            return []

    def append_message(
        self,
        session_id: str,
        role: str,
        content: str,
        attachments: list = None,
        thought_process: list = None,
        user_id: str | None = None,
    ):
        """追加消息到历史记录"""
        with Session(engine) as session:
            chat_session = session.get(ChatSession, session_id)
            if not chat_session:
                chat_session = ChatSession(id=session_id, title="新对话", history="[]", user_id=user_id)
                session.add(chat_session)

            try:
                history = json.loads(chat_session.history)
            except Exception:
                history = []

            msg_obj = {"role": role, "content": content}
            if attachments:
                msg_obj["attachments"] = attachments
            if thought_process:
                msg_obj["thought_process"] = thought_process

            history.append(msg_obj)
            chat_session.history = json.dumps(history, ensure_ascii=False)
            session.add(chat_session)
            session.commit()

    def update_title(self, session_id: str, title: str):
        """更新会话标题"""
        with Session(engine) as session:
            chat_session = session.get(ChatSession, session_id)
            if chat_session:
                chat_session.title = title
                session.add(chat_session)
                session.commit()


session_service = SessionService()
