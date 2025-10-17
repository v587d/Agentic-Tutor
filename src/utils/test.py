import secrets

# 生成一个32字节的随机字符串，然后转换为十六进制
SECRET_KEY = secrets.token_hex(32)

print(SECRET_KEY)