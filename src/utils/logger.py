import logging
import logging.handlers
import os
from pathlib import Path

class Logger:
    _instance = None
    _initialized = False

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    def __init__(self):
        if not Logger._initialized:
            self._setup_logger()
            Logger._initialized = True

    def _setup_logger(
            self,
            log_dir: str = None,  # 改为None，让方法内部计算路径
            log_file: str = "app.log",
            log_level: int = logging.INFO,
            max_file_size: int = 10 * 1024 * 1024,  # 10MB
            backup_count: int = 5
    ):
        """
        设置日志记录器

        参数:
            log_dir: 日志文件目录
            log_file: 日志文件名
            log_level: 日志级别
            max_file_size: 单个日志文件最大大小（字节）
            backup_count: 保留的备份文件数量
        """
        # 如果没有指定log_dir，使用默认的项目根目录下的logs文件夹
        if log_dir is None:
            ROOT_DIR = Path(__file__).parent.parent.parent
            log_dir = str(ROOT_DIR / "logs")

        # 创建日志目录
        if not os.path.exists(log_dir):
            os.makedirs(log_dir)

        # 创建logger对象
        self.logger = logging.getLogger('app_logger')
        self.logger.setLevel(log_level)

        # 如果logger已经有处理器，说明已经配置过，直接返回
        if self.logger.handlers:
            return

        # 创建日志格式
        formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )

        # 控制台处理器
        console_handler = logging.StreamHandler()
        console_handler.setLevel(log_level)
        console_handler.setFormatter(formatter)
        self.logger.addHandler(console_handler)

        # 文件处理器（使用RotatingFileHandler实现日志轮转）
        log_path = os.path.join(log_dir, log_file)
        file_handler = logging.handlers.RotatingFileHandler(
            log_path,
            maxBytes=max_file_size,
            backupCount=backup_count,
            encoding='utf-8'
        )
        file_handler.setLevel(log_level)
        file_handler.setFormatter(formatter)
        self.logger.addHandler(file_handler)

    def _get_caller(self) -> str:
        """获取调用者的函数名称和参数"""
        import inspect
        frame = inspect.currentframe()
        try:
            # 回溯两帧以获取实际的调用者
            caller_frame = frame.f_back.f_back
            # 获取函数名
            func_name = caller_frame.f_code.co_name
            # 获取参数信息
            args_info = inspect.getargvalues(caller_frame)
            # 格式化参数
            args = []
            for arg in args_info.args:
                args.append(f"{arg}={args_info.locals[arg]}")
            if args_info.varargs:
                args.append(f"*{args_info.varargs}={args_info.locals[args_info.varargs]}")
            if args_info.keywords:
                args.append(f"**{args_info.keywords}={args_info.locals[args_info.keywords]}")

            return f"{func_name}({', '.join(args)})"
        finally:
            del frame

    def debug(self, message: str):
        """记录调试信息"""
        self.logger.debug(message)

    def info(self, message: str):
        """记录一般信息"""
        self.logger.info(message)

    def warning(self, message: str):
        """记录警告信息"""
        self.logger.warning(message)

    def error(self, message: str, exc_info=False):
        """记录错误信息"""
        caller_info = self._get_caller()  # caller 函数名、参数
        if exc_info:
            self.logger.error(f"[{caller_info}] {message}", exc_info=True)
        else:
            self.logger.error(f"[{caller_info}] {message}")

    def critical(self, message: str):
        """记录严重错误信息"""
        self.logger.critical(message)

    def exception(self, message: str):
        """记录异常信息（包含堆栈跟踪）"""
        self.logger.exception(message)


# 创建单例实例
logger = Logger()

# 使用示例：
if __name__ == "__main__":
    # 测试不同级别的日志
    logger.debug("这是一条调试信息")
    logger.info("这是一条普通信息")
    logger.warning("这是一条警告信息")
    logger.error("这是一条错误信息")
    logger.critical("这是一条严重错误信息")


