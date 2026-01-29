# 웹 크롤링
    # 인터넷 상에 존재하는 데이터를 자동으로 수집하는 행위
    # 데이터 분석가에게 데이터를 탐색하고 원하는 조건에 맞는 데이터를 직접 수집/저장까지
        # 1. 웹페이지 정보
            # requests 라이브러리 사용
        # 2. html 소스 파싱(분석)하여 원하는 정보 얻기
            # BeautifulSoup 라이브러리 사용

# 파싱 연습
import requests
from bs4 import BeautifulSoup
response=requests.get("https://startcoding.pythonanywhere.com/basic")
print(response) # 연결됐는지 확인
html=response.text
print(html) # elements 확인
soup=BeautifulSoup(html,"html.parser")
print(soup) # 태그 별로 쪼갠 거 확인(파싱)

print("="*100)
# 카테고리
category=soup.select_one(".product-category") # 해당 클래스의 처음 것만 선택
print(category) # <p class="product-category">노트북</p>
category=soup.select_one(".product-category").text # 해당 클래스의 값만 출력
print(category) #노트북

# 상품명
name=soup.select_one(".product-name").text
print(name) #에이서 스위프트 GO 16 OLED, 스틸 그레이, 코어i7, 512GB, 16GB, WIN11 Home, SFG16-71-77FT

# 상세페이지(class가 없음, a태그)
link=soup.select_one(".product-name > a").attrs["href"]
# product-name 안에 있는 a 태그 가져오기(자식 관계는 > 사용, 안 쓰면 안의 모든 a가 다 바뀜)
# 손자 관계는 못 끌고 옮
# attrs: a가 가진 속성값(링크) 불러오기 -> dict 구조로 가져옮 -> ["href"]로 value만 불러오기
print(link)

# 이미지 경로 가져오기
# img=soup.select_one(".product-name > img")["src"]

# 가격 가져오기
price=soup.select_one(".product-price").text.replace(",","").replace("원","")
# ,과 원 없애서 가져오기
print(price)
print("="*70)
print(category,name,link,price)



