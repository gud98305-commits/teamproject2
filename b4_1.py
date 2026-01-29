# 도메인의 주소 뒤에 /robots.txt 를 붙여서 enter, 크롤링이 어디까지 되는지 알려줌
# 뭔 사이트를 검색했을 때, 도메인 뒤에 /000을 확인하여 위의 허가 리스트와 비교하여 크롤링 가능한지 확인
# 예를 들어 /search는 크롤링이 안 됨
# /$ : 메인페이지에 대해서만 크롤링 가능

# 뉴스 사이트는 많이 열어져 있음

# f12 : 개발자 모드

import requests # 웹서버와 통신을 위해
from bs4 import BeautifulSoup

# requests.get("크롤링하련는 웹페이지 주소")
reponse=requests.get("https://www.google.com/")
print(reponse) # response [200] : 통신이 됐다는 것임  # 404: 통신 오류(페이지 찾을 수 없음)
print(reponse.text) # 사이트 내용을 알고 싶을 때: f12번에 뜨는 모든 elements
url=reponse.text
print("="*50)
soup=BeautifulSoup(url,"html.parser")
    # 파싱: 전체에서 원하는 부분을 잘라서 나누겠다
    # library 필요(BeautifulSoup)
    # html.parser: 태그 단위로 끊기
print(soup)

    