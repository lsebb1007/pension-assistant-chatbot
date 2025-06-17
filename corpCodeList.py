import requests, zipfile, io
import xml.etree.ElementTree as ET
import pandas as pd
import os

def download_corp_list():
    api_key = os.getenv("DART_API_KEY")
    url = f"https://opendart.fss.or.kr/api/corpCode.xml?crtfc_key={api_key}"
    res = requests.get(url)

    with zipfile.ZipFile(io.BytesIO(res.content)) as z:
        xml_file = z.open(z.namelist()[0])
        tree = ET.parse(xml_file)
        root = tree.getroot()
        data = []

        for item in root.findall("list"):
            data.append({
                "corp_code": item.findtext("corp_code"),
                "corp_name": item.findtext("corp_name"),
                "stock_code": item.findtext("stock_code")
            })

        df = pd.DataFrame(data)
        df.to_csv("corp_list.csv", index=False, encoding="utf-8-sig")
        print("✅ corp_list.csv 저장 완료")

download_corp_list()
