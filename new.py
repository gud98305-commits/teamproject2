# KBS 국제 뉴스 크롤링 (여러 페이지) + OpenAI 요약
# Selenium으로 동적 페이지 크롤링

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options
from bs4 import BeautifulSoup
import pandas as pd
from openai import OpenAI
import time
import os
from dotenv import load_dotenv

# 환경변수 로드
load_dotenv()

# OpenAI API 키 설정 (.env 파일에서 자동 로드)
api_key = os.getenv("OPENAI_API_KEY")
if not api_key:
    raise ValueError("❌ OPENAI_API_KEY가 .env 파일에 설정되지 않았습니다!")

client = OpenAI(api_key=api_key)

# 뉴스 내용을 3줄로 요약하는 함수
def summarize_news(content):
    try:
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": "당신은 뉴스 요약 전문가입니다. 뉴스 내용을 정확하고 간결하게 3줄로 요약해주세요."},
                {"role": "user", "content": f"다음 뉴스를 3줄로 요약해주세요:\n\n{content}"}
            ],
            max_tokens=200,
            temperature=0.7
        )
        return response.choices[0].message.content.strip()
    except Exception as e:
        print(f"  ✗ 요약 생성 오류: {e}")
        return "요약 생성 실패"

# Chrome 옵션 설정
chrome_options = Options()
chrome_options.add_argument("--headless")  # 브라우저 창 숨기기 (원하면 제거)
chrome_options.add_argument("--no-sandbox")
chrome_options.add_argument("--disable-dev-shm-usage")

# WebDriver 초기화
driver = webdriver.Chrome(options=chrome_options)
wait = WebDriverWait(driver, 10)

# KBS 국제 뉴스 페이지
base_url = "https://news.kbs.co.kr/news/pc/category/category.do?ctcd=0006&ref=pSiteMap"

data = []
MAX_PAGES = 3  # 크롤링할 페이지 수 (원하는 만큼 조정)

try:
    print(f"KBS 국제 뉴스 크롤링 시작 (최대 {MAX_PAGES}페이지)\n")
    driver.get(base_url)
    time.sleep(3)  # 페이지 로딩 대기

    # 현재 날짜 확인
    current_date = driver.find_element(By.CSS_SELECTOR, ".datepicker-label .date").text
    print(f"📅 크롤링 날짜: {current_date}\n")

    for page_num in range(1, MAX_PAGES + 1):
        print(f"{'='*60}")
        print(f"📄 페이지 {page_num} 크롤링 중...")
        print(f"{'='*60}\n")

        # 현재 페이지의 HTML 가져오기
        time.sleep(2)
        soup = BeautifulSoup(driver.page_source, "html.parser")

        # 뉴스 목록 가져오기
        news_items = soup.select(".box-contents.has-wrap .box-content")
        print(f"이 페이지의 뉴스 개수: {len(news_items)}\n")

        for idx, item in enumerate(news_items, 1):
            try:
                # 뉴스 링크
                link = item.get("href")
                if not link:
                    continue

                news_url = "https://news.kbs.co.kr" + link

                # 제목
                title_elem = item.select_one(".title")
                title = title_elem.text.strip() if title_elem else "제목 없음"

                # 날짜
                date_elem = item.select_one(".field-writer .date")
                date = date_elem.text.strip() if date_elem else "날짜 없음"

                print(f"  [{page_num}-{idx}] {title[:40]}...")
                print(f"       날짜: {date}")

                # 상세 페이지 방문하여 본문 가져오기
                driver.execute_script(f"window.open('{news_url}', '_blank');")
                driver.switch_to.window(driver.window_handles[1])
                time.sleep(2)

                # 본문 내용 크롤링
                detail_soup = BeautifulSoup(driver.page_source, "html.parser")
                content_elem = detail_soup.select_one("#cont_newstext")
                content = content_elem.text.strip() if content_elem else "내용 없음"

                # OpenAI 요약
                print(f"       요약 생성 중...")
                summary = summarize_news(content)

                # 데이터 저장
                data.append([date, title, content, summary])
                print(f"       ✓ 완료\n")

                # 탭 닫고 원래 페이지로 돌아가기
                driver.close()
                driver.switch_to.window(driver.window_handles[0])

                time.sleep(1)  # API 제한 방지

            except Exception as e:
                print(f"       ✗ 오류: {e}\n")
                # 탭이 열려있으면 닫기
                if len(driver.window_handles) > 1:
                    driver.close()
                    driver.switch_to.window(driver.window_handles[0])
                continue

        # 다음 페이지로 이동
        if page_num < MAX_PAGES:
            try:
                print(f"\n⏭️  다음 페이지로 이동 중...\n")
                next_button = driver.find_element(By.CSS_SELECTOR, f"#page{page_num + 1}")
                driver.execute_script("arguments[0].click();", next_button)
                time.sleep(3)
            except Exception as e:
                print(f"⚠️  다음 페이지 버튼을 찾을 수 없습니다: {e}")
                break

finally:
    driver.quit()
    print(f"\n{'='*60}")
    print(f"✅ 크롤링 완료! 총 {len(data)}개의 뉴스 수집")
    print(f"{'='*60}\n")

# 엑셀로 저장
if data:
    df = pd.DataFrame(data, columns=["기고 날짜", "뉴스 제목", "뉴스 내용", "3줄 요약"])
    df.to_excel("국제뉴스.xlsx", index=False)
    print("📊 '국제뉴스.xlsx' 파일이 생성되었습니다!")
    print(f"   - 총 {len(df)}개의 뉴스 저장 완료")
else:
    print("⚠️  수집된 뉴스가 없습니다.")