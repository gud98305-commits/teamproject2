# 여러 개 상품 데이터를 들고오기(파싱)

import requests
from bs4 import BeautifulSoup
response=requests.get("https://startcoding.pythonanywhere.com/basic")
print(response) # 연결됐는지 확인
html=response.text
print(html) # elements 확인
soup=BeautifulSoup(html,"html.parser")
print(soup) # 태그 별로 쪼갠 거 확인(파싱)

print("="*100)

# for문 쓰기
    # 제일 큰 상품 묶음 찾아서 가져오기: product, col-md-4 col-xs-6, product-container 등 -> 10개

items=soup.select(".product") # 부모를 찾기
print(items)
for item in items: # 자식 찾아서 돌리기
    # 카테고리
    category=item.select_one(".product-category").text
    # 상품명
    name=item.select_one(".product-name").text
    # 상세페이지(class가 없음, a태그)
    link=item.select_one(".product-name > a").attrs["href"]
    # 가격
    price=item.select_one(".product-price").text.split("원")[0].replace(",","").replace("원","")
    # 할인가와 원가격 중 원가격 버리기: '원'을 가지고 앞뒤로 나누기-> [0]으로 앞(첫번째)만 살리기
    # ,과 원 없애서 가져오기
    print(category,name,link,price)