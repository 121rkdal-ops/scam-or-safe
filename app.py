import streamlit as st
import sqlite3
import os
import re
import uuid
from datetime import datetime, timezone
from pathlib import Path

st.set_page_config(page_title="SCAM OR SAFE? | 금융사기 대응력", page_icon="🛡️", layout="centered")
st.markdown("""<style>.block-container{max-width:850px;padding-top:2rem}.stButton button{border-radius:12px}h1{letter-spacing:-1px}</style>""",unsafe_allow_html=True)

QUESTIONS = [{'topic': '실제 대출 상담 이후의 연락',
  'level': '중상',
  'points': 10,
  'scene': '최근 은행 앱에서 대환대출 한도를 조회했습니다. 다음 날 상담원이 연락해 기존 대출 잔액과 만기일을 정확히 말하고, 대환 실행을 위해 기존 대출금을 먼저 상환하라고 '
           '안내합니다. 상담원은 은행명과 비슷한 명의의 계좌번호를 보냈습니다. 이때 가장 결정적인 확인 절차는 무엇입니까?',
  'options': ['공시된 대환 금리와 안내 금리를 대조합니다.',
              '기존 금융회사에서 상환 계좌를 조회합니다.',
              '상담 기록에 남은 승인번호를 확인합니다.',
              '신규 금융회사의 대출 약정을 조회합니다.'],
  'answer': 1,
  'why': '대출 잔액·만기일 등은 유출된 개인정보와 결합될 수 있습니다. 제시된 상환 계좌의 진위는 기존 금융회사의 독립적인 공식 경로에서 확인해야 합니다. 상담원이 지정한 제3자 '
         '계좌로의 상환 요구는 강한 사기 신호입니다.',
  'source': ('금융위원회, 개인정보 유출 관련 소비자경보 (2026.10.06) · 링크 및 문서명 재확인 필요',
             'https://www.fsc.go.kr/no010101/87882'),
  'category': '거래 검증'},
 {'topic': '정상 거래처럼 보이는 카드 알림',
  'level': '중상',
  'points': 10,
  'scene': '기존 카드사 문자 대화방에 해외 승인 알림이 도착했습니다. 문자에는 본인이 사용하지 않은 결제 금액, 승인 시각, 고객센터 번호가 있습니다. 현재 카드사 앱의 알림은 아직 '
           '확인하지 않았습니다. 가장 적절한 다음 행동은 무엇입니까?',
  'options': ['문자에 표시된 번호로 승인 취소를 요청합니다.',
              '기존 문자 대화방의 발신 이력을 비교합니다.',
              '카드사 앱에서 실제 승인 내역을 조회합니다.',
              '해외 이용 알림 설정을 먼저 변경합니다.'],
  'answer': 2,
  'why': '문자 대화방과 발신번호 표시는 발신자 진위를 보장하지 않습니다. 문자에 포함된 연락처나 링크를 이용하지 말고 독립적인 공식 채널에서 승인 여부를 확인해야 합니다.',
  'source': ('금융위원회, 보이스피싱 피해예방 10계명 (2026.02.10) · 링크 및 문서명 재확인 필요', 'https://www.fsc.go.kr/no010101/86250'),
  'category': '신원 검증'},
 {'topic': 'AI 가족 사칭과 비밀 질문',
  'level': '상',
  'points': 12,
  'scene': '가족의 목소리로 사고 합의금이 급하다는 전화가 왔습니다. 상대방은 최근 가족 여행지와 평소 가족끼리 사용하는 비밀 질문의 답까지 알고 있습니다. 그러나 가족 본인의 기존 '
           '휴대전화에는 연락이 닿지 않습니다. 가장 합리적인 판단은 무엇입니까?',
  'options': ['수령 계좌의 예금주가 가족인지 확인합니다.',
              '가족의 다른 연락 경로로 상황을 확인합니다.',
              '사고 접수번호와 담당자를 먼저 확인합니다.',
              '가족에게 최근 일정의 세부사항을 묻습니다.'],
  'answer': 1,
  'why': 'AI 음성 사칭과 개인정보 노출 가능성을 함께 고려해야 합니다. 비밀 질문이나 최근 일정은 유출될 수 있으므로 신뢰할 수 있는 다른 경로로 사실관계를 확인해야 합니다.',
  'source': ('금융위원회, 보이스피싱 피해예방 10계명 (2026.02.10) · 링크 및 문서명 재확인 필요', 'https://www.fsc.go.kr/no010101/86250'),
  'category': '신원 검증'},
 {'topic': '개인정보 노출 이후의 우선 조치',
  'level': '상',
  'points': 12,
  'scene': '신분증 사진과 계좌번호를 금융회사 사칭 상담원에게 전송했습니다. 금전 이체는 하지 않았지만 상대방이 비대면 대출을 신청했을 가능성이 우려됩니다. 다음 중 가장 적절한 조치는 '
           '무엇입니까?',
  'options': ['금융회사에 노출 사실과 차단 조치를 문의합니다.',
              '신분증 재발급을 신청하고 거래를 관찰합니다.',
              '신용정보 조회로 신규 대출 여부를 살핍니다.',
              '사용 중인 계좌의 인증수단을 변경합니다.'],
  'answer': 0,
  'why': '금전 이체가 없더라도 명의도용 금융거래 위험이 남습니다. 금융위원회는 개인정보노출자 사고예방시스템과 금융거래 안심차단서비스를 안내합니다. 상황에 따라 금융회사 및 경찰과 추가 '
         '대응을 협의해야 합니다.',
  'source': ('금융위원회, 개인정보 유출 관련 소비자경보 (2026.10.06) · 링크 및 문서명 재확인 필요',
             'https://www.fsc.go.kr/no010101/87882'),
  'category': '피해 대응'},
 {'topic': '기관 사칭과 진짜 사건번호',
  'level': '상',
  'points': 12,
  'scene': '수사기관 직원이라는 사람이 사건번호와 담당 검사 이름을 알려줬습니다. 검색 결과 해당 사건과 검사 이름은 실제로 존재합니다. 상대방은 본인 명의 계좌의 안전을 확인하기 위해 '
           '별도 자금 이체가 필요하다고 설명합니다. 가장 정확한 판단은 무엇입니까?',
  'options': ['사건번호로 사건 진행 여부를 재검색합니다.',
              '상대방의 신분증과 공문서 원본을 요청합니다.',
              '공식 수사기관 경로로 연락자를 확인합니다.',
              '해당 금융회사에서 자금 이체를 문의합니다.'],
  'answer': 2,
  'why': '사건번호·실명·공문서가 진짜처럼 보여도 연락자 신원은 별개입니다. 수사기관을 사칭해 자금 이체를 요구하는 것은 대표적인 금융사기 수법입니다.',
  'source': ('금융위원회, 보이스피싱 피해예방 10계명 (2026.02.10) · 링크 및 문서명 재확인 필요', 'https://www.fsc.go.kr/no010101/86250'),
  'category': '신원 검증'},
 {'topic': '피해 직후의 대응 순서',
  'level': '상',
  'points': 12,
  'scene': '금융사기범에게 500만 원을 이체한 직후 사기임을 알게 됐습니다. 상대방 계좌번호와 이체 내역을 확보했지만 돈이 인출됐는지는 모릅니다. 가장 적절한 초기 대응은 무엇입니까?',
  'options': ['수취 계좌로 반환 요청을 우선 발송합니다.',
              '은행에 지급정지를 신속하게 요청합니다.',
              '경찰서에서 증거를 먼저 제출합니다.',
              '거래내역을 정리한 후 민사 절차를 검토합니다.'],
  'answer': 1,
  'why': '피해금 인출을 막기 위한 신속한 지급정지 요청이 중요합니다. 경찰 신고와 피해구제 신청을 함께 진행해야 하며, 실제 지급정지·환급 가능 여부는 법적 요건과 계좌 상태에 따라 '
         '다릅니다.',
  'source': ('금융위원회, 금융권 개인정보 유출 피해 예방 안내 (2026.10.07) · 링크 및 문서명 재확인 필요',
             'https://www.fsc.go.kr/no040101/?cnId=2221&curPage=1&pastPage=169&srchKey=&srchText='),
  'category': '피해 대응'},
 {'topic': '악성 앱과 독립 검증의 함정',
  'level': '최상',
  'points': 16,
  'scene': '신청하지 않은 카드 배송 전화를 받고 상담원의 안내대로 원격지원 앱을 설치했습니다. 이후 의심스러워 앱을 종료한 뒤, 휴대전화에서 은행 대표번호를 직접 눌렀습니다. 상담원은 '
           '카드 발급 내역이 없다고 말했습니다. 계좌 출금도 없습니다. 현재 판단으로 가장 적절한 것은 무엇입니까?',
  'options': ['은행 앱의 승인내역부터 다시 조회합니다.',
              '같은 기기에서 다른 은행에 재차 전화합니다.',
              '원격지원 앱을 삭제하고 통화를 반복합니다.',
              '다른 안전한 기기에서 공식 경로로 확인합니다.'],
  'answer': 3,
  'why': '악성 앱이나 원격제어 앱이 설치된 기기는 통화 연결과 금융정보가 침해됐을 가능성이 있습니다. 앱을 종료하거나 대표번호를 직접 입력했다는 사실만으로 안전이 확인되지 않습니다.',
  'source': ('금융감독원, 카드배송 사칭 보이스피싱 소비자경보 (2025.02.13) · 링크 및 문서명 재확인 필요',
             'https://www.abllife.co.kr/cms/custDesk/cspCntr/cspInfo/cspInfo2/__icsFiles/afieldfile/2025/02/14/250213.pdf'),
  'category': '기기 보안'},
 {'topic': '복합 피해: 검증 채널의 신뢰성',
  'level': '최상',
  'points': 16,
  'scene': '실제 대환대출을 신청한 뒤 상담원의 안내로 휴대전화에 보안 앱을 설치했습니다. 상담원은 기존 대출 잔액을 정확히 말하고 선상환 계좌를 보냈습니다. 이후 고객이 같은 '
           '휴대전화로 은행 대표번호에 전화하자 상담원이 상환을 안내했습니다. 다음 중 가장 신뢰할 만한 확인 방법은 무엇입니까?',
  'options': ['상담원이 안내한 상환 계좌의 명의를 조회합니다.',
              '휴대전화의 보안 앱을 종료하고 다시 통화합니다.',
              '다른 기기에서 기존 금융회사에 직접 확인합니다.',
              '신규 대출의 약정 금리와 잔액을 재확인합니다.'],
  'answer': 2,
  'why': '정확한 대출 정보와 대표번호 통화만으로는 안전을 보장할 수 없습니다. 이미 앱을 설치한 기기의 통화가 조작될 가능성을 배제하고, 다른 안전한 기기 또는 영업점에서 기존 '
         '금융회사에 상환 절차를 확인해야 합니다.',
  'source': ('금융위원회, 개인정보 유출 관련 소비자경보 (2026.10.06) · 링크 및 문서명 재확인 필요',
             'https://www.fsc.go.kr/no010101/87882'),
  'category': '기기 보안'}]

# SQLite is shared only by users served from the same running instance.
# Streamlit Community Cloud local disk is ephemeral; comments can disappear after restarts/redeploys.
DB_PATH = Path(os.getenv("SCAM_DB_PATH", "scam_comments.sqlite3"))

def connect_db():
    con = sqlite3.connect(str(DB_PATH), timeout=10)
    con.execute("PRAGMA busy_timeout=10000")
    con.execute("CREATE TABLE IF NOT EXISTS comments (id TEXT PRIMARY KEY, nickname TEXT NOT NULL, body TEXT NOT NULL, created_at TEXT NOT NULL, hidden INTEGER NOT NULL DEFAULT 0)")
    con.commit()
    return con

def get_comments():
    with connect_db() as con:
        return con.execute("SELECT nickname,body,created_at FROM comments WHERE hidden=0 ORDER BY created_at DESC LIMIT 40").fetchall()

def add_comment(nickname,body):
    with connect_db() as con:
        con.execute("INSERT INTO comments (id,nickname,body,created_at) VALUES (?,?,?,?)", (str(uuid.uuid4()),nickname,body,datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")))
        con.commit()

def moderate_comment(cid):
    with connect_db() as con:
        con.execute("UPDATE comments SET hidden=1 WHERE id=?",(cid,))
        con.commit()

for k, default in {"step":0,"answers":{},"finished":False,"saved_response":False}.items():
    if k not in st.session_state: st.session_state[k]=default

st.title("🛡️ SCAM OR SAFE?")
st.caption("실제 금융사기 수법 기반 · 금융사기 대응력 학습 테스트")
st.info("교육용 가상 사례이며 실제 피해 위험을 예측하는 검사는 아닙니다. 외부 출처의 문서명과 링크는 배포 전 검증해 주세요.")

if st.session_state.finished:
    score=sum(q["points"] for i,q in enumerate(QUESTIONS) if st.session_state.answers.get(i)==q["answer"])
    correct=sum(st.session_state.answers.get(i)==q["answer"] for i,q in enumerate(QUESTIONS))
    st.metric("나의 금융사기 대응 점수",f"{score} / 100점",f"{correct} / 8문항 정답",delta_color="off")
    if score>=88: grade="매우 우수"
    elif score>=70: grade="양호"
    elif score>=50: grade="추가 학습 권장"
    else: grade="집중 학습 권장"
    st.subheader(grade)
    st.caption("점수 구간은 교육용 자체 기준입니다. 실제 피해 가능성을 예측하지 않습니다.")
    st.subheader("영역별 학습 결과")
    for category in dict.fromkeys(q["category"] for q in QUESTIONS):
        indices=[i for i,q in enumerate(QUESTIONS) if q["category"]==category]
        n=sum(st.session_state.answers.get(i)==QUESTIONS[i]["answer"] for i in indices)
        st.write(f"**{category}** · {n}/{len(indices)}문항")
        st.progress(n/len(indices))
    st.caption("영역별 문항 수가 2개로 적어 정밀한 역량 진단이 아닌 학습 참고용입니다.")
    st.subheader("문제별 해설")
    for i,q in enumerate(QUESTIONS):
        ok=st.session_state.answers.get(i)==q["answer"]
        with st.expander(f"{'✅' if ok else '❌'} Q{i+1}. {q['topic']}"):
            st.write("선택:",q["options"][st.session_state.answers[i]])
            st.write("정답:",q["options"][q["answer"]])
            st.write(q["why"])
            st.caption(q["source"][0]);st.link_button("관련 자료 열기 ↗",q["source"][1])
    st.divider()
    st.subheader("💬 공개 한 줄 후기")
    st.caption("후기는 다른 방문자에게 공개됩니다. 실명·전화번호·계좌번호 등 개인정보를 입력하지 마세요. 닉네임과 댓글은 서버의 SQLite에 저장됩니다. 서버 재시작 시 삭제될 수 있습니다.")
    with st.form("comment_form",clear_on_submit=True):
        nickname=st.text_input("닉네임",max_chars=20,placeholder="예: 조심왕")
        comment=st.text_area("후기",max_chars=300,placeholder="가장 헷갈렸던 문제나 새로 알게 된 점을 남겨 주세요.")
        consent=st.checkbox("닉네임과 후기를 공개 게시판에 표시하는 데 동의합니다.")
        submitted=st.form_submit_button("후기 등록",type="primary")
        if submitted:
            nickname=nickname.strip();comment=comment.strip()
            if not (2<=len(nickname)<=20 and 2<=len(comment)<=300):
                st.error("닉네임은 2~20자, 후기는 2~300자로 입력해 주세요.")
            elif re.search(r"https?://|www\.|@|\b\d{2,3}-?\d{3,4}-?\d{4}\b",nickname+" "+comment,re.I):
                st.error("링크, 이메일 또는 전화번호로 보이는 정보는 등록할 수 없습니다.")
            elif not consent:
                st.error("공개 동의를 확인해 주세요.")
            else:
                add_comment(nickname,comment)
                st.success("후기가 등록되었습니다.")
    try:
        comments=get_comments()
        if not comments: st.caption("아직 작성된 후기가 없습니다.")
        for name,body,created in comments:
            with st.container(border=True):
                st.write("닉네임:",name)
                st.caption(created)
                st.text(body)
    except sqlite3.Error:
        st.warning("현재 댓글 저장소를 사용할 수 없습니다. 잠시 후 다시 시도해 주세요.")
    # Optional owner moderation: set ADMIN_PASSWORD in Streamlit secrets or environment.
    admin_password=os.getenv("ADMIN_PASSWORD", "")
    try: admin_password=st.secrets.get("ADMIN_PASSWORD",admin_password)
    except Exception: pass
    if admin_password:
        with st.expander("운영자: 댓글 숨김 처리"):
            entered=st.text_input("운영자 비밀번호",type="password")
            if entered==admin_password:
                with connect_db() as con:
                    rows=con.execute("SELECT id,nickname,substr(body,1,50) FROM comments WHERE hidden=0 ORDER BY created_at DESC LIMIT 100").fetchall()
                for cid,nick,preview in rows:
                    if st.button(f"숨김: {nick} — {preview}",key=f"hide_{cid}"):
                        moderate_comment(cid);st.rerun()
    if st.button("다시 도전하기"):
        st.session_state.step=0;st.session_state.answers={};st.session_state.finished=False
        for k in list(st.session_state.keys()):
            if k.startswith("choice_"): del st.session_state[k]
        st.rerun()
else:
    i=st.session_state.step;q=QUESTIONS[i]
    st.progress(i/len(QUESTIONS),text=f"문제 {i+1} / {len(QUESTIONS)} · 난이도 {q['level']} · {q['points']}점")
    st.subheader(q["topic"]);st.write(q["scene"])
    st.markdown("**가장 적절한 답변 하나를 선택하세요.**")
    choice=st.radio("선택지",list(range(4)),format_func=lambda x:f"{'ABCD'[x]}. {q['options'][x]}",index=None,key=f"choice_{i}",label_visibility="collapsed",disabled=i in st.session_state.answers)
    if i not in st.session_state.answers:
        if st.button("정답 제출",disabled=choice is None,type="primary"):
            st.session_state.answers[i]=choice;st.rerun()
    else:
        ok=st.session_state.answers[i]==q["answer"]
        (st.success if ok else st.error)("정답입니다." if ok else "오답입니다.")
        st.markdown(f"**정답: {'ABCD'[q['answer']]}**")
        st.write(q["why"])
        st.caption(q["source"][0]);st.link_button("관련 자료 보기 ↗",q["source"][1])
        if st.button("결과 확인" if i==len(QUESTIONS)-1 else "다음 문제 →",type="primary"):
            if i==len(QUESTIONS)-1:st.session_state.finished=True
            else:st.session_state.step+=1
            st.rerun()
st.divider()
st.caption("피해가 의심되면 금융회사 또는 경찰(112)에 즉시 신고하고 필요한 지급정지 조치를 문의하세요.")
