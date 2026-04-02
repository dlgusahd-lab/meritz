import streamlit as st
import pdfplumber
import re

# 1. 페이지 설정
st.set_page_config(page_title="핵심담보 정리 요약서", layout="wide")

# 디자인 CSS
st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Noto+Sans+KR:wght@400;700&display=swap');
    * { font-family: 'Noto Sans KR', sans-serif; }
    body, .stApp { background-color: white !important; }
    .meritz-header { background-color: #E30613; padding: 18px; border-radius: 10px; color: white; text-align: center; margin-bottom: 15px; }
    .main-title { font-size: 30px; font-weight: 700; }
    .box-container { border: 2.5px solid #E30613; padding: 15px; border-radius: 15px; background-color: #fff; min-height: 580px; margin-bottom: 15px; }
    .section-title { font-size: 22px; font-weight: 700; color: #E30613; border-bottom: 3px solid #E30613; padding-bottom: 8px; margin-bottom: 12px; }
    .row { display: flex; justify-content: space-between; margin-bottom: 8px; font-size: 16px; border-bottom: 1.5px solid #f2f2f2; padding-bottom: 6px; align-items: flex-start; }
    .price { font-weight: 700; color: #333; text-align: right; min-width: 90px; }
    .sub-row { display: flex; justify-content: space-between; margin-left: 20px; color: #E30613; font-size: 14px; font-weight: 600; margin-top: -8px; margin-bottom: 10px; }
    .sub-price { text-align: right; }
    .jong-area { background: #fdf2f2; padding: 10px; border-radius: 8px; margin-bottom: 10px; border: 1.5px solid #ffcccc; }
    .jong-label { font-weight: bold; color: #E30613; font-size: 15px; margin-bottom: 6px; text-align: center; }
    .jong-grid { display: flex; justify-content: space-around; font-size: 15px; font-weight: 700; color: #444; }
    
    .stTextInput > div > div > input { border: 1px solid #E30613; font-weight: bold; }

    @media print {
        @page { size: A4; margin: 8mm; }
        .no-print, .stFileUploader, header, [data-testid="stSidebar"], .stTextInput { display: none !important; }
        .box-container { border: 2.5px solid #E30613 !important; page-break-inside: avoid; min-height: auto !important; }
    }
    </style>
    """, unsafe_allow_html=True)

st.markdown('<div class="meritz-header"><span class="main-title">핵심담보 정리 요약서</span></div>', unsafe_allow_html=True)

# 사이드바 설정
st.sidebar.header("📝 수기 입력 담보")
manual_cancer_val = st.sidebar.text_input("26종 항암금액 (숫자만 입력)", "")

uploaded_file = st.file_uploader("PDF 제안서를 업로드하세요", type="pdf")

if uploaded_file is not None:
    diag_main = {}
    sub_vals = {"암통치": "-", "뇌혈관혈전": "-", "허혈성혈전": "-"}
    surg_list = []
    cancer_treat, circ_treat = {}, {}
    s_jong, j_jong = ["-"]*5, ["-"]*5

    exclude_keywords = ["골절", "화상", "충수", "깁스", "응급실", "상해사망", "질병사망", "중환자실"]

    with pdfplumber.open(uploaded_file) as pdf:
        for page in pdf.pages:
            tables = page.extract_table()
            if not tables: continue
            for row in tables:
                if not row or len(row) < 3 or not row[1]: continue
                
                raw_name = row[1].replace("\n", "").strip()
                price = row[2].replace("\n", "").strip() if row[2] else ""
                clean_name = re.sub(r'^\d+\s*', '', raw_name).replace("(통합간편가입)", "").strip()

                # --- 1. 진단비 ---
                if "암종별(30종)통합암진단비(전이포함)" in raw_name:
                    val = price.replace("원", "").replace("만원", "").replace("만", "").replace(",", "").strip()
                    diag_main["30종통합암"] = f"항목별 {val}만원"
                elif "암진단비(유사암제외)" in clean_name: diag_main["암 진단비"] = price
                elif "유사암진단비" in clean_name: diag_main["유사암 진단비"] = price
                elif "뇌혈관질환진단비" in clean_name: diag_main["뇌혈관질환 진단비"] = price
                elif "허혈성심장질환진단비" in clean_name: diag_main["허혈성심장 진단비"] = price

                # --- 2. ㄴ 세부 항목 ---
                if "암 통합치료비Ⅲ" in clean_name and "비급여" in clean_name: sub_vals["암통치"] = price
                elif "뇌혈관질환 특정혈전치료비" in clean_name: sub_vals["뇌혈관혈전"] = price
                elif "허혈성심장질환 특정혈전치료비" in clean_name: sub_vals["허혈성혈전"] = price
                
                # --- 3. 수술비 ---
                if "수술비" in clean_name:
                    if any(kw in clean_name for kw in exclude_keywords): continue
                    match_jong = re.search(r'([상질])해?.*?(\d)종', clean_name)
                    if match_jong:
                        idx = int(match_jong.group(2)) - 1
                        val = price.replace("원", "").replace("만원", "").replace("만", "").replace(",", "").strip()
                        if match_jong.group(1) == "상": s_jong[idx] = val + "만"
                        else: j_jong[idx] = val + "만"
                    else:
                        match_n = re.search(r'(\d+대)\s*질병수술비', clean_name)
                        if match_n:
                            n_title = f"{match_n.group(1)} 질병수술비"
                            if not any(n_title in x[0] for x in surg_list):
                                surg_list.append((n_title, "세부항목 참고"))
                        else:
                            surg_list.append((clean_name, price))

                # --- 4. 암 치료비 ---
                if any(x in clean_name for x in ["암통치", "암 통합치료비", "표적", "중입자"]):
                    if "암 통합치료비(기본형)" in raw_name: cancer_treat["암 통합치료비(기본형)"] = "4천만원"
                    elif any(x in clean_name for x in ["표적항암", "중입자", "양성자"]): cancer_treat["중입자/표적"] = price
                    elif "비급여" in clean_name: cancer_treat["비통치(비급여)"] = price

                # --- 5. 순환계 치료비 ---
                if any(x in clean_name for x in ["순환계", "혈전용해", "카테터"]):
                    circ_treat[clean_name] = price

    # --- 화면 출력 ---
    c1, c2 = st.columns(2); c3, c4 = st.columns(2)
    with c1:
        content = '<div class="box-container"><p class="section-title">🔴 주요 진단비</p>'
        for k in ["암 진단비", "유사암 진단비", "30종통합암", "뇌혈관질환 진단비", "허혈성심장 진단비"]:
            if k in diag_main:
                content += f'<div class="row"><span>{k}</span><span class="price">{diag_main[k]}</span></div>'
                if k in ["암 진단비", "30종통합암"]:
                    content += f'<div class="sub-row"><span>ㄴ 암 통합치료비Ⅲ(비급여)</span><span class="sub-price">{sub_vals["암통치"]}</span></div>'
                elif k == "뇌혈관질환 진단비":
                    content += f'<div class="sub-row"><span>ㄴ 뇌혈관질환 특정혈전치료비</span><span class="sub-price">{sub_vals["뇌혈관혈전"]}</span></div>'
                elif k == "허혈성심장 진단비":
                    content += f'<div class="sub-row"><span>ㄴ 허혈성심장 특정혈전치료비</span><span class="sub-price">{sub_vals["허혈성혈전"]}</span></div>'
        content += '</div>'
        st.markdown(content, unsafe_allow_html=True)

    with c2:
        content = '<div class="box-container"><p class="section-title">🔵 수술비 보장</p>'
        content += f'<div class="jong-area"><div class="jong-label">상해 종수술비 (1-5종)</div><div class="jong-grid">' + "".join([f"<span>{i+1}종:{s_jong[i]}</span>" for i in range(5)]) + '</div></div>'
        content += f'<div class="jong-area"><div class="jong-label">질병 종수술비 (1-5종)</div><div class="jong-grid">' + "".join([f"<span>{i+1}종:{j_jong[i]}</span>" for i in range(5)]) + '</div></div>'
        for name, p in surg_list: content += f'<div class="row"><span>{name}</span><span class="price">{p}</span></div>'
        content += '</div>'
        st.markdown(content, unsafe_allow_html=True)

    with c3:
        content = '<div class="box-container"><p class="section-title">⭐ 암 치료비</p>'
        # 지점장님 요청사항: '가입금액' 빼고 숫자만!
        display_val = f"{manual_cancer_val}만원" if manual_cancer_val else "-"
        content += f'<div class="row"><span>26종 항암치료비(전이암포함)</span><span class="price">{display_val}</span></div>'
        for k, v in cancer_treat.items(): content += f'<div class="row"><span>{k}</span><span class="price">{v}</span></div>'
        content += '</div>'
        st.markdown(content, unsafe_allow_html=True)

    with c4:
        content = '<div class="box-container"><p class="section-title">🟣 순환계 치료비</p>'
        for k, v in circ_treat.items(): content += f'<div class="row"><span>{k}</span><span class="price">{v}</span></div>'
        content += '</div>'
        st.markdown(content, unsafe_allow_html=True)