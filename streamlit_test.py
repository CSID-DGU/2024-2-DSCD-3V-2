import streamlit as st
from streamlit_chat import message
import pandas as pd
from datetime import date, timedelta  # 날짜 입력을 위해 필요
import time  # 챗봇 메시지 지연 위해 필요

from PIL import Image   # 챗봇 이미지 로드에 필요
import requests         # 챗봇 이미지 로드에 필요
import base64           # 챗봇 이미지 로드에 필요
from io import BytesIO  # 챗봇 이미지 로드에 필요
import openai
import re
import json

import lodging 
import travel
from streamlit_css import get_css, travel_card_style, accommodation_card_style, title_style  # CSS 모듈 불러오기


# Set your OpenAI API key directly in the code
openai.api_key = "your-api-key"  # Replace with your actual API key

# 페이지 설정
st.set_page_config(page_title="Travel Planner Chatbot", layout="wide")

########################################## CHATBOT ##########################################

# CSS 스타일 정의     # 나영수정(11/14): 별도 파일 만들기 완료
st.markdown(get_css(), unsafe_allow_html=True)

# Google Geocoding API 키 설정
google_maps_api_key = "your-api-key"

# Google 지도에 마커와 경로를 표시하는 함수
def create_google_map_js(day_df, google_maps_api_key):
    markers_js = ""
    for idx, row in day_df.iterrows():
        markers_js += f"""
            geocoder.geocode({{ 'address': '{row['주소']}' }}, function(results, status) {{
                if (status === 'OK') {{
                    const marker = new google.maps.Marker({{
                        map: map,
                        position: results[0].geometry.location,
                        label: '{idx + 1}'
                    }});
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

        {markers_js}  // 각 장소의 마커 추가

        const flightPath = new google.maps.Polyline({{
          path: route,
          geodesic: true,
          strokeColor: "#FF0000",
          strokeOpacity: 1.0,
          strokeWeight: 2
        }});

        flightPath.setMap(map);

        setTimeout(() => {{ map.fitBounds(bounds); }}, 1000);
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
        unsafe_allow_html=True
    )

# 사용자 메시지 출력 함수
def user_message(text):
    st.markdown(
        f"""
        <div class="chatbox">
            <div class="user-bubble">{text}</div>
        </div>
        """,
        unsafe_allow_html=True
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
        unsafe_allow_html=True
    )

# 세션 초기화 - for 문 이용
if "messages" not in st.session_state:
    st.session_state.messages = []
required_keys = [
    "destination","destination_kr",
    "travel_dates","travel_dates_str","itinerary_days",
    "total_days","stay_duration","stay_duration_kr",
    "companion","travel_style","itinerary_preference",
    "accommodation_type","itinerary_generated","itinerary",
    "current_step"
]

for key in required_keys:
    if key not in st.session_state:
        st.session_state[key] = None

# 각 단계의 논리 구조 코드 : 상우 수정(11/12)
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

# Reset function to go back to the start
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
    ]:
        st.session_state[key] = None
    st.session_state.messages = []
    st.session_state.current_step = 0

    # 애플리케이션을 다시 실행하여 초기 화면을 표시
    st.rerun()

# 메시지 및 질문 출력 후 추가 요청 질문 표시
def follow_up_question():
    chatbot_message("여행 일정 생성이 끝났습니다! 처음 서비스를 이용하고 싶다면 선택해 주세요 😊")
    
    # "처음으로" 옵션을 pills 스타일로 제공
    selected_option = st.pills(
        label=None,
        options=["처음으로"],
        selection_mode="single"
    )

    # "처음으로"가 선택된 경우 reset_conversation 호출
    if selected_option and "처음으로" in selected_option:
        reset_conversation()

# 여행 일정 생성 함수
def generate_itinerary():
    if not st.session_state.itinerary_generated:
        with st.spinner("여행 일정을 생성하는 중입니다..."):
            # 여행 일정 생성
            itinerary = travel.final_recommendations(
                city=st.session_state.destination,
                trip_duration=st.session_state.total_days,
                companions=st.session_state.companion,
                travel_style=st.session_state.travel_style,
                itinerary_style=st.session_state.itinerary_preference
            )
            st.session_state.itinerary = itinerary
            st.session_state.messages.append(
                {"role": "assistant", "content": st.session_state.itinerary}
            )
            st.session_state.itinerary_generated = True

            # 숙소 추천 생성
            if st.session_state.accommodation_type and st.session_state.destination:
                # 숙소 추천 생성
                recommended_accommodations = lodging.final_recommendations(
                    st.session_state.destination,
                    st.session_state.stay_duration,
                    st.session_state.companion,
                    st.session_state.accommodation_type,
                    st.session_state.get("travel_dates_str", None)
                )

                # 불필요한 설명 제거 및 JSON 변환
                start_index = recommended_accommodations.find("[")
                end_index = recommended_accommodations.rfind("]")
                json_text = recommended_accommodations[start_index:end_index + 1].strip()

                # JSON 유효성 확인
                json_text = re.sub(r"\n\s*", "", json_text)
                accommodations = json.loads(json_text)

                # 세션에 숙소 데이터 저장
                st.session_state.accommodations = accommodations
    

# 사이드바를 통한 입력 인터페이스
with st.sidebar:
    st.markdown('<div class="sidebar-title">여행 일정 생성 Chat</div>', unsafe_allow_html=True)
    # Assistant message for greeting
    chatbot_message(
        "안녕하세요 여행자님! 여행자님의 계획 생성을 도와줄 리포(RIPO)입니다👋 저와 함께 멋진 여행 일정을 만들어봐요!✨ 그럼 질문에 맞는 답을 체크박스로 선택해주시면 바로 시작해볼게요!",  # 문구변경함
    )

    # 1초 지연
    time.sleep(0.5)

    # 도시 선택 체크박스 UI + 사용자 입력 상자 추가
    chatbot_message("어느 도시를 여행하고 싶으신가요? 아래에서 도시를 선택해주세요.")

    # 도시 이름과 해당 영어 표기 매핑
    cities = {"일본 오사카": "osaka", "프랑스 파리": "paris", "태국 방콕": "bangkok", "미국 뉴욕": "newyork"}

    # Pills 스타일로 도시 선택 (기본 선택 없음)
    selected_city = st.pills(
        label=None,
        options=list(cities.keys()),  # 도시 목록
        selection_mode="single"
    )

    # 선택된 도시에 따라 상태 업데이트
    if selected_city:
        selected_city_en = cities[selected_city]
        st.session_state.destination = selected_city_en  # 영어 이름으로 세션 상태 업데이트
        st.session_state.destination_kr = selected_city
        st.session_state.current_step = 1
        user_message(f"{selected_city}")  # 사용자 선택 도시 메시지
        chatbot_message(f"{selected_city} 여행을 계획해드리겠습니다.")

    # 지연
    time.sleep(0.5)

    # 여행 날짜 선택 (달력 형식) - 나영 추가 수정(11/14)
    if st.session_state.get("destination"):
        chatbot_message("여행 날짜를 선택해주세요 📅 아직 확정된 여행 날짜가 없다면 여행 기간을 입력해주세요")

        # 기본값을 설정하지만 선택 여부에 따라 업데이트
        selected_dates = st.date_input(
            "여행 날짜 선택 (선택하지 않으셔도 됩니다):",
            value=(date.today(), date.today()),
            key="travel_dates",
            min_value=date.today(),
            help="시작일과 종료일을 선택하세요."
        )

        # 사용자 정의 여행 기간 입력받기
        custom_duration = st.text_input("또는 여행 기간을 'O박 O일' 형식으로 입력해주세요", key="custom_duration")

        # 여행 기간 설정 로직
        if custom_duration:
            # 사용자 정의 입력 처리
            if re.match(r"^\d+박\s*\d+일$", custom_duration):
                nights, days = map(int, re.findall(r'\d+', custom_duration))
                start_date = date.today()
                end_date = start_date + timedelta(days=nights)
            
                # 선택한 사용자 정의 기간을 상태에 업데이트
                st.session_state.stay_duration = f"{nights} nights {days} days"
                st.session_state.stay_duration_kr = f"{nights}박 {days}일"
                st.session_state.itinerary_days = [
                    (start_date + timedelta(days=i)).strftime("Day %d") for i in range(days)
                ]
                st.session_state.total_days = days

                # 사용자 정의 기간에 대한 메시지 출력
                user_message(f"{st.session_state.stay_duration_kr}")
                chatbot_message(f"{st.session_state.stay_duration_kr} 동안의 멋진 여행을 준비해드리겠습니다!")
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
                    (start_date + timedelta(days=i)).strftime("Day %d") for i in range(days)
                ]
                st.session_state.total_days = days

                # 선택한 날짜를 "YYYY/MM/DD ~ YYYY/MM/DD" 형식으로 저장
                st.session_state.travel_dates_str = f"{start_date.strftime('%Y/%m/%d')} ~ {end_date.strftime('%Y/%m/%d')}"

                # 날짜 선택에 대한 메시지 출력
                user_message(f"{st.session_state.travel_dates_str}")
                chatbot_message(f"{st.session_state.travel_dates_str} 동안의 멋진 여행을 준비해드리겠습니다!")
        else:
            # 선택한 날짜 또는 사용자 정의 기간이 없으면 초기 상태 유지
            st.session_state.stay_duration = None
    
    # 지연
    time.sleep(0.5)

    # 한글로 입력된 입력을 gpt 이용해서 영어로 번역해주는 함수     
    def translate_to_english(text):
        try:
            response = openai.Completion.create(
                engine="davinci",   # 가장 강력한 GPT-3 모델
                prompt=f"Translate the following Korean text to English: {text}",
                max_tokens=60  # 번역에 충분한 토큰 수
            )
            return response.choices[0].text.strip()
        except Exception as e:
            return text  # 번역 실패 시 원본 텍스트 반환

    # 여행 동행인 선택 - 나영수정(11/14): pills 스타일 사용, 다중선택 변경 완료
    if st.session_state.stay_duration:
        chatbot_message("누구와 함께 여행을 떠나시나요? 골라주세요! 중복선택도 가능합니다 😎")
        companions = {
            "혼자": "Alone",
            "친구와": "With friends",
            "연인과": "With partner",
            "가족과": "With family",
            "어린아이와": "With children",
            "반려동물과": "With pets",
            "단체 여행": "Group travel"
        }

        # Pills 스타일로 동행인 선택
        selected_companions = st.pills(
            label=None,
            options=list(companions.keys()),
            selection_mode="multi"
        )

        # 기본 선택된 동행인 목록 초기화
        selected_companion_en = []
        selected_companions_kr = ""

        # 사용자 정의 동행인 입력받기
        custom_companion = st.text_input("다른 동행인을 입력하시려면 'OO 과/와' 형식으로 입력해주세요", key="custom_companion")

        if custom_companion:
            # 사용자 정의 동행인이 입력된 경우, pills 선택 초기화하고 사용자 정의 동행인만 반영
            translated_companion = translate_to_english(custom_companion)
            selected_companion_en = [translated_companion]
            selected_companions_kr = custom_companion
            st.session_state.companion = selected_companion_en
            st.session_state.current_step = 3
            # 선택된 동행인 메시지 출력
            user_message(f"{selected_companions_kr}")
            chatbot_message(f"{selected_companions_kr} 함께하는 멋진 여행을 준비해드리겠습니다!")
        elif selected_companions:
            # 사용자 정의 동행인이 없을 때만 pills 선택 반영
            selected_companion_en = [companions[companion] for companion in selected_companions]
            selected_companions_kr = ", ".join(selected_companions)
            st.session_state.companion = selected_companion_en
            st.session_state.current_step = 3
            # 선택된 동행인 메시지 출력
            user_message(f"{selected_companions_kr}")
            chatbot_message(f"{selected_companions_kr} 함께하는 멋진 여행을 준비해드리겠습니다!")

    # 지연
    time.sleep(0.5)

    # 여행 스타일 선택 - 나영수정(11/14): pills 스타일 사용, 다중선택 변경 완료
    if st.session_state.companion:
        chatbot_message("어떤 여행 스타일을 선호하시나요? 아래에서 선택하거나 직접 입력해주세요. 중복선택도 가능합니다 😎")
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

        # Pills 스타일로 여행 스타일 선택
        selected_styles = st.pills(
            label=None,
            options=list(travel_styles.keys()),
            selection_mode="multi"
        )

        # 기본 선택된 여행 스타일 목록 초기화
        selected_styles_en = []
        selected_styles_kr = ""

        # 사용자 정의 여행 스타일 입력받기
        custom_style = st.text_input("다른 스타일을 원하시면 입력해주세요", key="custom_style")

        if custom_style:
            # 사용자 정의 스타일이 입력된 경우, pills 선택 초기화하고 사용자 정의 스타일만 반영
            translated_style = translate_to_english(custom_style)
            selected_styles_en = [translated_style]
            selected_styles_kr = custom_style
            st.session_state.travel_style = selected_styles_en
            st.session_state.current_step = 4
            # 선택된 스타일 메시지 출력
            user_message(f"{selected_styles_kr}")
            chatbot_message(f"{selected_styles_kr} 타입의 여행을 선택했습니다.")
        elif selected_styles:
            # 사용자 정의 스타일이 없을 때만 pills 선택 반영
            selected_styles_en = [travel_styles[style] for style in selected_styles]
            selected_styles_kr = ", ".join(selected_styles)
            st.session_state.travel_style = selected_styles_en
            st.session_state.current_step = 4
            # 선택된 스타일 메시지 출력
            user_message(f"{selected_styles_kr}")
            chatbot_message(f"{selected_styles_kr} 타입의 여행을 선택했습니다.")

    # 지연
    time.sleep(0.5)

    # 여행 일정 스타일 선택 - 나영수정(11/14): pills 스타일 사용
    if st.session_state.travel_style:
        chatbot_message("선호하는 여행 일정 스타일은 무엇인가요? 두 가지 타입 중 선택해주세요 🤗")
        itinerary_preferences = {
            "빼곡한 일정": "Packed itinerary",
            "널널한 일정": "Relaxed itinerary"
        }

        # Pills 스타일로 여행 일정 스타일 선택
        selected_preference_kr = st.pills(
            label=None,
            options=list(itinerary_preferences.keys()),
            selection_mode="single"
        )

        # 선택된 일정 스타일에 따라 상태 업데이트
        if selected_preference_kr:
            selected_preference_en = itinerary_preferences[selected_preference_kr]
            st.session_state.itinerary_preference = selected_preference_en
            st.session_state.current_step = 5
            user_message(f"{selected_preference_kr}")   # 사용자 선택 일정 스타일 메시지
            chatbot_message(f"{selected_preference_kr} 일정 스타일로 일정을 준비하겠습니다.")

    # 지연
    time.sleep(0.5)

    # 숙소 유형 선택 - pills와 text_input 같이 표시
    if st.session_state.itinerary_preference:
        chatbot_message("어떤 숙소를 원하시나요? 아래에서 선택하거나 직접 입력해주세요. 중복선택도 가능합니다 😎")
    
        accommodations = {
            "공항 근처 숙소": "Accommodation near the airport",
            "5성급 호텔": "5-star hotel",
            "수영장이 있는 숙소": "with a swimming pool",
            "게스트 하우스": "Guest house",
            "민박집": "Bed and Breakfast",
            "전통가옥": "Traditional house"
        }

        # Pills 스타일로 숙소 유형 선택
        selected_accommodations_kr = st.pills(
            label="숙소 유형 선택",
            options=list(accommodations.keys()),
            selection_mode="multi"
        )

        # 기본 선택된 숙소 유형 목록 초기화
        selected_accommodations_en = []
        selected_accommodations_kr_str = ""

        # 사용자 정의 숙소 유형 입력받기
        custom_accommodation = st.text_input("다른 숙소 유형을 원하시면 입력해주세요", key="custom_accommodation")

        # 선택된 항목 처리
        if custom_accommodation:
            # 사용자 정의 숙소 유형 추가
            translated_accommodation = translate_to_english(custom_accommodation)
            selected_accommodations_en = [translated_accommodation]
            selected_accommodations_kr_str = custom_accommodation
            st.session_state.accommodation_type = selected_accommodations_en
            st.session_state.current_step = 6

            # 선택된 숙소 유형 메시지 출력
            user_message(f"{selected_accommodations_kr_str}")
            chatbot_message(f"{selected_accommodations_kr_str} 스타일의 숙소로 추천해드리겠습니다.")
    
        elif selected_accommodations_kr:
            # Pills 선택된 항목 추가
            selected_accommodations_en = [accommodations[accommodation] for accommodation in selected_accommodations_kr]
            selected_accommodations_kr_str = ", ".join(selected_accommodations_kr)
            st.session_state.accommodation_type = selected_accommodations_en
            st.session_state.current_step = 6

            # 선택된 숙소 유형 메시지 출력
            user_message(f"{selected_accommodations_kr_str}")
            chatbot_message(f"{selected_accommodations_kr_str} 스타일의 숙소로 추천해드리겠습니다.")


    # 지연
    time.sleep(1.5)


    # 여행 일정 생성 조건
    if (
        st.session_state.destination
        and st.session_state.stay_duration
        and st.session_state.companion
        and st.session_state.travel_style
        and st.session_state.itinerary_preference
        and st.session_state.accommodation_type
    ):
        chatbot_message("기본 여행 질문이 끝났습니다. 😊 여행 정보 작성이 완료되었나요? 완료되었다면 여행 일정을 생성합니다! 추가적인 요청 사항이 있으시다면 '아니오'를 선택해주세요")

        # '네'와 '아니요' 선택 옵션
        response = st.pills(
            label=" ",
            options=["네", "아니요"],
            selection_mode="single",
            key="confirm_response"
        )

        # '네'를 선택한 경우
        if response == "네":
            chatbot_message("여행 일정을 생성합니다!")
            #st.session_state.show_itinerary = True
            generate_itinerary()

            # 지연
            time.sleep(1.5)
            follow_up_question()

        # '아니요'를 선택한 경우
        elif response == "아니요":
            additional_question = st.text_input(
                "추가적으로 입력하고 싶은 여행 정보가 있다면 입력해주세요 📝", 
                key="additional_question",
                value=""
            )
            if additional_question.strip():
                translated_question = translate_to_english(additional_question)
                chatbot_message("추가 요청사항 입력이 끝났습니다. 😊 여행 일정을 생성합니다!")
                #st.session_state.show_itinerary = True
                generate_itinerary()

                # 지연
                time.sleep(1.5)
                follow_up_question()


        

########################################## 결과창 ##########################################

###### 여행일정 출력 페이지 수정 완료 - 가린 수정(11/14)
# 사용자 입력 상태 확인
destination = st.session_state.get('destination_kr', None)
stay_duration = st.session_state.get('stay_duration_kr', None)

# CSS 스타일 정의     # 나영수정(11/14): 별도 파일 만들기 완료
st.markdown(get_css(), unsafe_allow_html=True)

if destination is None or stay_duration is None:
    # 여행 일정 생성 전 화면
    st.markdown("""
        <div class="header-container">
            <div class="header-title">TRiPO 여행 일정 생성</div>
            <div class="header-subtitle">트리포와 함께 만든 여행일정으로 떠나보세요.</div>
        </div>
        <div style="text-align: center; margin-top: 100px;">
        </div>
    """, unsafe_allow_html=True)
else:
    # 여행 일정 생성 후 화면
    st.markdown(f"""
        <div class="header-container">
            <div class="header-title">{destination} {stay_duration} 추천 일정</div>
            <div class="header-subtitle">트리포와 함께 만든 여행일정으로 떠나보세요.</div>
        </div>
    """, unsafe_allow_html=True)


    # 여기서 지도나 여행 일정 카드 등을 추가하세요
    # 예: st.map(), 여행 일정 카드 등

# 오른쪽에 지도 및 일정 표시
with st.container():   
    # 여행 일정 생성 조건: 모든 필수 요소가 선택되었는지 확인
    if st.session_state.itinerary:

        # 불필요한 설명 제거 및 JSON 변환
        start_index = st.session_state.itinerary.find("{")
        end_index = st.session_state.itinerary.rfind("}")
        json_text = st.session_state.itinerary[start_index:end_index+1]
        data = json.loads(json_text)

        # "여행 일정" 키 아래의 리스트를 DataFrame으로 변환
        df = pd.DataFrame(data["여행 일정"])

        st.markdown(travel_card_style(), unsafe_allow_html=True)

        # 여행 일정 표시
        days = sorted(df['날짜'].unique())
        selected_day = st.pills(None, days, selection_mode="single", default=days[0])

        # 선택한 날짜에 해당하는 장소의 주소 및 장소명 추출
        day_df = df[df['날짜'] == selected_day]
        # Google 지도 표시 - day 선택 버튼 위에 배치
        st.components.v1.html(create_google_map_js(day_df, google_maps_api_key), height=200)
        
        # 선택된 날짜에 맞는 일정 표시
        time_periods = ["오전", "오후", "저녁"]
        for time_period in time_periods:
            st.markdown(f"<h3 class='subheader'>{time_period} 일정</h3>", unsafe_allow_html=True)
            
            # 선택한 날짜와 시간대에 맞는 데이터 필터링
            filtered_df = df[(df['날짜'] == selected_day) & (df['시간대'] == time_period)]
            
            # 일정 카드 형식으로 표시
            for _, row in filtered_df.iterrows():
                st.markdown(
                    f"""
                    <div class="travel-card">
                        <h5>{row['장소명']}</h5>
                        <p class="time">{row['운영시간']}</p>
                        <hr>
                        <p class="description"><strong>📌 장소 소개:</strong> {row['장소 소개']}</p>
                    </div>
                    """,
                    unsafe_allow_html=True
                )

        # 페이지에 숙소 추천 스타일 추가
        st.markdown(accommodation_card_style(), unsafe_allow_html=True)

        # 숙소 추천 표시
        if "accommodations" in st.session_state:
            accommodations = st.session_state.accommodations

            st.markdown(title_style(), unsafe_allow_html=True)
            st.markdown("<div class='accommodation-title'>이런 숙소는 어떠신가요?</div>", unsafe_allow_html=True)

            cols = st.columns(5)  # 5열로 나누기

            for i, accommodation in enumerate(accommodations):
                with cols[i % 5]:  # 각 열에 하나씩 표시
                    st.markdown(
                        f"""
                        <div class="accommodation-card">
                            <h6>{accommodation.get('name', '이름없음')}</h6>
                            <p>평점: ⭐ {accommodation.get('rating', '없음')}</p>
                            <p>가격: {accommodation.get('approximate price(KRW)', '없음')}</p>
                        </div>
                        """, 
                        unsafe_allow_html=True
                    )
                