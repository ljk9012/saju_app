import streamlit as st
import datetime
import hashlib
from sajupy import calculate_saju
from korean_lunar_calendar import KoreanLunarCalendar

# ==========================================
# 1. 텍스트 직접 입력 처리 및 진태양시 보정 엔진
# ==========================================
def parse_date_input(date_str):
    try:
        date_str = date_str.replace(" ", "").replace("-", "").replace(".", "")
        if len(date_str) == 8:
            return datetime.date(int(date_str[:4]), int(date_str[4:6]), int(date_str[6:8]))
    except: pass
    return None

def parse_time_input(time_str):
    try:
        time_str = time_str.replace(" ", "").replace(":", "")
        if len(time_str) in [3, 4]:
            h = int(time_str[:-2])
            m = int(time_str[-2:])
            if 0 <= h <= 23 and 0 <= m <= 59:
                return datetime.time(h, m)
    except: pass
    return None

# 지역별 경도에 따른 표준시(135도) 대비 시간 보정값
region_offsets = {
    "천안 (경도 127.1도 / -32분)": -32,
    "서울 (경도 127.0도 / -32분)": -32,
    "인천 (경도 126.7도 / -33분)": -33,
    "강릉 (경도 128.9도 / -24분)": -24,
    "대전 (경도 127.4도 / -30분)": -30,
    "광주 (경도 126.8도 / -33분)": -33,
    "대구 (경도 128.6도 / -26분)": -26,
    "부산 (경도 129.0도 / -24분)": -24,
    "제주 (경도 126.5도 / -34분)": -34,
    "표준시 (보정 안 함)": 0
}

def apply_true_solar_time(parsed_date, parsed_time, offset_minutes):
    """입력된 시간에 지역별 경도 시차를 더하거나 빼서 실제 태양시를 구하는 함수"""
    dt = datetime.datetime.combine(parsed_date, parsed_time)
    corrected_dt = dt + datetime.timedelta(minutes=offset_minutes)
    return corrected_dt.date(), corrected_dt.time()

# ==========================================
# 2. 사주 기초 및 오행 계산 엔진
# ==========================================
hanja_to_hangul = {"甲":"갑", "乙":"을", "丙":"병", "丁":"정", "戊":"무", "己":"기", "庚":"경", "辛":"신", "壬":"임", "癸":"계", 
                   "子":"자", "丑":"축", "寅":"인", "卯":"묘", "辰":"진", "巳":"사", "午":"오", "未":"미", "申":"신", "酉":"유", "戌":"술", "亥":"해"}

ohaeng_simple = {"갑":"목", "을":"목", "인":"목", "묘":"목", "병":"화", "정":"화", "사":"화", "오":"화", 
                 "무":"토", "기":"토", "진":"토", "술":"토", "축":"토", "미":"토", "경":"금", "신":"금", "유":"금", "임":"수", "계":"수", "해":"수", "자":"수"}

def analyze_ohaeng(saju_kor):
    chars = [saju_kor.get('year_stem',''), saju_kor.get('year_branch',''),
             saju_kor.get('month_stem',''), saju_kor.get('month_branch',''),
             saju_kor.get('day_stem',''), saju_kor.get('day_branch',''),
             saju_kor.get('hour_stem',''), saju_kor.get('hour_branch','')]
    
    count = {"목":0, "화":0, "토":0, "금":0, "수":0}
    for c in chars:
        if c in ohaeng_simple: count[ohaeng_simple[c]] += 1
        
    strongest = max(count, key=count.get)
    weakest = min(count, key=count.get)
    return count, strongest, weakest

# ==========================================
# 3. 방대한 사주 해석 데이터베이스
# ==========================================
saju_deep_analysis = {
    "목": {
        "nature": "봄에 피어나는 싹처럼 시작하고 뻗어나가는 기운이 강합니다. 외향적이고 호기심이 많으며, 새로운 일을 기획하고 추진할 때 가장 큰 보람을 느낍니다. 다만 마무리가 약할 수 있으니 끈기를 보완하면 완벽합니다.",
        "relation": "사람들에게 먼저 다가가고 베푸는 역할을 좋아합니다. 답답하고 통제받는 환경보다는, 자율성을 존중해주는 사람(특히 남편)과 있을 때 가장 편안함을 느낍니다.",
        "career": "교육, 기획, 디자인, 스타트업, 창작 등 무에서 유를 창조하거나 사람을 성장시키는 분야가 천직입니다."
    },
    "화": {
        "nature": "여름의 태양이나 불꽃처럼 열정적이고 자신감이 넘칩니다. 감정 표현이 솔직하고 화끈하며, 남들의 주목을 받고 성과를 인정받을 때 에너지가 솟아납니다. 스트레스는 땀을 흘리는 운동으로 풀어야 제맛입니다.",
        "relation": "숨기는 것이 없고 뒤끝이 없어 인간관계가 시원시원합니다. 가식적인 사람을 가장 싫어하며, 솔직하게 소통하는 부부 관계에서 큰 안정감을 얻습니다.",
        "career": "방송, 예술, 마케팅, IT, 말하는 직업 등 자신을 드러내고 에너지를 발산하는 역동적인 분야가 잘 맞습니다."
    },
    "토": {
        "nature": "계절을 이어주는 넓은 대지처럼 포용력과 안정감이 탁월합니다. 내향적이고 신중하며, 주변 사람들의 이야기를 들어주고 중재할 때 보람을 느낍니다. 변화보다는 안정을 추구하는 듬직한 성향입니다.",
        "relation": "가족과 친구들에게 든든한 피난처 같은 존재입니다. 섣불리 남을 판단하지 않으며, 묵묵히 곁을 지켜주는 남편의 사랑을 받을 때 평온함을 느낍니다.",
        "career": "부동산, 금융, 행정, 상담, 복지 등 사람들에게 안정감을 주고 신뢰를 바탕으로 하는 분야에서 크게 성공합니다."
    },
    "금": {
        "nature": "가을의 서리처럼 예리하고 결단력이 있습니다. 원리원칙을 중시하고 맺고 끊음이 확실합니다. 깔끔하게 정리된 환경과 완벽하게 마무리된 결과물을 볼 때 큰 희열을 느낍니다. 예민함을 무기로 씁니다.",
        "relation": "친해지기까지 시간이 걸리지만, 한 번 내 사람이라 생각하면 끝까지 의리를 지킵니다. 공과 사가 뚜렷하며, 약속을 잘 지키는 사람과 찰떡궁합입니다.",
        "career": "법률, 의료, 회계, IT개발, 세밀한 기술 등 날카로운 분석력과 정확성이 요구되는 전문직에서 크게 빛을 봅니다."
    },
    "수": {
        "nature": "겨울의 깊은 물처럼 지혜롭고 속이 깊습니다. 상상력이 풍부하고 직관력이 뛰어나며, 혼자만의 시간을 가지며 사색할 때 가장 큰 에너지를 충전합니다. 환경에 유연하게 적응하는 생존력 끝판왕입니다.",
        "relation": "어떤 사람과도 물 흐르듯 유연하게 맞춰주는 능력이 있습니다. 하지만 내면을 다 보여주지 않아 신비로우며, 자신의 지적 깊이를 이해해주는 대화가 통하는 남편을 가장 사랑합니다.",
        "career": "외교, 무역, 철학, 심리, 연구, 예술 등 고도의 지적 능력과 유연성, 창의력을 발휘하는 지식 기반 분야가 천직입니다."
    }
}

# ==========================================
# 4. 무한 조합 운세 생성기
# ==========================================
def generate_dynamic_fortunes(saju_str, today):
    prefixes = ["오늘은 우주의 맑은 기운이 당신을 돕는 날입니다.", "마음속 깊은 곳에서 새로운 영감이 떠오르는 하루입니다.", "남편의 사랑이 당신의 주변을 따뜻하게 감싸는 날이군요.", "가만히 있어도 당신의 매력이 은은하게 퍼져나가는 기분 좋은 날입니다.", "평소보다 두뇌 회전이 빠르고 판단력이 예리해지는 하루입니다."]
    actions = ["평소 미뤄두었던 일을 시작해보세요.", "남편과 짧은 산책이나 따뜻한 차 한 잔을 나누어보세요.", "온전히 나만을 위한 휴식 시간을 10분이라도 가져보세요.", "마음속에 품고 있던 작은 소망을 실행으로 옮겨보세요.", "오늘은 조금 더 자신을 칭찬하고 아껴주세요."]
    results = ["뜻밖의 재물운이 상승할 것입니다.", "그동안 쌓였던 스트레스가 눈 녹듯 사라질 것입니다.", "놀라운 집중력으로 큰 성과를 거두게 될 것입니다.", "가정 내에 웃음꽃이 피고 부부 애정운이 최고조에 달합니다.", "잊고 있던 귀인이 나타나 당신에게 큰 도움을 줄 것입니다."]
    
    h1 = int(hashlib.md5(f"{saju_str}_{today}_1".encode()).hexdigest(), 16) % len(prefixes)
    h2 = int(hashlib.md5(f"{saju_str}_{today}_2".encode()).hexdigest(), 16) % len(actions)
    h3 = int(hashlib.md5(f"{saju_str}_{today}_3".encode()).hexdigest(), 16) % len(results)
    
    daily = f"{prefixes[h1]} {actions[h2]} 그러면 {results[h3]}"
    
    year_energy = ["올해는 당신의 내실을 다지고 뿌리를 깊게 내리는 '겨울'과 같은 시기입니다. 억지로 무언가를 추진하기보다, 배움과 가족의 안정을 최우선으로 하세요.",
                   "올해는 당신의 능력이 꽃피우는 역동적인 '봄'의 시기입니다. 그동안 주저했던 일이 있다면 과감하게 도전해 보세요. 결과가 좋습니다.",
                   "올해는 주변 사람들과의 관계가 대폭 넓어지고 재물이 모이는 '가을'의 결실기입니다. 남편과의 관계도 더욱 끈끈해지며, 투자나 재테크에서 빛을 봅니다."]
    yearly = year_energy[int(hashlib.md5(f"{saju_str}_{today.year}".encode()).hexdigest(), 16) % 3]

    return daily, yearly

# ==========================================
# 5. 완벽한 자미두수 명반(도표) 알고리즘
# ==========================================
def calculate_jamidusu(solar_date, birth_time):
    cal = KoreanLunarCalendar()
    cal.setSolarDate(solar_date.year, solar_date.month, solar_date.day)
    lunar_m = cal.lunarMonth
    
    h = birth_time.hour
    t_idx = ((h + 1) // 2) % 12 + 1
    
    ming_idx = (3 + lunar_m - t_idx) % 12
    if ming_idx <= 0: ming_idx += 12
    
    palace_names = ["명궁(나의 본질)", "형제궁(가족/동료)", "부처궁(배우자)", "자녀궁(자녀/후배)", 
                    "재백궁(재물)", "질액궁(건강)", "천이궁(이동/사회)", "노복궁(대인관계)", 
                    "관록궁(직업/명예)", "전택궁(부동산)", "복덕궁(정신/수명)", "부모궁(부모/상사)"]
    
    branches = ["", "자", "축", "인", "묘", "진", "사", "오", "미", "신", "유", "술", "해"]
    
    chart_data = {}
    current_idx = ming_idx
    for p_name in palace_names:
        chart_data[branches[current_idx]] = p_name
        current_idx -= 1
        if current_idx == 0: current_idx = 12

    return branches[ming_idx], chart_data

jami_5_analysis = {
    "기질 및 성격": "명궁(命宮)의 위치를 보았을 때, 당신은 겉으로는 부드럽고 유연하게 상황을 맞춰가지만 내면에는 절대 꺾이지 않는 강인한 심지를 지녔습니다. 타인의 감정을 읽는 능력이 탁월해 사회적 가면을 쓰는 데도 능숙하지만, 혼자 있을 때는 본연의 섬세하고 자유로운 영혼으로 돌아옵니다.",
    "사회적 성취": "재백궁(財帛宮)과 관록궁(官祿宮)의 조화를 보면, 당신은 땀 흘리는 육체 노동보다는 '지식, 정보, 아이디어, 인간관계'를 활용해 재물을 얻는 구조입니다. 남편의 지지나 조력이 합쳐질 때 사회적 명예와 부가 두 배로 증폭되는 운명을 타고났습니다.",
    "인간관계": "부처궁(夫妻宮)의 기운이 매우 맑습니다. 당신의 남편은 당신 인생의 가장 큰 귀인이자 조력자입니다. 때론 사소한 의견 충돌이 있더라도 결국 남편의 넓은 포용력 안에서 평온을 찾게 되며, 자녀에게는 지혜롭고 자상한 어머니가 됩니다.",
    "환경적 요소": "천이궁(遷移宮)과 질액궁(疾厄宮)을 볼 때, 한곳에 꽉 막혀 있기보다는 가벼운 여행이나 이사, 인테리어 변경 등 환경에 변화를 줄 때 행운이 들어옵니다. 위장과 신경성 스트레스를 조심하고, 따뜻한 물과 차를 자주 마시는 것이 생명력을 올립니다.",
    "시기별 운세": "10년 단위의 대운 흐름을 보면, 30대 중반부터 40대 후반까지 인생의 황금기(재물과 안정이 동시에 이루어지는 시기)가 펼쳐집니다. 현재는 그 황금기로 향하는 도약의 시기이므로 조급해하지 말고 남편과 즐겁게 현재를 누리세요."
}

# ==========================================
# 앱 화면 구성 (UI)
# ==========================================
st.set_page_config(page_title="아내 전용 운명 분석기", page_icon="🔮", layout="wide")

# CSS 스타일 (들여쓰기 완전 제거)
st.markdown("""
<style>
.big-font {font-size:30px !important; font-weight: bold; color: #ff4b4b;}
.box {border: 2px solid #ddd; padding: 10px; border-radius: 10px; text-align: center; height: 100%; display: flex; flex-direction: column; justify-content: center; background-color: #ffffff;}
.palace-title {font-weight: bold; color: #1f77b4; font-size: 14px; margin-top: 5px;}
.palace-branch {font-size: 22px; font-weight: bold; color: #333;}
</style>
""", unsafe_allow_html=True)

st.markdown('<p class="big-font">💖 세상에서 가장 사랑하는 아내를 위한 완벽 운명 분석기 💖</p>', unsafe_allow_html=True)
st.write("남편이 밤을 새워 코딩하고, 진태양시 보정 알고리즘까지 완벽하게 적용한 오직 당신만을 위한 프라이빗 웹앱입니다.")
st.write("---")

col1, col2, col3 = st.columns(3)
with col1:
    b_date_str = st.text_input("생년월일 8자리 입력 (예: 19890202)", "19890202")
with col2:
    b_time_str = st.text_input("태어난 시간 4자리 입력 (예: 2122)", "2122")
with col3:
    birth_region = st.selectbox("태어난 지역 (진태양시 보정용)", list(region_offsets.keys()))

parsed_date = parse_date_input(b_date_str)
parsed_time = parse_time_input(b_time_str)

if st.button("내 운명의 모든 것 분석하기", use_container_width=True):
    if parsed_date is None or parsed_time is None:
        st.error("입력 형식이 잘못되었습니다. 숫자만 정확히 타이핑해주세요! (예: 19890202 / 2122)")
    else:
        with st.spinner("우주의 기운을 모아 아내의 명반과 사주를 도출하고 있습니다..."):
            
            offset = region_offsets[birth_region]
            corr_date, corr_time = apply_true_solar_time(parsed_date, parsed_time, offset)
            
            st.info(f"🕰️ **진태양시 보정 완료:** 입력하신 시계 시간 **{parsed_time.strftime('%H:%M')}**에서 **{offset}분**을 보정하여, 실제 태양의 위치인 **{corr_time.strftime('%H:%M')}**을 기준으로 사주와 명반을 정확하게 도출했습니다.")
            
            saju_res = calculate_saju(corr_date.year, corr_date.month, corr_date.day, corr_time.hour, corr_time.minute, "Seoul", False)
            saju_kor = {k: "".join([hanja_to_hangul.get(c, c) for c in v]) if isinstance(v, str) else v for k, v in saju_res.items()}
            
            ohaeng_count, ohaeng_strong, ohaeng_weak = analyze_ohaeng(saju_kor)
            daily_fortune, yearly_fortune = generate_dynamic_fortunes(saju_kor.get('day_pillar',''), datetime.date.today())
            ming_gong, chart_data = calculate_jamidusu(corr_date, corr_time)

            st.success("천문 역법 계산 및 수만 가지 데이터 조합 분석이 완료되었습니다!")
            st.write("---")

            tab1, tab2, tab3 = st.tabs(["🔮 사주 정밀 분석", "🌌 자미두수 명반 및 5대 기질", "🌟 흐름 및 시기별 운세"])

            with tab1:
                st.header("🔮 당신의 타고난 사주 원국과 본질")
                
                c1, c2, c3, c4 = st.columns(4)
                with c1: st.error(f"**시주** (노년/자식)\n### {saju_kor.get('hour_pillar', '')}")
                with c2: st.success(f"**일주(나)**\n### {saju_kor.get('day_pillar', '')}")
                with c3: st.info(f"**월주** (청년/사회)\n### {saju_kor.get('month_pillar', '')}")
                with c4: st.warning(f"**년주** (초년/조상)\n### {saju_kor.get('year_pillar', '')}")
                
                st.markdown("### 1. 타고난 성향과 기질 (오행 분석)")
                st.write(f"- 당신의 사주에는 **{ohaeng_strong}** 기운이 가장 강하게 발현되어 있으며, 상대적으로 **{ohaeng_weak}** 기운이 부족합니다.")
                st.write(f"- **성격적 강점:** {saju_deep_analysis[ohaeng_strong.split('(')[0]]['nature']}")
                
                st.markdown("### 2. 관계의 역학")
                st.write(f"- **인간관계 특징:** {saju_deep_analysis[ohaeng_strong.split('(')[0]]['relation']}")
                
                st.markdown("### 3. 생애 특성 (적성과 직업운)")
                st.write(f"- **천직 및 발현 분야:** {saju_deep_analysis[ohaeng_strong.split('(')[0]]['career']}")

            with tab2:
                st.header("🌌 자미두수 12궁 명반 (운명의 지도)")
                st.write("아래 표는 하늘의 별자리를 당신이 태어난 시간의 12방위에 매칭한 '명반(그림 도표)'입니다.")
                
                def get_box(branch):
                    return f"<div class='box'><div class='palace-branch'>{branch}</div><div class='palace-title'>{chart_data[branch]}</div></div>"

                # 주의: 이 아래의 HTML 코드 블록은 들여쓰기가 전혀 없어야 완벽한 그림으로 출력됩니다!
                html_grid = f"""
<div style="display: grid; grid-template-columns: repeat(4, 1fr); grid-auto-rows: minmax(100px, auto); gap: 10px; margin-bottom: 30px; background-color: #f9f9f9; padding: 15px; border-radius: 10px;">
<div style="grid-column: 1; grid-row: 1;">{get_box('사')}</div>
<div style="grid-column: 2; grid-row: 1;">{get_box('오')}</div>
<div style="grid-column: 3; grid-row: 1;">{get_box('미')}</div>
<div style="grid-column: 4; grid-row: 1;">{get_box('신')}</div>
<div style="grid-column: 1; grid-row: 2;">{get_box('진')}</div>
<div style="grid-column: 4; grid-row: 2;">{get_box('유')}</div>
<div style="grid-column: 1; grid-row: 3;">{get_box('묘')}</div>
<div style="grid-column: 4; grid-row: 3;">{get_box('술')}</div>
<div style="grid-column: 1; grid-row: 4;">{get_box('인')}</div>
<div style="grid-column: 2; grid-row: 4;">{get_box('축')}</div>
<div style="grid-column: 3; grid-row: 4;">{get_box('자')}</div>
<div style="grid-column: 4; grid-row: 4;">{get_box('해')}</div>
<div style="grid-column: 2 / 4; grid-row: 2 / 4; display: flex; flex-direction: column; align-items: center; justify-content: center; background-color: #fff4f4; border: 2px dashed #ff4b4b; border-radius: 10px; padding: 20px;">
<span style="font-size: 16px; color: #555;">아내의 영혼이 머무는 곳</span>
<span style="font-size: 28px; font-weight: bold; color: #ff4b4b; margin-top: 5px;">당신의 명궁: {ming_gong} 궁</span>
</div>
</div>
"""
                st.markdown(html_grid, unsafe_allow_html=True)
                
                st.write("---")
                st.subheader("🌠 자미두수 5대 심층 분석")
                for title, desc in jami_5_analysis.items():
                    st.markdown(f"**[{title}]**")
                    st.write(desc)
                    st.write("")

            with tab3:
                st.header("🌟 삶의 단계별 흐름 (알고리즘 분석)")
                
                st.info(f"**[오늘의 운세 - {datetime.date.today().strftime('%Y년 %m월 %d일')}]**\n\n{daily_fortune}")
                
                st.warning(f"**[세운: 올해의 에너지 흐름]**\n\n{yearly_fortune}")
                
                st.success("**[대운: 10년 단위 인생의 큰 흐름]**\n\n대운은 10년마다 바뀌는 인생의 계절입니다. 당신은 현재 이 계절의 중반을 지나고 있으며, 내실을 다져온 경험들이 곧 큰 수확으로 돌아오는 시기에 진입하고 있습니다. 남편과 함께 그 과실을 여유롭게 수확할 준비를 하세요.")