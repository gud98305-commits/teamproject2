# KBS 국제 뉴스 크롤링 대시보드
# 날짜별 크롤링 + 키워드 분석 + 트렌드 시각화 + AI 인사이트

import streamlit as st
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from bs4 import BeautifulSoup
import pandas as pd
from openai import OpenAI
import time
from datetime import datetime
import io
import os
from dotenv import load_dotenv
from collections import Counter
import re
import plotly.express as px
import plotly.graph_objects as go
from wordcloud import WordCloud
import matplotlib.pyplot as plt

# 환경변수 로드
load_dotenv()

# 페이지 설정
st.set_page_config(
    page_title="KBS 국제 뉴스 대시보드",
    page_icon="📊",
    layout="wide"
)

# 제목
st.title("📊 KBS 국제 뉴스 분석 대시보드")
st.markdown("실시간 뉴스 크롤링 + AI 분석 + 키워드 트렌드")
st.markdown("---")

# 사이드바
with st.sidebar:
    st.header("⚙️ 크롤링 설정")

    # API 키 (.env에서 자동 로드)
    env_api_key = os.getenv("OPENAI_API_KEY", "")

    # UI에서 키 입력 (선택사항)
    user_input_key = st.text_input(
        "OpenAI API 키 (선택)",
        type="password",
        value="",
        placeholder="비워두면 .env 파일의 키를 사용합니다",
        help=".env 파일에 키가 있으면 입력하지 않아도 됩니다"
    )

    # 사용자 입력이 있으면 그것을 사용, 없으면 .env 키 사용
    api_key = user_input_key if user_input_key else env_api_key

    # API 키 상태 표시
    if api_key:
        st.success("✅ API 키 설정됨")
    else:
        st.warning("⚠️ API 키가 설정되지 않았습니다")

    st.markdown("---")

    # 날짜 범위
    st.subheader("📅 크롤링 날짜")
    num_days = st.slider("크롤링할 날짜 수", 1, 30, 3)

    st.markdown("---")

    # 페이지 수
    st.subheader("📄 페이지 설정")
    pages_per_day = st.slider("날짜당 페이지 수", 1, 10, 2)

    st.markdown("---")
    start_crawling = st.button("🚀 크롤링 시작", type="primary", use_container_width=True)

# 키워드 추출 함수 (한글)
def extract_keywords(text):
    """한글 텍스트에서 주요 키워드 추출 (명사 중심)"""
    # 불용어 제거
    stopwords = {'있다', '하다', '되다', '이다', '않다', '없다', '같다', '많다',
                 '크다', '작다', '높다', '낮다', '좋다', '나쁘다', '위해', '통해',
                 '대한', '있는', '하는', '되는', '이번', '올해', '지난', '오늘'}

    # 2글자 이상 한글 단어 추출
    words = re.findall(r'[가-힣]{2,}', text)

    # 불용어 제거 및 카운트
    filtered_words = [w for w in words if w not in stopwords]

    return filtered_words

# OpenAI 요약 함수
def summarize_news(content, client):
    try:
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": "뉴스를 정확하고 간결하게 3줄로 요약하세요."},
                {"role": "user", "content": f"다음 뉴스를 3줄로 요약:\n\n{content}"}
            ],
            max_tokens=200,
            temperature=0.7
        )
        return response.choices[0].message.content.strip()
    except Exception as e:
        return f"요약 실패: {str(e)}"

# AI 인사이트 생성 함수
def generate_insights(df, top_keywords, client):
    """수집된 뉴스 데이터를 분석하여 인사이트 생성"""
    try:
        # 뉴스 제목과 요약 샘플
        sample_titles = "\n".join(df['뉴스 제목'].head(10).tolist())
        keyword_str = ", ".join([f"{k}({v}건)" for k, v in top_keywords[:10]])

        prompt = f"""
다음은 최근 국제 뉴스 데이터 분석 결과입니다:

**수집 기간**: {df['기고 날짜'].min()} ~ {df['기고 날짜'].max()}
**총 뉴스 수**: {len(df)}개
**주요 키워드**: {keyword_str}

**주요 뉴스 제목들**:
{sample_titles}

위 데이터를 바탕으로 다음 관점에서 인사이트를 제공해주세요:

1. 🔥 현재 가장 핫한 국제 이슈 (3개)
2. 📈 트렌드 분석 (어떤 주제가 부상하고 있는지)
3. 💡 주목할 만한 인사이트 (숨겨진 패턴이나 연관성)

각 항목을 명확하게 구분하여 간결하게 작성해주세요.
"""

        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": "당신은 국제 뉴스 분석 전문가입니다."},
                {"role": "user", "content": prompt}
            ],
            max_tokens=500,
            temperature=0.8
        )

        return response.choices[0].message.content.strip()
    except Exception as e:
        return f"인사이트 생성 실패: {str(e)}"

# 크롤링 함수
def crawl_news(num_days, pages_per_day, api_key, progress_bar, status_text):
    client = OpenAI(api_key=api_key)

    chrome_options = Options()
    chrome_options.add_argument("--headless")
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")
    chrome_options.add_argument("--disable-gpu")

    driver = webdriver.Chrome(options=chrome_options)
    data = []
    base_url = "https://news.kbs.co.kr/news/pc/category/category.do?ctcd=0006&ref=pSiteMap"

    total_steps = num_days * pages_per_day
    current_step = 0

    try:
        status_text.text("🌐 KBS 국제 뉴스 접속 중...")
        driver.get(base_url)
        time.sleep(3)

        for day_num in range(num_days):
            try:
                current_date = driver.find_element(By.CSS_SELECTOR, ".datepicker-label .date").text
            except:
                current_date = datetime.now().strftime("%Y.%m.%d")

            status_text.text(f"📅 [{day_num + 1}/{num_days}일] {current_date} 크롤링 중...")

            for page_num in range(1, pages_per_day + 1):
                current_step += 1
                progress_bar.progress(current_step / total_steps)

                time.sleep(2)
                soup = BeautifulSoup(driver.page_source, "html.parser")
                news_items = soup.select(".box-contents.has-wrap .box-content")

                for item in news_items:
                    try:
                        link = item.get("href")
                        if not link:
                            continue

                        news_url = "https://news.kbs.co.kr" + link
                        title_elem = item.select_one(".title")
                        title = title_elem.text.strip() if title_elem else "제목 없음"

                        date_elem = item.select_one(".field-writer .date")
                        date = date_elem.text.strip() if date_elem else current_date

                        driver.execute_script(f"window.open('{news_url}', '_blank');")
                        driver.switch_to.window(driver.window_handles[1])
                        time.sleep(1)

                        detail_soup = BeautifulSoup(driver.page_source, "html.parser")
                        content_elem = detail_soup.select_one("#cont_newstext")
                        content = content_elem.text.strip() if content_elem else "내용 없음"

                        summary = summarize_news(content, client)
                        data.append([date, title, content, summary])

                        driver.close()
                        driver.switch_to.window(driver.window_handles[0])
                        time.sleep(0.5)

                    except Exception as e:
                        if len(driver.window_handles) > 1:
                            driver.close()
                            driver.switch_to.window(driver.window_handles[0])
                        continue

                if page_num < pages_per_day:
                    try:
                        next_button = driver.find_element(By.CSS_SELECTOR, f"#page{page_num + 1}")
                        driver.execute_script("arguments[0].click();", next_button)
                        time.sleep(2)
                    except:
                        break

            if day_num < num_days - 1:
                try:
                    prev_button = driver.find_element(By.CSS_SELECTOR, ".previous-button")
                    driver.execute_script("arguments[0].click();", prev_button)
                    time.sleep(3)
                except:
                    break

    finally:
        driver.quit()

    return data

# 크롤링 실행
if start_crawling:
    if not api_key:
        st.error("❌ OpenAI API 키를 입력하세요!")
    else:
        progress_bar = st.progress(0)
        status_text = st.empty()

        with st.spinner("크롤링 중..."):
            data = crawl_news(num_days, pages_per_day, api_key, progress_bar, status_text)

        progress_bar.progress(1.0)
        status_text.text("✅ 크롤링 완료!")

        if data:
            df = pd.DataFrame(data, columns=["기고 날짜", "뉴스 제목", "뉴스 내용", "3줄 요약"])
            st.session_state['df'] = df
            st.success(f"✅ 총 {len(df)}개의 뉴스를 수집했습니다!")
        else:
            st.error("❌ 수집된 뉴스가 없습니다.")

# 대시보드 표시
if 'df' in st.session_state:
    df = st.session_state['df']
    client = OpenAI(api_key=api_key)

    # 키워드 추출
    all_text = " ".join(df['뉴스 제목'] + " " + df['뉴스 내용'])
    keywords = extract_keywords(all_text)
    keyword_counts = Counter(keywords)
    top_keywords = keyword_counts.most_common(20)

    # 탭 구성
    tab1, tab2, tab3, tab4 = st.tabs(["📊 대시보드", "🔍 키워드 분석", "💡 AI 인사이트", "📥 데이터"])

    with tab1:
        st.header("📊 뉴스 분석 대시보드")

        # 통계 카드
        col1, col2, col3, col4 = st.columns(4)
        with col1:
            st.metric("총 뉴스", f"{len(df)}개")
        with col2:
            st.metric("수집 날짜", f"{df['기고 날짜'].nunique()}일")
        with col3:
            st.metric("평균 길이", f"{df['뉴스 내용'].str.len().mean():.0f}자")
        with col4:
            st.metric("주요 키워드", f"{len(top_keywords)}개")

        st.markdown("---")

        # 날짜별 뉴스 개수 차트
        st.subheader("📈 날짜별 뉴스 트렌드")
        date_counts = df['기고 날짜'].value_counts().sort_index()
        fig_timeline = px.line(
            x=date_counts.index,
            y=date_counts.values,
            labels={'x': '날짜', 'y': '뉴스 개수'},
            title="날짜별 뉴스 발행 추이"
        )
        fig_timeline.update_traces(mode='lines+markers', line_color='#FF6B6B')
        st.plotly_chart(fig_timeline, use_container_width=True)

        st.markdown("---")

        # Top 10 키워드 바 차트
        col1, col2 = st.columns(2)

        with col1:
            st.subheader("🔝 Top 10 키워드")
            top10_keywords = top_keywords[:10]
            fig_bar = px.bar(
                x=[k[1] for k in top10_keywords],
                y=[k[0] for k in top10_keywords],
                orientation='h',
                labels={'x': '빈도', 'y': '키워드'},
                title="가장 많이 언급된 키워드"
            )
            fig_bar.update_traces(marker_color='#4ECDC4')
            st.plotly_chart(fig_bar, use_container_width=True)

        with col2:
            st.subheader("☁️ 워드 클라우드")
            # 워드클라우드 생성
            wordcloud = WordCloud(
                font_path='C:\\Windows\\Fonts\\malgun.ttf',  # 한글 폰트
                width=800,
                height=400,
                background_color='white',
                colormap='viridis'
            ).generate_from_frequencies(dict(top_keywords))

            fig, ax = plt.subplots(figsize=(10, 5))
            ax.imshow(wordcloud, interpolation='bilinear')
            ax.axis('off')
            st.pyplot(fig)

    with tab2:
        st.header("🔍 키워드 상세 분석")

        # 키워드 검색
        search_keyword = st.text_input("🔎 키워드 검색", placeholder="검색할 키워드를 입력하세요")

        if search_keyword:
            filtered = df[df['뉴스 제목'].str.contains(search_keyword, case=False, na=False) |
                         df['뉴스 내용'].str.contains(search_keyword, case=False, na=False)]
            st.info(f"'{search_keyword}' 관련 뉴스: {len(filtered)}개")
            st.dataframe(filtered[['기고 날짜', '뉴스 제목', '3줄 요약']], use_container_width=True)

        st.markdown("---")

        # 전체 키워드 테이블
        st.subheader("📋 전체 키워드 순위")
        keyword_df = pd.DataFrame(top_keywords, columns=['키워드', '빈도'])
        keyword_df['순위'] = range(1, len(keyword_df) + 1)
        st.dataframe(keyword_df[['순위', '키워드', '빈도']], use_container_width=True, height=400)

    with tab3:
        st.header("💡 AI 인사이트")

        if st.button("🤖 AI 인사이트 생성", type="primary"):
            with st.spinner("AI가 뉴스를 분석하고 있습니다..."):
                insights = generate_insights(df, top_keywords, client)
                st.session_state['insights'] = insights

        if 'insights' in st.session_state:
            st.markdown(st.session_state['insights'])

    with tab4:
        st.header("📥 데이터 및 다운로드")

        # 데이터 미리보기
        st.subheader("📋 전체 뉴스 데이터")
        st.dataframe(df, use_container_width=True, height=400)

        # 엑셀 다운로드
        output = io.BytesIO()
        with pd.ExcelWriter(output, engine='openpyxl') as writer:
            df.to_excel(writer, index=False, sheet_name='국제뉴스')
            keyword_df.to_excel(writer, index=False, sheet_name='키워드')
        excel_data = output.getvalue()

        st.download_button(
            label="📥 엑셀 다운로드 (뉴스 + 키워드)",
            data=excel_data,
            file_name=f"국제뉴스_분석_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            use_container_width=True
        )

else:
    # 초기 화면
    st.info("👈 사이드바에서 설정 후 '크롤링 시작' 버튼을 클릭하세요!")

    with st.expander("📖 사용 가이드"):
        st.markdown("""
        ### 🚀 사용 방법

        1. **API 키**: .env 파일에서 자동 로드
        2. **날짜 설정**: 크롤링할 날짜 수 선택
        3. **페이지 설정**: 날짜당 페이지 수 선택
        4. **크롤링 시작**: 버튼 클릭
        5. **대시보드**: 4개 탭에서 분석 결과 확인

        ### 📊 대시보드 기능

        - **📊 대시보드**: 통계, 트렌드, 워드클라우드
        - **🔍 키워드 분석**: 키워드 검색 및 순위
        - **💡 AI 인사이트**: GPT 기반 트렌드 분석
        - **📥 데이터**: 엑셀 다운로드
        """)
