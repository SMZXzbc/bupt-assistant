import os
from langchain_community.document_loaders import TextLoader, PyPDFLoader
from langchain_core.documents import Document


def load_documents(data_dir: str = "data") -> list[Document]:
    documents = []
    if not os.path.exists(data_dir):
        print(f"[错误] 数据目录不存在: {data_dir}")
        return documents

    for filename in os.listdir(data_dir):
        filepath = os.path.join(data_dir, filename)

        if filename.endswith(".txt"):
            loader = TextLoader(filepath, encoding="utf-8")
            docs = loader.load()
            for doc in docs:
                doc.metadata["source"] = filename
            documents.extend(docs)

        elif filename.endswith(".pdf"):
            loader = PyPDFLoader(filepath)
            docs = loader.load()
            for doc in docs:
                doc.metadata["source"] = filename
            documents.extend(docs)

    print(f"[loader] 从 {data_dir} 加载了 {len(documents)} 个文档片段")
    return documents
