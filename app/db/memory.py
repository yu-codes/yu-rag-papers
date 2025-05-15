from langchain.memory import ConversationBufferMemory
from langchain.schema import HumanMessage, AIMessage
from langchain_core.chat_history import InMemoryChatMessageHistory
# -------------------------------------------------------------
from .database import SessionLocal
from .models import User, ChatHistory


def build_memory(line_user_id: str) -> ConversationBufferMemory:
    """
    依 LINE 使用者 ID 取得（或建立）資料庫使用者，
    將其歷史訊息載入為 ConversationBufferMemory。
    """
    session = SessionLocal()

    # 1. 取得或建立 User
    user = session.query(User).filter_by(line_user_id=line_user_id).first()
    if not user:
        user = User(line_user_id=line_user_id)
        session.add(user)
        session.commit()

    # 2. 讀取歷史訊息，依 timestamp 排序
    rows = (
        session.query(ChatHistory)
        .filter_by(user_id=user.id)
        .order_by(ChatHistory.timestamp)
        .all()
    )

    # 3. 填入 InMemoryChatMessageHistory
    history = InMemoryChatMessageHistory()
    for r in rows:
        if r.role in ("user", "human"):
            history.add_user_message(r.content)
        else:  # "ai"
            history.add_ai_message(r.content)

    session.close()

    # 4. 回傳 Memory（LangChain 會在對話結束後再把新訊息寫回 DB）
    return ConversationBufferMemory(
        memory_key="chat_history",
        return_messages=True,
        chat_memory=history,
    )
