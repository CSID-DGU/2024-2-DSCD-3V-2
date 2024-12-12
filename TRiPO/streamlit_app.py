import streamlit as st
from streamlit_chat import message
import streamlit.components.v1 as components
import pandas as pd
from datetime import date, timedelta  # 날짜 입력을 위해 필요
import time  # 챗봇 메시지 지연 위해 필요

from PIL import Image  # 챗봇 이미지 로드에 필요
import requests  # 챗봇 이미지 로드에 필요
import base64  # 챗봇 이미지 로드에 필요
from io import BytesIO  # 챗봇 이미지 로드에 필요
import openai
import re
import json

# api 로드에 필요
from dotenv import load_dotenv
import os

import lodging
import travel
from streamlit_css import (
    get_status,
    get_css,
    travel_card_style,
    accommodation_card_style,
    title_style,
    get_loading1, get_loading, get_slide
)  # CSS 모듈 불러오기

# 배포용 api 설정
openai_api_key = st.secrets["OPENAI_API_KEY"]
google_maps_api_key = st.secrets["GOOGLE_API_KEY"]

if not openai_api_key or not google_maps_api_key:
   raise ValueError("API 키가 Streamlit Secrets에 설정되지 않았습니다.")

# .env 파일 로드
load_dotenv()
# API 키 가져오기
# openai_api_key = os.getenv("OPENAI_API_KEY")

# OpenAI 라이브러리에 API 키 설정
import openai
openai.api_key = openai_api_key

# 페이지 설정
st.set_page_config(page_title="TRiPO", layout="wide")

########################################## CHATBOT ##########################################

# CSS 스타일 정의     # 나영수정(11/14): 별도 파일 만들기 완료
st.markdown(get_css(), unsafe_allow_html=True)

# Google Geocoding API 키 설정
google_maps_api_key = os.getenv("GOOGLE_API_KEY")


# Google 지도에 마커와 경로를 표시하는 함수
def create_google_map_js(day_df, google_maps_api_key):
    markers_js = ""
    for idx, row in day_df.iterrows():

        # Google 지도 링크 생성 (PlaceID 기반) - travel.py 수정해야함
        place_id = row["PlaceID"]  # Google Place ID 가져오기
        google_maps_link = f"https://www.google.com/maps/place/?q=place_id:{place_id}"  # Place ID 기반 Google 지도 링크 생성

        # 각 장소에 대해 마커와 Info Window 추가
        markers_js += f"""
            geocoder.geocode({{ 'placeId': '{row['PlaceID']}' }}, function(results, status) {{
                if (status === 'OK') {{
                    // 마커 생성
                    const marker = new google.maps.Marker({{
                        map: map,
                        position: results[0].geometry.location,
                        label: '{idx + 1}'
                    }});

                    // Info Window 생성 (주소 표시)
                    const infowindow = new google.maps.InfoWindow({{
                        content: `<div>
                                    <strong>{row['장소명']}</strong><br>  <!-- 장소명 표시 -->
                                    {row['PlaceID']}<br>  <!-- 주소 표시 -->
                                    <a href="{google_maps_link}" target="_blank">Google 지도에서 보기</a>  <!-- Google 지도 링크 추가 -->
                                  </div>`
                    }});

                    // 마커 클릭 이벤트 리스너 추가
                    marker.addListener('click', function() {{
                        infowindow.open(map, marker);  // 마커 클릭 시 Info Window 열기
                    }});

                    // 기존 로직: 경로와 지도 범위 설정
                    route.push(results[0].geometry.location);  // 경로 좌표 추가
                    bounds.extend(results[0].geometry.location);  // 지도 범위 조정
                }}
            }});
        """

    # HTML 및 JavaScript 코드
    map_html = f"""
    <div id="map" style="height: 500px; width: 100%; margin-bottom: 20px;"></div>
    <script>
      function initMap() {{
        const map = new google.maps.Map(document.getElementById("map"), {{
          center: {{ lat: 13.7563, lng: 100.5018 }},
          zoom: 12
        }});

        const geocoder = new google.maps.Geocoder();
        const route = [];
        const bounds = new google.maps.LatLngBounds();

        {markers_js}  // 각 장소의 마커 및 Info Window 추가

        // 경로를 표시하는 Polyline 생성
        const flightPath = new google.maps.Polyline({{
          path: route,
          geodesic: true,
          strokeColor: "#FF0000",
          strokeOpacity: 1.0,
          strokeWeight: 2
        }});

        flightPath.setMap(map);  // 지도에 Polyline 표시

        setTimeout(() => {{ map.fitBounds(bounds); }}, 1000);  // 지도 범위 조정
      }}
    </script>
    <script async defer src="https://maps.googleapis.com/maps/api/js?key={google_maps_api_key}&callback=initMap"></script>
    """
    return map_html


# 챗봇 이미지 로드 및 인코딩
image_url = "https://raw.githubusercontent.com/CSID-DGU/2024-2-DSCD-3V-2/main/data/RIPO_image.png?raw=true"
response = requests.get(image_url)
if response.status_code == 200:
    chatbot_image = Image.open(BytesIO(response.content))
    buffered = BytesIO()
    chatbot_image.save(buffered, format="PNG")
    chatbot_image_base64 = base64.b64encode(buffered.getvalue()).decode()
else:
    st.error("챗봇 이미지를 불러오는 데 실패했습니다.")
    chatbot_image_base64 = ""


# 챗봇 메시지 출력 함수
def chatbot_message(text):
    st.markdown(
        f"""
        <div class="chatbox">
            <div class="chatbot-message">
                <img src="data:image/png;base64,{chatbot_image_base64}" class="chatbot-avatar"/>
                <div class="chatbot-bubble">{text}</div>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )


# 사용자 메시지 출력 함수
def user_message(text):
    st.markdown(
        f"""
        <div class="chatbox">
            <div class="user-bubble">{text}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )


# 입력창 디자인
def message_input():
    st.markdown(
        """
        <div class="input-container">
            <input type="text" class="message-input" placeholder="메시지를 입력하세요..."/>
            <button class="send-button">보내기</button>
        </div>
        """,
        unsafe_allow_html=True,
    )


# 세션 초기화 - for 문 이용
if "messages" not in st.session_state:
    st.session_state.messages = []
required_keys = [
    "destination",
    "destination_kr",
    "travel_dates",
    "travel_dates_str",
    "itinerary_days",
    "total_days",
    "stay_duration",
    "stay_duration_kr",
    "companion",
    "travel_style",
    "itinerary_preference",
    "accommodation_type",
    "itinerary_generated",
    "itinerary",
    "current_step",
    "itinerary_generating",
    "user_request"
]

for key in required_keys:
    if key not in st.session_state:
        st.session_state[key] = None

# 각 단계의 논리 구조 코드
if st.session_state.current_step == 0 and st.session_state.destination:
    st.session_state.current_step = 1
if st.session_state.current_step == 1 and st.session_state.stay_duration:
    st.session_state.current_step = 2
if st.session_state.current_step == 2 and st.session_state.companion:
    st.session_state.current_step = 3
if st.session_state.current_step == 3 and st.session_state.travel_style:
    st.session_state.current_step = 4
if st.session_state.current_step == 4 and st.session_state.itinerary_preference:
    st.session_state.current_step = 5
if st.session_state.current_step == 5 and st.session_state.accommodation_type:
    st.session_state.current_step = 6


# 챗봇 대화 초기화 코드(처음으로 버튼 연동 부분)- 수정 부분(상우)
def reset_conversation():
    """전체 대화를 초기화하고 처음 단계로 돌아갑니다."""
    for key in [
        "destination",
        "stay_duration",
        "companion",
        "travel_style",
        "itinerary_preference",
        "accommodation_type",
        "itinerary_generated",
        "itinerary",
        "selected_companions",        # 여행 동행인 초기화
        "companions_selected",        # 여행 동행인 선택 완료 여부 초기화
        "selected_styles",            # 여행 스타일 초기화
        "styles_selected",            # 여행 스타일 선택 완료 여부 초기화
        "selected_itinerary_style",   # 여행 일정 스타일 초기화
        "itinerary_style_selected",   # 여행 일정 스타일 선택 완료 여부 초기화
        "accommodations_selected",    # 숙소 선택 완료 여부 초기화
        "selected_accommodations",     # 숙소 초기화
        "user_request"
    ]:
        st.session_state[key] = None
    st.session_state.messages = []
    st.session_state.current_step = 0 #(current_step=0으로 초기화)
    # 초기 화면 제목을 리셋하기 위한 부분
    st.session_state.destination_kr = None
    st.session_state.stay_duration_kr = None
    # 애플리케이션을 다시 실행하여 초기 화면을 표시 #(오른쪽 제목) #################확인필요##############
    st.session_state.page_title = "TRiPO 여행 일정 생성"
    st.rerun()


def reset_widget_state(current_step):  # 각 step에 대해 초기화할 부분들
    fields_to_reset = {
        0: ["destination", "destination_kr"],
        1: ["stay_duration", "stay_duration_kr", "travel_dates", "travel_dates_str"],
        2: ["companion", "companions_selected"],
        3: ["travel_style", "styles_selected"],
        4: [
            "itinerary_preference",
            "selected_itinerary_style",
            "itinerary_style_selected",
        ],
        5: ["accommodation_type", "accommodations_selected"],
    }

    if current_step in fields_to_reset:
        for field in fields_to_reset[current_step]:
            st.session_state[field] = None


# 이전 단계로 돌아가기 함수
def previous_step():
    """이전 단계로 돌아가며 선택 항목을 초기화합니다."""
    if st.session_state.current_step > 0:
        st.session_state.current_step -= 1  # 이전 단계로 이동
        reset_widget_state(st.session_state.current_step)
        # 단계별 초기화할 상태 설정
        fields_to_reset = {
            0: ["destination", "destination_kr"],
            1: [
                "stay_duration",
                "stay_duration_kr",
                "travel_dates",
                "travel_dates_str",
            ],
            2: ["companion", "companions_selected"],
            3: ["travel_style", "styles_selected"],
            4: ["itinerary_preference"],
            5: ["accommodation_type", "accommodations_selected"],
        }

        # 현재 단계에 맞는 필드 초기화
        fields = fields_to_reset.get(st.session_state.current_step, [])
        for field in fields:
            if field in st.session_state:
                st.session_state[field] = None

        reset_widget_state(st.session_state.current_step)
        st.rerun()


# 메시지 및 질문 출력 후 추가 요청 질문 표시
def follow_up_question():
    chatbot_message(
        "여행 일정 생성이 끝났습니다! 처음 서비스를 이용하고 싶다면 선택해 주세요 😊"
    )

    # "처음으로" 옵션을 pills 스타일로 제공
    selected_option = st.pills(
        label=None, options=["처음으로"], selection_mode="single"
    )

    # "처음으로"가 선택된 경우 reset_conversation 호출
    if selected_option == "처음으로":
        reset_conversation()


# 여행 일정 생성 함수
def generate_itinerary():
    if not st.session_state.itinerary_generated:
        with st.sidebar:
            with st.spinner("여행 일정을 생성하는 중입니다..."):
                max_attempts = 10  # 무한 루프 방지를 위한 최대 시도 횟수
                attempts = 0
                
                itinerary = pd.DataFrame()  # 초기화된 빈 데이터프레임
                
                # 여행 일정 생성 반복 실행
                while (itinerary.empty or len(itinerary)<st.session_state.total_days*5) and attempts < max_attempts:
                    attempts += 1
                    itinerary = travel.final_recommendations(
                        city=st.session_state.destination,
                        trip_duration=st.session_state.total_days,
                        companions=st.session_state.companion,
                        travel_style=st.session_state.travel_style,
                        itinerary_style=st.session_state.itinerary_preference,
                        user_request = st.session_state.get("user_request", None)
                    )
                    
                    if itinerary.empty:
                        st.warning(f"여행 일정을 다시 생성하는 중입니다. ({attempts}/{max_attempts} 시도 중)")

                # 반복 종료 후에도 비어 있다면 오류 처리
                if itinerary.empty:
                    st.error("여행 일정 데이터를 생성할 수 없습니다. 다시 시도해주세요.")
                    return
                
                # 성공적으로 데이터를 생성한 경우
                st.session_state.itinerary = itinerary
                st.session_state.messages.append(
                    {"role": "assistant", "content": st.session_state.itinerary}
                )
                st.session_state.itinerary_generated = True

                # 숙소 추천 생성
                if st.session_state.accommodation_type and st.session_state.destination:
                    recommended_accommodations = lodging.final_recommendations(
                        st.session_state.destination,
                        st.session_state.companion,
                        st.session_state.accommodation_type
                    )

                    # 세션에 숙소 데이터 저장
                    st.session_state.accommodations = recommended_accommodations

# 자동 스크롤 함수
def add_scroll():
    components.html("""
                    <div id="scroll-target"></div>
                    <script>
                        document.getElementById('scroll-target').scrollIntoView({behavior: "smooth"});
                    </script>
                """, height=0, width=0)


# 사이드바를 통한 입력 인터페이스
with st.sidebar:
    if "initialized" not in st.session_state:
        st.session_state.current_step = 0
        st.session_state.initialized = True
    st.markdown(
        '<div class="sidebar-title">여행 일정 생성 Chat</div>', unsafe_allow_html=True
    )
    chatbot_message(
        "안녕하세요 여행자님! 여행자님의 계획 생성을 도와줄 리포(RIPO)입니다👋 저와 함께 멋진 여행 일정을 만들어봐요!✨ 그럼 질문에 맞는 답을 체크박스로 선택해주시면 바로 시작해볼게요!",  # 문구변경함
    )
    chatbot_message("어느 도시를 여행하고 싶으신가요? 아래에서 도시를 선택해주세요.")

    # 수정한 부분(11/29-상우)
    if st.session_state.current_step == 0:
        cities = {
            "일본 오사카": "osaka",
            "프랑스 파리": "paris",
            "태국 방콕": "bangkok",
            "미국 뉴욕": "newyork",
        }
        selected_city = st.pills(
            label=None,
            options=list(cities.keys()),
            selection_mode="single",
            key="destination_pills",
        )

        if selected_city:
            st.session_state.destination = cities[selected_city]
            st.session_state.destination_kr = selected_city
            st.session_state.current_step = 1  # 다음 단계로 이동
            st.rerun()   # pills 없어지도록 추가
    

    # 수정한 부분(11/29- 상우)
    # 여행 날짜 선택 (달력 형식)
    if st.session_state.get("destination"):
        if st.session_state.get("destination_kr"):
            # chatbot_message("어느 도시를 여행하고 싶으신가요? 아래에서 도시를 선택해주세요.")
            user_message(f"{st.session_state.destination_kr}")
            chatbot_message(
                f"{st.session_state.destination_kr} 여행을 계획해드리겠습니다."
            )
            add_scroll()  # 자동스크롤

        if "travel_dates_reset" not in st.session_state:
            st.session_state["travel_dates_reset"] = False
        if "dates_selected" not in st.session_state:
            st.session_state["dates_selected"] = False  # 기본값: 날짜 미선택

        if st.session_state["travel_dates_reset"]:
            default_dates = (date.today(), date.today())
            st.session_state["travel_dates_reset"] = False  # 리셋 플래그 해제
        else:
            default_dates = st.session_state.get(
                "travel_dates", (date.today(), date.today())
            )

        chatbot_message(
            "여행 날짜를 선택해주세요 📅 아직 확정된 여행 날짜가 없다면 여행 기간을 입력해주세요"
        )

        # 기본값을 설정하지만 선택 여부에 따라 업데이트
        selected_dates = st.date_input(
            "여행 날짜 선택 (선택하지 않으셔도 됩니다):",
            value=(date.today(), date.today()),
            key="travel_dates",
            min_value=date.today(),
            help="시작일과 종료일을 선택하세요.",
        )

        # 사용자 정의 여행 기간 입력받기
        custom_duration = st.text_input(
            "또는 여행 기간을 'O박 O일' 형식으로 입력해주세요", key="custom_duration"
        )

        # "처음으로", "이전으로" 옵션 추가
        navigation_options = st.pills(
            label=None,
            options=["처음으로"],
            selection_mode="single",
            key="date_navigation",
        )

        # 선택한 옵션에 따라 동작
        if navigation_options == "처음으로":
            reset_conversation()

        # 여행 기간 설정 로직
        if custom_duration:
            # 사용자 정의 입력 처리
            if re.match(r"^\d+박\s*\d+일$", custom_duration):
                nights, days = map(int, re.findall(r"\d+", custom_duration))
    
                # "n박 n+1일" 조건 확인
                if days == nights + 1:
                    start_date = date.today()
                    end_date = start_date + timedelta(days=nights)

                    # 선택한 사용자 정의 기간을 상태에 업데이트
                    st.session_state.stay_duration = f"{nights} nights {days} days"
                    st.session_state.stay_duration_kr = f"{nights}박 {days}일"
                    st.session_state.itinerary_days = [
                        (start_date + timedelta(days=i)).strftime("Day %d")
                        for i in range(days)
                    ]
                    st.session_state.total_days = days
                    st.session_state["dates_selected"] = True  # 날짜 선택 완료 상태로 변경
                    add_scroll()

                    # 사용자 정의 기간에 대한 메시지 출력
                    user_message(f"{st.session_state.stay_duration_kr}")
                    chatbot_message(
                        f"{st.session_state.stay_duration_kr} 동안의 멋진 여행을 준비해드리겠습니다!"
                    )
                else:
                    st.error("입력 형식이 올바르지 않습니다. 예: '5박 6일'")
            else:
                st.error("입력 형식이 올바르지 않습니다. 예: '5박 6일'")

        elif isinstance(selected_dates, tuple) and len(selected_dates) == 2:
            # 날짜 선택 시 처리
            start_date, end_date = selected_dates
            nights = (end_date - start_date).days
            days = nights + 1

            # 선택된 날짜가 기본값과 다른 경우에만 업데이트
            if nights > 0 or days > 1:
                st.session_state.stay_duration = f"{nights} nights {days} days"
                st.session_state.stay_duration_kr = f"{nights}박 {days}일"
                st.session_state.itinerary_days = [
                    (start_date + timedelta(days=i)).strftime("Day %d")
                    for i in range(days)
                ]
                st.session_state.total_days = days

                # 선택한 날짜를 "YYYY/MM/DD ~ YYYY/MM/DD" 형식으로 저장
                st.session_state.travel_dates_str = f"{start_date.strftime('%Y/%m/%d')} ~ {end_date.strftime('%Y/%m/%d')}"
                st.session_state["dates_selected"] = True  # 날짜 선택 완료 상태로 변경
                add_scroll()

                # 날짜 선택에 대한 메시지 출력
                user_message(f"{st.session_state.travel_dates_str}")
                chatbot_message(
                    f"{st.session_state.travel_dates_str} 동안의 멋진 여행을 준비해드리겠습니다!"
                )
        else:
            # 선택한 날짜 또는 사용자 정의 기간이 없으면 초기 상태 유지
            st.session_state.stay_duration = None
            st.session_state.current_step = 2

    # 한글로 입력된 입력을 gpt 이용해서 영어로 번역해주는 함수
    def translate_to_english(text):
        try:
            response = openai.Completion.create(
                engine="davinci",  # 가장 강력한 GPT-3 모델
                prompt=f"Translate the following Korean text to English: {text}",
                max_tokens=60,  # 번역에 충분한 토큰 수
            )
            return response.choices[0].text.strip()
        except Exception as e:
            return text  # 번역 실패 시 원본 텍스트 반환

    # 여행 동행인 선택
    if st.session_state.stay_duration:
        chatbot_message(
            "누구와 함께 여행을 떠나시나요? 골라주세요! 중복선택도 가능합니다 😎"
        )
        companions = {
            "혼자": "Alone",
            "친구와": "With friends",
            "연인과": "With partner",
            "가족과": "With family",
            "어린아이와": "With children",
            "반려동물과": "With pets",
            "단체 여행": "Group travel"
        }

        # 상태 초기화
        if "companions_selected" not in st.session_state:
            st.session_state.companions_selected = False
        if "selected_companions" not in st.session_state:
            st.session_state.selected_companions = []

        # Pills 옵션 및 선택 로직
        if not st.session_state.companions_selected:
            selected_companions = st.pills(
                label=None,
                options=list(companions.keys()) + ["처음으로"],
                selection_mode="multi",
                key="companion_pills",
            )

            # '처음으로' 선택 시 대화 초기화
            if "처음으로" in selected_companions:
                reset_conversation()

            # 다른 동행인 입력
            custom_companion = st.text_input(
                "다른 동행인을 입력하시려면 'OO 과/와' 형식으로 입력해주세요",
                key="custom_companion",
            )

            # 선택 완료 버튼 클릭 시
            if st.button("선택 완료", key="confirm_companions"):
                st.session_state.companions_selected = True  # 선택 완료 상태로 변경
                if custom_companion:
                    translated_companion = translate_to_english(custom_companion)
                    selected_companion_en = [translated_companion]
                    selected_companions_kr = custom_companion
                    st.session_state.selected_companions = selected_companion_en
                else:
                    st.session_state.selected_companions = [
                        comp for comp in selected_companions if comp != "처음으로"
                    ]
                st.rerun()   # 선택완료 버튼 한번만 누르도록 추가   
        else:
            # 선택 완료 후 결과 메시지 출력
            selected_companions = st.session_state.selected_companions
            selected_companions_en = [
                companions.get(comp, comp) for comp in selected_companions
            ]
            selected_companions_kr = ", ".join(selected_companions)
            st.session_state.companion = selected_companions_en
            add_scroll()  # 자동스크롤

            user_message(f"{selected_companions_kr}")
            if selected_companions_kr == '혼자':
                chatbot_message(
                    f"{selected_companions_kr}만의 멋진 여행을 준비해드리겠습니다!"
                )
            elif selected_companions_kr == '단체 여행':
                chatbot_message(
                    f"멋진 {selected_companions_kr}을 준비해드리겠습니다!"
                )
            else:
                chatbot_message(
                    f"{selected_companions_kr} 함께하는 멋진 여행을 준비해드리겠습니다!"
                )
            st.session_state.current_step = 3

    # 수정한 부분(11/29-상우)
    # 여행 스타일 선택
    if st.session_state.companion:
        chatbot_message(
            "어떤 여행 스타일을 선호하시나요? 요청하신 여행 스타일에 맞춰 여행 일정을 생성해 드립니다! 여행 스타일을 아래에서 선택하거나 직접 입력해주세요. 중복선택도 가능합니다 😎"
        )
        travel_styles = {
            "액티비티": "Activity",
            "핫플레이스": "Hotspots",
            "자연": "Nature",
            "관광지": "Sightseeing",
            "힐링": "Relaxing",
            "쇼핑": "Shopping",
            "맛집": "Gourmet",
            "럭셔리 투어": "Luxury Tour"
        }

        # 상태 초기화
        if "styles_selected" not in st.session_state:
            st.session_state.styles_selected = False
        if "selected_styles" not in st.session_state:
            st.session_state.selected_styles = []

        # Pills 옵션 및 선택 로직
        if not st.session_state.styles_selected:
            selected_styles = st.pills(
                label=None,
                options=list(travel_styles.keys()) + ["처음으로", "이전으로"],
                selection_mode="multi",
                key="style_pills",
            )

            # '처음으로' 선택 시 대화 초기화
            if "처음으로" in selected_styles:
                reset_conversation()
            elif "이전으로" in selected_styles:
                previous_step()

            # 사용자 정의 여행 스타일 입력받기
            custom_style = st.text_input(
                "다른 스타일을 원하시면 입력해주세요", key="custom_style"
            )

            # '선택 완료' 버튼 클릭 시
            if st.button("선택 완료", key="confirm_styles"):
                if custom_style:
                    # 사용자 정의 스타일이 입력된 경우
                    translated_style = translate_to_english(custom_style)
                    st.session_state.selected_styles = [custom_style]
                    st.session_state.travel_style = [translated_style]
                    add_scroll()  # 자동스크롤
                    user_message(f"{custom_style}")
                    chatbot_message(f"요청하신 스타일대로 여행을 준비해 드리겠습니다.")
                elif selected_styles:
                    # Pills 선택된 항목 반영
                    selected_styles_en = [
                        travel_styles.get(style, style)
                        for style in selected_styles
                        if style not in ["처음으로", "이전으로"]
                    ]
                    selected_styles_kr = ", ".join(selected_styles)
                    st.session_state.selected_styles = selected_styles
                    st.session_state.travel_style = selected_styles_en
                    add_scroll()  # 자동스크롤
                    user_message(f"{selected_styles_kr}")
                    chatbot_message("요청하신 스타일대로 여행을 준비해 드리겠습니다.")
                else:
                    st.error("여행 스타일을 선택하거나 입력해주세요.")
                st.session_state.styles_selected = True
                st.rerun()   # 선택완료 버튼 한번만 누르도록 추가
        else:
            # 선택 완료 후 결과 메시지 출력
            selected_styles = st.session_state.selected_styles
            selected_styles_en = [
                travel_styles.get(style, style) for style in selected_styles
            ]
            selected_styles_kr = ", ".join(selected_styles)
            st.session_state.travel_style = selected_styles_en
            add_scroll()  # 자동스크롤

            user_message(f"{selected_styles_kr}")
            chatbot_message("요청하신 스타일대로 여행을 준비해 드리겠습니다.")
            st.session_state.current_step = 4

    # 여행 일정 스타일 선택
    if st.session_state.travel_style:
        chatbot_message(
            "선호하는 여행 일정 스타일은 무엇인가요? 두 가지 타입 중 선택해주세요 🤗"
        )
        itinerary_preferences = {
            "빼곡한 일정": "Packed itinerary",
            "널널한 일정": "Relaxed itinerary",
        }

        # 상태 초기화
        if "itinerary_style_selected" not in st.session_state:
            st.session_state.itinerary_style_selected = False
        if "selected_itinerary_style" not in st.session_state:
            st.session_state.selected_itinerary_style = None

        # Pills 옵션 및 선택 로직
        if not st.session_state.itinerary_style_selected:
            selected_preference_kr = st.pills(
                label=None,
                options=list(itinerary_preferences.keys()) + ["처음으로", "이전으로"],
                selection_mode="single",
                key="itinerary_style_pills",
            )

            # '처음으로' 선택 시 대화 초기화
            if selected_preference_kr == "처음으로":
                reset_conversation()
            elif selected_preference_kr == "이전으로":
                previous_step()
            elif selected_preference_kr:
                # 선택 완료 처리
                st.session_state.itinerary_style_selected = True
                st.session_state.selected_itinerary_style = selected_preference_kr
                selected_preference_en = itinerary_preferences[selected_preference_kr]
                st.session_state.itinerary_preference = selected_preference_en
                selected_itinerary_style_kr = st.session_state.selected_itinerary_style
                add_scroll()  # 자동스크롤
                user_message(f"{selected_itinerary_style_kr}")
                chatbot_message(
                    f"{selected_itinerary_style_kr}으로 여행 일정을 준비하겠습니다."
                )
                st.rerun()   # pills 없어지도록 추가
        else:
            # 선택 완료 후 결과 메시지 출력
            selected_itinerary_style_kr = st.session_state.selected_itinerary_style
            add_scroll()  # 자동스크롤
            user_message(f"{selected_itinerary_style_kr}")
            chatbot_message(
                f"{selected_itinerary_style_kr}으로 여행 일정을 준비하겠습니다."
            )
            st.session_state.current_step = 5

    # 숙소 유형 선택 - pills와 text_input 같이 표시
    if st.session_state.itinerary_preference:
        chatbot_message(
            "어떤 숙소를 원하시나요? 원하시는 숙소 유형에 따라 숙소를 추천해 드립니다. 선호하는 숙소 유형을 아래에서 선택하거나 직접 입력해주세요. 중복선택도 가능합니다 😎"
        )

        accommodations = {
            "공항 근처 숙소": "Accommodation near the airport",
            "4성급 이상 호텔": "super deluxe 5-star hotel",
            "수영장이 있는 숙소": "with a swimming pool",
            "게스트 하우스": "Guest house",
            "호스텔": "hostel",
            "전통가옥": "Traditional house",
        }

        # 상태 초기화
        if "accommodations_selected" not in st.session_state:
            st.session_state.accommodations_selected = False
        if "selected_accommodations" not in st.session_state:
            st.session_state.selected_accommodations = []

        # Pills 옵션 및 선택 로직
        if not st.session_state.accommodations_selected:
            selected_accommodations = st.pills(
                label=None,
                options=list(accommodations.keys()) + ["처음으로", "이전으로"],
                selection_mode="multi",
                key="accommodation_pills",
            )

            # '처음으로' 선택 시 대화 초기화
            if "처음으로" in selected_accommodations:
                reset_conversation()
            elif "이전으로" in selected_accommodations:
                previous_step()

            # 사용자 정의 숙소 유형 입력받기
            custom_accommodation = st.text_input(
                "다른 숙소 유형을 원하시면 입력해주세요", key="custom_accommodation"
            )

            # 선택 완료 버튼 클릭 시
            if st.button("선택 완료", key="confirm_accommodations"):
                st.session_state.accommodations_selected = True  # 선택 완료 상태로 변경
                # 기존 선택 옵션과 사용자 입력을 합치기
                selected_accommodations_combined = [
                    acc
                    for acc in selected_accommodations
                    if acc not in ["처음으로", "이전으로"]
                ]
                if custom_accommodation:
                    translated_accommodation = translate_to_english(
                        custom_accommodation
                    )
                    selected_accommodations_combined.append(custom_accommodation)
                    st.session_state.selected_accommodations.append(
                        translated_accommodation
                    )

                st.session_state.selected_accommodations = (
                    selected_accommodations_combined
                )
                st.rerun()   # 선택완료 버튼 한번만 누르도록 추가
        else:
            # 선택 완료 후 결과 메시지 출력
            selected_accommodations = st.session_state.selected_accommodations
            selected_accommodations_en = [
                accommodations.get(acc, acc) for acc in selected_accommodations
            ]
            selected_accommodations_kr = ", ".join(selected_accommodations)
            st.session_state.accommodation_type = selected_accommodations_en
            add_scroll()  # 자동스크롤

            user_message(f"{selected_accommodations_kr}")
            chatbot_message(
                f"{selected_accommodations_kr} 스타일의 숙소를 추천해드리겠습니다."
            )
            st.session_state.current_step = 6

    # 여행 일정 생성 조건
    if (
        st.session_state.destination
        and st.session_state.stay_duration
        and st.session_state.companion
        and st.session_state.travel_style
        and st.session_state.itinerary_preference
        and st.session_state.accommodation_type
    ):
        chatbot_message(
            "기본 여행 질문이 끝났습니다. 😊 여행 정보 작성이 완료되었나요? 완료되었다면 여행 일정을 생성합니다! 추가적인 요청 사항이 있으시다면 '아니오'를 선택해주세요"
        )

        # '네'와 '아니요' 선택 옵션
        response = st.pills(
            label=" ",
            options=["네", "아니요"],
            selection_mode="single",
            key="confirm_response",
        )

        # '네'를 선택한 경우
        if response == "네":
            # 허재원 추가_1130
            st.session_state.itinerary_generating = True
            # 여행 일정 생성 중 상태 활성화
            add_scroll()  # 자동스크롤
            chatbot_message("여행 일정을 생성합니다!")
            st.session_state.user_request = None
            # st.session_state.show_itinerary = True
            #generate_itinerary()
            #add_scroll()  # 자동스크롤
            #follow_up_question()

        # '아니요'를 선택한 경우
        elif response == "아니요":
            add_scroll()  # 자동스크롤
            additional_question = st.text_input(
                "추가적으로 입력하고 싶은 여행 정보가 있다면 입력해주세요 📝",
                key="additional_question",
                value="",
            )
            if additional_question.strip():
                translated_question = translate_to_english(additional_question)
                translated_question = additional_question
                st.session_state.user_request = translated_question
                add_scroll()  # 자동스크롤
                chatbot_message(
                    "추가 요청사항 입력이 끝났습니다. 😊 여행 일정을 생성합니다!"
                )
                # st.session_state.show_itinerary = True
                st.session_state.itinerary_generating = True  # 생성 상태 활성화
                #generate_itinerary()
                #add_scroll()  # 자동스크롤
                #follow_up_question()

########################################## 결과창 ##########################################

###### 여행일정 출력 페이지 수정 완료 - 가린 수정(11/14)
# 사용자 입력 상태 확인
destination = st.session_state.get("destination_kr", None)
stay_duration = st.session_state.get("stay_duration_kr", None)

# CSS 스타일 정의     # 나영수정(11/14): 별도 파일 만들기 완료
st.markdown(get_css(), unsafe_allow_html=True)

if destination is None or stay_duration is None:
    # 여행 일정 생성 전 화면
    st.markdown(
        """
        <div class="header-container" style="font-family: 'Pretendard', sans-serif;">
            <div class="header-title">TRiPO 여행 일정 생성</div>
            <div class="header-subtitle">트리포와 함께 만든 여행일정으로 떠나보세요.</div>
        </div>
    """,
        unsafe_allow_html=True,
    )

else:
    # 여행 일정 생성 후 화면
    st.markdown(
        f"""
        <div class="header-container" style="font-family: 'Pretendard', sans-serif;">
            <div class="header-title">{destination} {stay_duration} 추천 일정</div>
            <div class="header-subtitle">트리포와 함께 만든 여행일정으로 떠나보세요.</div>
    """,
        unsafe_allow_html=True,
    )

# 오른쪽에 일정 표시
# HTML 구조 정의
LOADER_HTML = """
<div style="display: flex; justify-content: center; align-items: center; height: 200px;">
    <div class="loader"></div>
</div>
"""

# CSS와 JavaScript를 활용한 슬라이더 정의
SLIDER_HTML = """
<div class="slider">
    <div class="slides">
        <!-- 슬라이드 이미지 -->
        <div class="slide"><img src="https://raw.githubusercontent.com/CSID-DGU/2024-2-DSCD-3V-2/main/data/chatbot1.png?raw=true" alt="Image 1"></div>
        <div class="slide"><img src="https://raw.githubusercontent.com/CSID-DGU/2024-2-DSCD-3V-2/main/data/chatbot2.png?raw=true" alt="Image 2"></div>
        <div class="slide"><img src="https://raw.githubusercontent.com/CSID-DGU/2024-2-DSCD-3V-2/main/data/chatbot3.png?raw=true" alt="Image 3"></div>
    </div>
</div>

<style>
/* 슬라이더 컨테이너 */
.slider {
    width: 308px; /* 확대된 슬라이더 가로 크기 */
    height: 450px; /* 확대된 슬라이더 세로 크기 */
    overflow: hidden; /* 넘치는 부분 숨김 */
    position: relative; /* 상대적 위치 설정 */
    margin: auto; /* 중앙 정렬 */
}

/* 슬라이드 이미지 컨테이너 */
.slides {
    display: flex;
    width: calc(308px * 3); /* 이미지 개수만큼 폭 설정 */
    animation: slide 6s infinite; /* 6초 주기로 애니메이션 실행 */
}

/* 개별 슬라이드 */
.slide {
    min-width: 308px; /* 확대된 슬라이드의 가로 크기 */
    height: 450px; /* 확대된 슬라이드의 세로 크기 */
}

/* 이미지 */
.slide img {
    width: 308px; /* 이미지의 가로 크기 */
    height: 450px; /* 이미지의 세로 크기 */
    object-fit: cover; /* 비율 유지하며 크기 조정 */
}

/* 애니메이션 */
@keyframes slide {
    0% { transform: translateX(0); }
    33% { transform: translateX(-308px); }
    66% { transform: translateX(-616px); }
    100% { transform: translateX(0); }
}
</style>
"""

# 숫자 추출 함수 정의
def extract_number(day):
    match = re.search(r'\d+', day)  # 문자열에서 숫자 부분 추출
    return int(match.group()) if match else 0


with st.container():
    if st.session_state.get("itinerary_generating", False):
        # 일정 생성 중 스피너와 캐릭터 표시
        #with st.sidebar:
            #with st.spinner("여행 일정을 생성하는 중입니다..."):
        generate_itinerary()
        # 일정 생성 완료 상태로 업데이트
        st.session_state.itinerary_generating = False
        st.session_state.itinerary_generated = True
        add_scroll()  # 자동스크롤
        with st.sidebar:
            follow_up_question()
    
    # 여행 일정 생성 조건: 모든 필수 요소가 선택되었는지 확인
    if isinstance(st.session_state.itinerary, pd.DataFrame):  # DataFrame 확인
        df = st.session_state.itinerary
        #st.write(df)
        #st.write(df.empty)

        st.markdown(travel_card_style(), unsafe_allow_html=True)

        # 여행 일정 표시
        days = sorted(df['날짜'].unique(), key=extract_number)
        selected_day = st.pills(None, days, selection_mode="single", default=days[0])

        # 선택한 날짜에 해당하는 장소의 주소 및 장소명 추출
        day_df = df[df["날짜"] == selected_day]
        # Google 지도 표시 - day 선택 버튼 위에 배치
        st.components.v1.html(
            create_google_map_js(day_df, google_maps_api_key), height=200
        )

        # 선택된 날짜에 맞는 일정 표시
        time_periods = ["오전", "오후", "저녁"]
        for time_period in time_periods:
            st.markdown(
                f"<h3 class='subheader'>{time_period} 일정</h3>", unsafe_allow_html=True
            )

            # 선택한 날짜와 시간대에 맞는 데이터 필터링
            filtered_df = df[
                (df["날짜"] == selected_day) & (df["시간대"] == time_period)
            ]
            # <img src="{image_url}" alt="Accommodation Image" class="accommodation-image"/>
            # 여행 일정 카드 출력
            for idx, row in filtered_df.iterrows():
                image_url = (
                    row["이미지"] if row["이미지"] else "https://via.placeholder.com/40"
                )  # 이미지 없을 경우 기본 이미지
                st.markdown(
                    f"""
                    <div class="travel-card-container">
                        <div class="card-number">
                            <div class="circle">{idx + 1}</div>
                        </div>
                        <div class="travel-card">
                            <div class="travel-card-header">
                                <img src="{image_url}" alt="Place Image" />
                                <div>
                                    <h5>{row['장소명']}</h5>
                                    <p class="time">{row.get('운영시간', '운영시간 정보 없음')}</p>
                                </div>
                            </div>
                            <hr>
                            <p class="description">📌 {row['장소 소개']}</p>
                        </div>
                    </div>
                    """,
                    unsafe_allow_html=True,
                )

        # 페이지에 숙소 추천 스타일 추가
        st.markdown(accommodation_card_style(), unsafe_allow_html=True)

        # 숙소 추천 표시
        if "accommodations" in st.session_state:
            accommodations = st.session_state.accommodations
            #st.write(accommodations)

            st.markdown(title_style(), unsafe_allow_html=True)
            st.markdown(
                "<div class='accommodation-title'>이런 숙소는 어떠신가요?</div>",
                unsafe_allow_html=True,
            )

            cols = st.columns(5)  # 5열로 나누기

            for i, row in accommodations.iterrows():
                with cols[i % 5]:
                    image_url = row["이미지"]
                    place_id = row["PlaceID"]  # Google Place ID 가져오기
                    booking_url = (
                        f"https://www.google.com/maps/place/?q=place_id:{place_id}"
                    )

                    if image_url != "없음":
                        st.markdown(
                            f"""
                            <div class="accommodation-card">
                                <img src="{image_url}" alt="Accommodation Image" class="accommodation-image"/>
                                <h6>{row['장소명']}</h6>
                                <h6>⭐ {row.get('평점', '4.7')}</h6>
                                <p>
                                    <a href="{booking_url}" target="_blank" style="text-decoration: none; color: #007bff; display: flex; align-items: center;">
                                        <img src="https://cdn-icons-png.flaticon.com/512/25/25284.png" 
                                            alt="Link Icon" 
                                            style="width: 14px; height: 14px; vertical-align: middle; margin-right: 5px;" />
                                        <span style="font-size: 12px;">예약하기</span>
                                    </a>
                                </p>
                            </div>
                            """,
                            unsafe_allow_html=True,
                        )
                    else:
                        st.markdown(
                            f"""
                            <div class="accommodation-card">
                                <h6>{row['장소명']}</h6>
                                <h6>⭐ {row.get('평점', '4.7')}</h6>
                                <p>
                                    <a href="{booking_url}" target="_blank" style="text-decoration: none; color: #007bff; display: flex; align-items: center;">
                                        <img src="https://cdn-icons-png.flaticon.com/512/25/25284.png" 
                                            alt="Link Icon" 
                                            style="width: 14px; height: 14px; vertical-align: middle; margin-right: 5px;" />
                                        <span style="font-size: 14px;">예약하기</span>
                                    </a>
                                </p>
                            </div>
                            """,
                            unsafe_allow_html=True,
                        )
    else : 
        # 사용자 입력을 받고 있는 중 화면
        st.markdown(SLIDER_HTML, unsafe_allow_html=True)
        st.markdown(f"{get_loading1()}", unsafe_allow_html=True)
        st.markdown(LOADER_HTML, unsafe_allow_html=True)
