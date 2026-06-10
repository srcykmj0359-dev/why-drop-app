import os
import requests
from dotenv import load_dotenv

load_dotenv()

KIS_APP_KEY = os.getenv("KIS_APP_KEY")
KIS_APP_SECRET = os.getenv("KIS_APP_SECRET")
KIS_ENV = os.getenv("KIS_ENV", "real").lower()

if KIS_ENV == "virtual":
    BASE_URL = "https://openapivts.koreainvestment.com:29443"
else:
    BASE_URL = "https://openapi.koreainvestment.com:9443"


def get_access_token():
    if not KIS_APP_KEY or not KIS_APP_SECRET:
        raise ValueError("KIS_APP_KEY 또는 KIS_APP_SECRET이 .env에 없습니다.")

    url = f"{BASE_URL}/oauth2/tokenP"

    headers = {
        "content-type": "application/json; charset=UTF-8"
    }

    payload = {
        "grant_type": "client_credentials",
        "appkey": KIS_APP_KEY,
        "appsecret": KIS_APP_SECRET,
    }

    res = requests.post(url, headers=headers, json=payload, timeout=10)
    print("TOKEN STATUS:", res.status_code)

    if res.status_code != 200:
        print("TOKEN ERROR BODY:")
        print(res.text)
        raise RuntimeError("토큰 발급 실패")

    data = res.json()
    token = data.get("access_token")

    if not token:
        print("TOKEN RESPONSE:")
        print(data)
        raise RuntimeError("access_token이 응답에 없습니다.")

    return token


def get_kis_price(stock_code="005930"):
    token = get_access_token()

    url = f"{BASE_URL}/uapi/domestic-stock/v1/quotations/inquire-price"

    headers = {
        "content-type": "application/json; charset=UTF-8",
        "authorization": f"Bearer {token}",
        "appkey": KIS_APP_KEY,
        "appsecret": KIS_APP_SECRET,
        "tr_id": "FHKST01010100",
        "custtype": "P",
    }

    params = {
        "FID_COND_MRKT_DIV_CODE": "J",
        "FID_INPUT_ISCD": stock_code,
    }

    res = requests.get(url, headers=headers, params=params, timeout=10)
    print("PRICE STATUS:", res.status_code)

    if res.status_code != 200:
        print("PRICE ERROR BODY:")
        print(res.text)
        raise RuntimeError("현재가 조회 실패")

    data = res.json()
    print("RAW RESPONSE:")
    print(data)

    output = data.get("output", {})

    result = {
        "종목코드": stock_code,
        "현재가": output.get("stck_prpr"),
        "전일대비": output.get("prdy_vrss"),
        "등락률": output.get("prdy_ctrt"),
        "거래량": output.get("acml_vol"),
        "거래대금": output.get("acml_tr_pbmn"),
        "시가": output.get("stck_oprc"),
        "고가": output.get("stck_hgpr"),
        "저가": output.get("stck_lwpr"),
        "전일종가": output.get("stck_sdpr"),
    }

    return result


if __name__ == "__main__":
    result = get_kis_price("005930")

    print("\n=== 삼성전자 현재가 조회 결과 ===")
    for k, v in result.items():
        print(f"{k}: {v}")
