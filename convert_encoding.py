# convert_encoding.py
import pandas as pd

# 1) CP949로 읽어서
df = pd.read_csv("dummy_users.csv", encoding="cp949")

# 2) UTF-8-SIG로 덮어쓰기
df.to_csv("dummy_users.csv", index=False, encoding="utf-8-sig")

print("dummy_users.csv 를 UTF-8-SIG 로 변환 완료!")
