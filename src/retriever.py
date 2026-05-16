import os
from langchain_chroma import Chroma
from langchain_core.documents import Document


def create_vectorstore(
    documents: list[Document],
    embedding_func,
    persist_dir: str = "chroma_db",
) -> Chroma:
    vectorstore = Chroma.from_documents(
        documents=documents,
        embedding=embedding_func,
        persist_directory=persist_dir,
    )
    print(f"[retriever] 向量库已创建并保存到 {persist_dir}，共 {len(documents)} 个文本块")
    return vectorstore


def load_vectorstore(
    embedding_func,
    persist_dir: str = "chroma_db",
) -> Chroma:
    if not os.path.exists(persist_dir):
        raise FileNotFoundError(f"向量库目录不存在: {persist_dir}，请先执行数据加载")

    vectorstore = Chroma(
        persist_directory=persist_dir,
        embedding_function=embedding_func,
    )
    print(f"[retriever] 已加载向量库: {persist_dir}")
    return vectorstore


# Query-to-document topic mapping for improved retrieval
TOPIC_KEYWORDS = {
    # Library
    "开放时间": ["8:00", "22:00", "周一至周", "开放时间", "法定节假日"],
    "图书馆": ["图书馆", "馆藏", "阅览室", "借阅", "座位"],
    "借书": ["借阅", "借书", "续借", "借期", "本科生", "最多可借", "罚款", "逾期"],
    "数据库": ["数据库", "CNKI", "知网", "万方", "IEEE", "ACM", "SCI", "SSCI", "EI"],
    # Academic
    "教务处": ["教务处", "教三楼", "选课", "成绩", "培养方案", "考试安排"],
    "选课": ["选课", "正选", "补退选", "退补选", "教务系统"],
    "考试": ["考试", "期末", "成绩", "复查"],
    # Portal
    "信息门户": ["my.bupt.edu.cn", "信息门户", "统一认证", "VPN"],
    "校园卡": ["校园卡", "充值", "一卡通", "挂失", "食堂", "自助充值"],
    # Campus
    "校区": ["西土城", "沙河", "昌平", "海淀"],
    "联系方式": ["电话", "地址", "邮编", "邮箱"],
    "校医院": ["校医院", "医疗", "健康"],
}


def hybrid_search(vectorstore: Chroma, query: str, k: int = 8) -> list:
    """Combine TF-IDF similarity search with topic-aware keyword matching.
    Topic-matched results are prioritized over TF-IDF results.
    """
    query_lower = query.lower()

    # 1. Topic-aware matching: collect all matches, keep highest match count per doc
    all_data = vectorstore._collection.get(limit=500)
    documents = all_data.get("documents", [])
    metadatas = all_data.get("metadatas", [])

    doc_scores = {}  # key -> (doc, match_count)

    for topic, keywords in TOPIC_KEYWORDS.items():
        if not _topic_matches_query(topic, query_lower):
            continue

        for i, doc_text in enumerate(documents):
            if i >= len(metadatas):
                break
            match_count = sum(1 for kw in keywords if kw in doc_text)
            if match_count >= 2:
                meta = metadatas[i]
                key = doc_text[:50]
                doc = Document(page_content=doc_text, metadata=meta)
                if key not in doc_scores or doc_scores[key][1] < match_count:
                    doc_scores[key] = (doc, match_count)

    # Sort by match count descending
    topic_results = sorted(doc_scores.values(), key=lambda x: x[1], reverse=True)

    # 2. TF-IDF similarity search
    seen_content = set(doc_scores.keys())
    semantic_results = []
    try:
        tfidf_results = vectorstore.similarity_search(query, k=k)
        for doc in tfidf_results:
            key = doc.page_content[:50]
            if key not in seen_content:
                seen_content.add(key)
                semantic_results.append(doc)
    except Exception:
        pass

    # Merge: topic results first, then semantic results
    merged = [doc for doc, _ in topic_results[:k]]
    merged.extend(semantic_results)

    return merged[:k * 2]


def _topic_matches_query(topic: str, query: str) -> bool:
    """Check if a topic is relevant to the query."""
    if topic in query:
        return True
    # Check topic components
    for char in topic:
        if char in query:
            return True
    # Semantic shortcuts
    shortcuts = {
        "开放时间": ["开门", "几点", "几点开", "什么时候"],
        "借书": ["借", "最多", "几本", "怎么借"],
        "信息门户": ["门户", "登录", "怎么进", "进门户"],
        "校园卡": ["充值", "一卡通", "饭卡"],
        "联系方式": ["在哪", "地址", "电话"],
    }
    for kw in shortcuts.get(topic, []):
        if kw in query:
            return True
    return False
