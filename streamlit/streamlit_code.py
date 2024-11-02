import streamlit as st
import openai
import re
from streamlit_chat import message

# Set your OpenAI API key directly in the code
openai.api_key = "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"  # Replace with your actual API key

# 페이지 설정
st.set_page_config(page_title="Travel Planner Chatbot", layout="wide")

# Add custom CSS for styling (white theme)
st.markdown(
    """
    <style>
        body {
            background-color: #273346;
        }
        .title { font-size: 36px; font-weight: bold; color: #333333; }
        .subtitle { font-size: 24px; font-weight: bold; margin-top: 20px; color: #333333; }
        .bot-response, .user-response { margin: 10px 0; padding: 10px; border-radius: 5px; }
        .bot-response { background-color: #f1f1f1; color: #333333; }
        .user-response { background-color: #e1f5fe; color: #0c5460; }
        .itinerary-content { margin-top: 10px; background-color: #fafafa; color: #333333; padding: 15px; border-radius: 8px; font-size: 16px; line-height: 1.6; }
    </style>
""",
    unsafe_allow_html=True,
)

# 제목과 설명
st.title("🌍 여행 계획 챗봇")
st.write(
    "이 챗봇은 개인 맞춤형 여행 일정을 제공합니다. 다양한 목적지와 여행 기간을 선택하고 추가 정보를 입력해보세요."
)

# 세션 초기화
if "messages" not in st.session_state:
    st.session_state.messages = []
if "destination" not in st.session_state:
    st.session_state.destination = None
if "stay_duration" not in st.session_state:
    st.session_state.stay_duration = None
if "companion" not in st.session_state:
    st.session_state.companion = None
if "travel_style" not in st.session_state:
    st.session_state.travel_style = None
if "itinerary_preference" not in st.session_state:
    st.session_state.itinerary_preference = None
if "accommodation_type" not in st.session_state:
    st.session_state.accommodation_type = None
if "itinerary_generated" not in st.session_state:
    st.session_state.itinerary_generated = False
if "itinerary" not in st.session_state:
    st.session_state.itinerary = ""
if "current_step" not in st.session_state:
    st.session_state.current_step = 0  # 현재 단계 추적 변수


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


# 수정한 부분
def calculate_trip_days(duration):
    """입력된 여행 기간에서 총 며칠인지 계산"""
    match = re.match(r"(\d+)박\s*(\d+)일", duration)
    if match:
        nights = int(match.group(1))
        days = int(match.group(2))
        return days
    return None


# Go back to the previous step
def previous_step():
    """이전 단계로 돌아가 현재 단계의 선택을 초기화합니다."""
    if st.session_state.current_step > 0:
        st.session_state.current_step -= 1
        # Reset the specific choice based on the current step
        if st.session_state.current_step == 0:
            st.session_state.destination = None
        elif st.session_state.current_step == 1:
            st.session_state.stay_duration = None
        elif st.session_state.current_step == 2:
            st.session_state.companion = None
        elif st.session_state.current_step == 3:
            st.session_state.travel_style = None
        elif st.session_state.current_step == 4:
            st.session_state.itinerary_preference = None
        elif st.session_state.current_step == 5:
            st.session_state.accommodation_type = None
        st.session_state.itinerary_generated = False  # 일정 생성 상태 초기화


# 사이드바를 통한 입력 인터페이스
with st.sidebar:
    # Assistant message for greeting
    message(
        "안녕하세요 여행자님! 여행자님의 계획 생성을 도와줄 트리포입니다. 저와 함께 멋진 여행 일정을 만들어봐요! 그럼 질문에 맞는 답을 체크박스로 선택해주시면 바로 시작해볼게요!",
        is_user=False,
    )

    # 도시 선택 체크박스 UI + 사용자 입력 상자 추가
    message(
        "어느 도시를 여행하고 싶으신가요? 아래에서 도시를 선택하거나 직접 입력해주세요.",
        is_user=False,
    )
    cities = ["오사카", "파리", "방콕", "뉴욕"]

    for city in cities:
        if st.checkbox(
            city, key=f"city_{city}", disabled=st.session_state.destination is not None
        ):
            st.session_state.destination = city
            st.session_state.current_step = 1
            message(f"{st.session_state.destination}로 여행을 가고 싶어!", is_user=True)
            message(
                f"{st.session_state.destination}로의 여행을 계획해드리겠습니다.",
                is_user=False,
            )

    custom_city = st.text_input(
        "다른 도시를 원하시면 직접 입력해주세요", key="custom_city"
    )
    if custom_city:
        st.session_state.destination = custom_city
        st.session_state.current_step = 1
        message(f"{st.session_state.destination}로 여행을 가고 싶어!", is_user=True)
        message(
            f"{st.session_state.destination}로의 여행을 계획해드리겠습니다.",
            is_user=False,
        )

    # 여행 기간 선택
    if st.session_state.destination:
        message(
            "언제 여행을 떠날 예정인가요? 아래에서 선택하거나 직접 입력해주세요.",
            is_user=False,
        )
        durations = ["1박 2일", "2박 3일", "3박 4일", "Custom"]

        for duration in durations:
            if st.checkbox(
                duration,
                key=f"duration_{duration}",
                disabled=st.session_state.stay_duration is not None,
            ):
                st.session_state.stay_duration = duration
                st.session_state.current_step = 2
                message(
                    f"{st.session_state.stay_duration}만큼의 여행을 가고 싶어!",
                    is_user=True,
                )
                message(
                    f"{st.session_state.stay_duration}의 기간만큼의 여행을 계획해드리겠습니다.",
                    is_user=False,
                )

        custom_duration = st.text_input(
            "다른 여행 기간을 원하시면 'O박 O일' 형식으로 입력해주세요",
            key="custom_duration",
        )
        if custom_duration:
            if re.match(r"^\d+박\s*\d+일$", custom_duration):
                st.session_state.stay_duration = custom_duration
                st.session_state.current_step = 2
                message(
                    f"{st.session_state.stay_duration}만큼의 여행을 가고 싶어!",
                    is_user=True,
                )
                message(
                    f"{st.session_state.stay_duration}의 기간만큼의 여행을 계획해드리겠습니다.",
                    is_user=False,
                )
            else:
                st.warning(
                    "입력 형식이 올바르지 않습니다. 예: '2박 3일' 형태로 다시 입력해주세요."
                )
    # 여행 동반자 선택
    if st.session_state.stay_duration:
        message(
            "누구와 함께 여행을 떠나시나요? 하나만 선택하거나 직접 입력해주세요.",
            is_user=False,
        )
        companions = [
            "혼자",
            "친구와",
            "연인과",
            "가족과",
            "어린아이와",
            "반려동물과",
            "단체 여행",
        ]

        for companion in companions:
            if st.checkbox(
                companion,
                key=f"companion_{companion}",
                disabled=st.session_state.companion is not None,
            ):
                st.session_state.companion = companion
                st.session_state.current_step = 3
                message(
                    f"이번 여행은 {st.session_state.companion}와 함께 떠나고 싶어!",
                    is_user=True,
                )
                message(
                    f"{st.session_state.companion}와 함께하는 멋진 여행을 준비해드리겠습니다!",
                    is_user=False,
                )

        custom_companion = st.text_input(
            "다른 동반자를 원하시면 입력해주세요", key="custom_companion"
        )
        if custom_companion:
            st.session_state.companion = custom_companion
            st.session_state.current_step = 3
            message(
                f"이번 여행은 {st.session_state.companion}와 함께 떠나고 싶어!",
                is_user=True,
            )
            message(
                f"{st.session_state.companion}와 함께하는 멋진 여행을 준비해드리겠습니다!",
                is_user=False,
            )

    # 여행 스타일 선택
    if st.session_state.companion:
        message(
            "어떤 여행 스타일을 선호하시나요? 아래에서 선택하거나 직접 입력해주세요.",
            is_user=False,
        )
        travel_styles = [
            "액티비티",
            "핫플레이스",
            "자연",
            "관광지",
            "힐링",
            "쇼핑",
            "맛집",
            "럭셔리 투어",
        ]

        for style in travel_styles:
            if st.checkbox(
                style,
                key=f"style_{style}",
                disabled=st.session_state.travel_style is not None,
            ):
                st.session_state.travel_style = style
                st.session_state.current_step = 4
                message(
                    f"{st.session_state.travel_style} 스타일의 여행을 떠나고 싶어",
                    is_user=True,
                )
                message(
                    f"{st.session_state.travel_style} 타입의 여행을 선택했습니다.",
                    is_user=False,
                )

        custom_style = st.text_input(
            "다른 스타일을 원하시면 입력해주세요", key="custom_style"
        )
        if custom_style:
            st.session_state.travel_style = custom_style
            st.session_state.current_step = 4
            message(
                f"{st.session_state.travel_style} 스타일의 여행을 떠나고 싶어",
                is_user=True,
            )
            message(
                f"{st.session_state.travel_style} 타입의 여행을 선택했습니다.",
                is_user=False,
            )

    # 여행 일정 스타일 선택
    if st.session_state.travel_style:
        message(
            "선호하는 여행 일정 스타일은 무엇인가요? 선택하거나 직접 입력해주세요.",
            is_user=False,
        )
        itinerary_preferences = ["빼곡한 일정 선호", "널널한 일정 선호"]

        for preference in itinerary_preferences:
            if st.checkbox(
                preference,
                key=f"itinerary_{preference}",
                disabled=st.session_state.itinerary_preference is not None,
            ):
                st.session_state.itinerary_preference = preference
                st.session_state.current_step = 5
                message(
                    f"{st.session_state.itinerary_preference} 여행 일정을 선호해",
                    is_user=True,
                )
                message(
                    f"{st.session_state.itinerary_preference} 일정 스타일로 일정을 준비하겠습니다.",
                    is_user=False,
                )

        custom_itinerary = st.text_input(
            "다른 일정 스타일을 원하시면 입력해주세요", key="custom_itinerary"
        )
        if custom_itinerary:
            st.session_state.itinerary_preference = custom_itinerary
            st.session_state.current_step = 5
            message(
                f"{st.session_state.itinerary_preference} 여행 일정을 선호해",
                is_user=True,
            )
            message(
                f"{st.session_state.itinerary_preference} 일정 스타일로 일정을 준비하겠습니다.",
                is_user=False,
            )

    # 숙소 유형 선택
    if st.session_state.itinerary_preference:
        message(
            "어떤 숙소를 원하시나요? 아래에서 선택하거나 직접 입력해주세요.",
            is_user=False,
        )
        accommodations = [
            "공항 근처 숙소",
            "5성급 호텔 이상",
            "수영장이 있는 숙소",
            "게스트 하우스",
            "민박집",
            "전통가옥",
        ]

        for accommodation in accommodations:
            if st.checkbox(
                accommodation,
                key=f"accommodation_{accommodation}",
                disabled=st.session_state.accommodation_type is not None,
            ):
                st.session_state.accommodation_type = accommodation
                st.session_state.current_step = 6
                message(
                    f"{st.session_state.accommodation_type} 스타일의 숙소를 원해",
                    is_user=True,
                )
                message(
                    f"{st.session_state.accommodation_type} 스타일의 숙소로 추천해드리겠습니다.",
                    is_user=False,
                )

        custom_accommodation = st.text_input(
            "다른 숙소 유형을 원하시면 입력해주세요", key="custom_accommodation"
        )
        if custom_accommodation:
            st.session_state.accommodation_type = custom_accommodation
            st.session_state.current_step = 6
            message(
                f"{st.session_state.accommodation_type} 스타일의 숙소를 원해",
                is_user=True,
            )
            message(
                f"{st.session_state.accommodation_type} 스타일의 숙소로 추천해드리겠습니다.",
                is_user=False,
            )

    # 여행 일정 생성 조건: 모든 필수 요소가 선택되었는지 확인
    if (
        st.session_state.destination
        and st.session_state.stay_duration
        and st.session_state.companion
        and st.session_state.travel_style
        and st.session_state.itinerary_preference
        and st.session_state.accommodation_type
    ):
        # itinerary_details = {
        #     "city": st.session_state.get("destination"),
        #     "trip_duration": st.session_state.get("stay_duration"),
        #     "travel_dates": "2024-11-15 ~ 2024-11-18",
        #     "companions": st.session_state.get("companion"),
        #     "travel_style": st.session_state.get("travel_style"),
        #     "itinerary_style": st.session_state.get("itinerary_preference"),
        # }
        # 위 코드는 여행계획 생성 함수에 넣을 변수들을 session에서 불러와서 저장하는 코드
        if not st.session_state.itinerary_generated:
            try:
                with st.spinner("여행 일정을 생성하는 중입니다..."):
                    # itinerary_request는 openai에 보낼 프롬프트를 정리하는 곳.
                    # st.session_state.{}는 사용자가 선택한 값들을 불러오는 것.

                    # 여행 기간을 일 수로 계산, 수정한 부분
                    trip_days = calculate_trip_days(st.session_state.stay_duration)
                    if trip_days is None:
                        trip_days = 2  # 기본값 설정 (예: 2박 3일로 설정)

                    # 여행 일정을 생성하는 프롬프트에서 trip_days를 사용, 수정한 부분
                    itinerary_request = (
                        f"{st.session_state.destination}로 {st.session_state.stay_duration} 동안 "
                        f"{st.session_state.companion}와 함께하는 여행 일정을 만들어 주세요. "
                        f"여행 스타일은 '{st.session_state.travel_style}'을(를) 선호하며, "
                        f"일정 스타일은 '{st.session_state.itinerary_preference}'을(를) 선호하고, "
                        f"숙소는 '{st.session_state.accommodation_type}'을(를) 원합니다. "
                        f"{trip_days}일 동안의 일정을 생성해 주세요. 각 날을 'Day 1:', 'Day 2:' 형식으로 나누고, "
                        "오전 관광지와 아침 식사 장소를, 오후 관광지와 점심 식사 장소를, 저녁 야경 명소와 저녁 식사 장소를 추천해주세요. "
                        "각 문장은 한국어로 자연스럽게 작성해주세요."
                    )
                    # openai에 itinerary_request라는 이름으로 저장된 프롬프트를 보내서 답변을 생성하는 코드.
                    # messages 키 값에 오른쪽과 같이 페르소나를 설정해줄 수 있음. -> {"role": "system", "content": "You are a helpful assistant."}
                    response = openai.chat.completions.create(
                        model="gpt-3.5-turbo",
                        messages=[{"role": "user", "content": itinerary_request}],
                    )
                    # 만약 여행 계획 생성 함수가 있다면 여기에 넣어서 결과를 문자열 형태로 st.session_state.itinerary 변수에 넣어주면 됨.
                    # json 형태로 데이터를 넣어서 st.session_state.itinerary['key'] 이런 식으로 데이터를 뽑아서 사용하면 됨.
                    st.session_state.itinerary = response.choices[0].message.content
                    st.session_state.messages.append(
                        {"role": "assistant", "content": st.session_state.itinerary}
                    )
                    st.session_state.itinerary_generated = True

            except Exception as e:
                st.error(f"여행 일정 생성 중 오류가 발생했습니다: {e}")

    # 기존 메시지 출력
    for msg in st.session_state.messages:
        message(msg["content"], is_user=(msg["role"] == "user"))

    # "처음으로" and "이전으로" buttons
    st.container()
    st.button("처음으로", on_click=reset_conversation)
    st.button("이전으로", on_click=previous_step)

# 오른쪽에 지도 및 일정 표시
with st.container():
    # Google 지도 표시
    if st.session_state.destination:
        st.subheader("🗺️ 여행 지도")
        map_url = f"https://www.google.com/maps/embed/v1/place?key=AIzaSyBW3TJ70cZAU7A48hlbXBIk_YkJHu8nKsg&q={st.session_state.destination}&zoom=12"
        st.markdown(
            f"""
            <iframe width="100%" height="400" frameborder="0" style="border:0" 
            src="{map_url}" allowfullscreen></iframe>
            """,
            unsafe_allow_html=True,
        )
    # 일정 표시
    if st.session_state.itinerary:
        st.subheader("🗺️ 여행 일정")
        itinerary_lines = st.session_state.itinerary.splitlines()
        days = [line for line in itinerary_lines if line.startswith("Day")]

        selected_day_content = ""
        if days:
            # Create columns for day buttons
            button_columns = st.columns(len(days))

            for i, day in enumerate(days):
                with button_columns[i]:
                    if st.button(day.strip(), key=f"button_{i}"):
                        start_index = itinerary_lines.index(day)
                        end_index = (
                            itinerary_lines.index(days[i + 1])
                            if i + 1 < len(days)
                            else len(itinerary_lines)
                        )
                        day_content = itinerary_lines[start_index:end_index]

                        # Separate morning, afternoon, and night activities
                        morning, afternoon, night = [], [], []
                        current_section = None
                        for line in day_content:
                            if "오전" or "아침" in line:
                                current_section = morning
                                line = line.replace("오전", "").strip()
                            elif "오후" in line:
                                current_section = afternoon
                                line = line.replace("오후", "").strip()
                            elif "저녁" in line:
                                current_section = night
                                line = line.replace("저녁", "").strip()
                            if current_section is not None and line:
                                current_section.append(line)

                        # Format each section for display
                        selected_day_content = ""
                        if morning:
                            selected_day_content += (
                                "**오전 일정**" + "<br>".join(morning) + "\n\n"
                            )
                        if afternoon:
                            selected_day_content += (
                                "**오후 일정**" + "<br>".join(afternoon) + "\n\n"
                            )
                        if night:
                            selected_day_content += (
                                "**저녁 일정**" + "<br>".join(night) + "\n\n"
                            )

            # Display the selected day's itinerary
            if selected_day_content:
                st.write("### 선택한 일정")
                st.markdown(
                    selected_day_content.replace("\n", "<br>"), unsafe_allow_html=True
                )
        else:
            st.write("일정에 표시할 날짜가 없습니다. 전체 일정을 확인하세요:")
            st.write(st.session_state.itinerary)

    # 숙소 추천
    if st.session_state.accommodation_type and st.session_state.destination:
        st.subheader("🛏️ 추천 숙소")

        # Example accommodations based on selected destination and accommodation type
        # 숙소 추천 프롬프트 결과 예시
        # 숙소 추천 생성 함수가 있다면 accomodations_data = accomdation_recommendation() 이런식으로 불러오면 됨
        accommodations_data = {
            "오사카": {
                "공항 근처 숙소": [
                    {
                        "name": "오사카 공항 호텔",
                        "rating": "4.2",
                        "reviews": "(1,234)",
                        "price": "₩150,000",
                    },
                    {
                        "name": "칸사이 공항 인",
                        "rating": "4.5",
                        "reviews": "(2,567)",
                        "price": "₩180,000",
                    },
                    {
                        "name": "오사카 에어포트 리조트",
                        "rating": "4.3",
                        "reviews": "(890)",
                        "price": "₩200,000",
                    },
                ],
                "수영장이 있는 숙소": [
                    {
                        "name": "오사카 수영장 호텔",
                        "rating": "4.8",
                        "reviews": "(1,102)",
                        "price": "₩250,000",
                    },
                    {
                        "name": "오사카 워터파크 리조트",
                        "rating": "4.6",
                        "reviews": "(2,001)",
                        "price": "₩300,000",
                    },
                    {
                        "name": "스파 앤 리조트",
                        "rating": "4.7",
                        "reviews": "(1,450)",
                        "price": "₩280,000",
                    },
                ],
                # 오사카에 맞는 숙소를 추가
            },
            "파리": {
                "5성급 호텔 이상": [
                    {
                        "name": "파리 리츠 호텔",
                        "rating": "4.9",
                        "reviews": "(3,240)",
                        "price": "₩700,000",
                    },
                    {
                        "name": "파리 프라자 호텔",
                        "rating": "4.8",
                        "reviews": "(1,920)",
                        "price": "₩650,000",
                    },
                    {
                        "name": "호텔 드 파리",
                        "rating": "4.7",
                        "reviews": "(1,700)",
                        "price": "₩600,000",
                    },
                ],
                "게스트 하우스": [
                    {
                        "name": "파리 게스트 하우스",
                        "rating": "4.3",
                        "reviews": "(900)",
                        "price": "₩100,000",
                    },
                    {
                        "name": "몽마르트 게스트 홈",
                        "rating": "4.5",
                        "reviews": "(750)",
                        "price": "₩120,000",
                    },
                    {
                        "name": "세느 게스트 하우스",
                        "rating": "4.4",
                        "reviews": "(680)",
                        "price": "₩110,000",
                    },
                ],
                # 파리에 맞는 숙소를 추가
            },
            # 뉴욕과 방콕도 각 항목에 맞는 숙소를 추가
        }

        # Get recommended accommodations for the selected city and accommodation type
        city_accommodations = accommodations_data.get(st.session_state.destination, {})
        recommended_accommodations = city_accommodations.get(
            st.session_state.accommodation_type, []
        )

        # Display the top 3 recommendations
        for accommodation in recommended_accommodations[:3]:
            st.write(f"**{accommodation['name']}**")
            st.write(f"평점: ⭐ {accommodation['rating']} {accommodation['reviews']}")
            st.write(f"가격: {accommodation['price']}")
            st.markdown("---")

        # Fallback message if no accommodations are found for the selected type
        if not recommended_accommodations:
            st.write("선택한 여행지와 숙소 유형에 맞는 추천 숙소가 없습니다.")
