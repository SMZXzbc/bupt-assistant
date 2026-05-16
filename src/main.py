import os
import sys
from dotenv import load_dotenv

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.loader import load_documents
from src.splitter import split_documents
from src.embedding import get_embedding_function
from src.retriever import create_vectorstore, load_vectorstore
from src.generator import generate_answer


def build_knowledge_base(data_dir: str = "data", persist_dir: str = "chroma_db"):
    print("=" * 50)
    print("正在构建知识库...")
    print("=" * 50)

    documents = load_documents(data_dir)
    if not documents:
        print("[错误] 未加载到任何文档，请检查 data/ 目录")
        return None

    chunks = split_documents(documents)
    embeddings = get_embedding_function()
    vectorstore = create_vectorstore(chunks, embeddings, persist_dir)

    print("知识库构建完成！")
    print("=" * 50)
    return vectorstore


def interactive_loop(vectorstore):
    print("\n欢迎使用北邮校园智能助手！输入问题开始对话，输入 'exit' 退出。\n")

    while True:
        question = input("🧑 你的问题：").strip()
        if not question:
            continue
        if question.lower() == "exit":
            print("再见！")
            break

        print("正在检索相关知识...")
        results = vectorstore.similarity_search(question, k=3)
        print(f"检索到 {len(results)} 个相关片段")

        print("正在生成回答...\n")
        answer = generate_answer(question, results)
        print(f"🤖 回答：\n{answer}\n")
        print("-" * 50)


def main():
    load_dotenv()

    api_key = os.getenv("MIMO_API_KEY")
    if not api_key or api_key == "your_mimo_api_key_here":
        print("[错误] 请先在 .env 文件中配置 MIMO_API_KEY")
        print("复制 .env.example 为 .env，然后填入真实的 API Key")
        return

    persist_dir = "chroma_db"
    data_dir = "data"

    if os.path.exists(persist_dir) and os.listdir(persist_dir):
        print("检测到已有向量库，直接加载...")
        embeddings = get_embedding_function()
        vectorstore = load_vectorstore(embeddings, persist_dir)
    else:
        vectorstore = build_knowledge_base(data_dir, persist_dir)
        if vectorstore is None:
            return

    interactive_loop(vectorstore)


if __name__ == "__main__":
    main()
