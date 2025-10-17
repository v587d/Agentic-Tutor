import uvicorn
from src.api.app import create_app  # 防止第一次VSCODE无法识别

# 虚拟环境命令：`python -m src.api`
if __name__ == "__main__":
    uvicorn.run(
        "src.api.app:create_app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        reload_dirs=["src", "static"],

    )
