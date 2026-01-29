
# 여러 페이지 크롤링
    # 주소: page=n 이라고 들어오는 주소마다 크롤링

# 여러 개 상품 데이터를 들고오기(파싱)

import requests
from bs4 import BeautifulSoup
import pandas as pd # 파일 형태로 바꾸기 위해
import openpyxl # 엑셀 파일로 in/out 가능하게

data=[] # 파싱한 데이터를 넣을 빈 list
for i in range(1,5):
    response=requests.get(f"https://startcoding.pythonanywhere.com/basic?page={i}&keyword=") # 페이지 돌기
    html=response.text
    soup=BeautifulSoup(html,"html.parser")
    items=soup.select(".product") # 부모를 찾기
    for item in items: # 자식 찾아서 돌리기
        # 카테고리
        category=item.select_one(".product-category").text
        # 상품명
        name=item.select_one(".product-name").text
        # 상세페이지(class가 없음, a태그)
        link=item.select_one(".product-name > a").attrs["href"]
        # 가격
        price=item.select_one(".product-price").text.split("원")[0].replace(",","").replace("원","")
        print(category,name,link,price)
        data.append([category,name,link,price])
    print(f"<페이지 {i}>")

print(data)

# 엑셀로 만들기
df=pd.DataFrame(data,columns=["카테고리","상품명","상세페이지 링크","가격"]) # 해당 컬럼 명으로 구조화시키겠다.
df.to_excel("data.xlsx",index=False) # 엑셀 파일로 빼기