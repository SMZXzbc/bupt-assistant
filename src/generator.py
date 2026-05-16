import os
from dotenv import load_dotenv
from langchain_community.chat_models import ChatOpenAI
from langchain_core.messages import HumanMessage, SystemMessage

load_dotenv()


def generate_answer(question: str, context_chunks: list) -> str:
    api_key = os.getenv("MIMO_API_KEY")
    base_url = os.getenv("MIMO_BASE_URL")
    model = os.getenv("MIMO_MODEL", "mimo-v2-omni")

    if not api_key or not base_url:
        raise ValueError("请在 .env 文件中设置 MIMO_API_KEY 和 MIMO_BASE_URL 环境变量")

    llm = ChatOpenAI(
        openai_api_key=api_key,
        openai_api_base=base_url,
        model=model,
        temperature=0.3,
        request_timeout=30,
    )

    context_text = "\n\n".join(
        f"[片段 {i+1}]\n{chunk.page_content}" for i, chunk in enumerate(context_chunks)
    )

    sources = []
    for chunk in context_chunks:
        source = chunk.metadata.get("source", "未知")
        if source not in sources:
            sources.append(source)

    system_prompt = (
        "你是北京邮电大学的校园智能助手。请根据以下提供的上下文信息回答用户的问题。\n"
        "规则：\n"
        "1. 只根据上下文中的信息回答，不要编造内容\n"
        "2. 如果上下文中的信息不足以回答问题，请诚实说明\n"
        "3. 回答要简洁准确，使用中文\n"
        "4. 在回答末尾标注信息来源\n\n"
        f"上下文信息：\n{context_text}"
    )

    messages = [
        SystemMessage(content=system_prompt),
        HumanMessage(content=question),
    ]

    response = llm.invoke(messages)
    answer = response.content

    source_str = "、".join(sources)
    answer += f"\n\n📄 来源：{source_str}"

    return answer
