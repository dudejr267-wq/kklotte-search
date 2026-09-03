"""
school_photo_viewer.html + school_meal_photos.json → school_photo_viewer_standalone.html
JSON을 HTML에 인라인 삽입해서 file:// 프로토콜에서도 동작
"""
import json, os, re

base = os.path.dirname(os.path.abspath(__file__))

with open(os.path.join(base, 'school_meal_photos.json'), encoding='utf-8') as f:
    data = json.load(f)

with open(os.path.join(base, 'school_photo_viewer.html'), encoding='utf-8') as f:
    html = f.read()

json_str = json.dumps(data, ensure_ascii=False)

# loadData() 함수를 인라인 버전으로 교체
old_func = """async function loadData() {
  document.getElementById('loadingOverlay').classList.add('show');
  try {
    const res = await fetch('school_meal_photos.json');
    if (!res.ok) throw new Error('파일 없음');
    DB = await res.json();
    document.getElementById('totalBadge').textContent =
      `${DB.length}개교 · ${DB.reduce((s,d)=>s+d.entries.length,0)}일치 데이터`;
  } catch(e) {
    document.getElementById('totalBadge').textContent = '데이터 없음';
    document.getElementById('mainContent').innerHTML = `
      <div class="empty">
        <div class="empty-icon">⚠️</div>
        <h2>데이터 파일을 찾을 수 없어요</h2>
        <p>school_meal_photos.json 파일이 같은 폴더에 있는지 확인해주세요.<br>
        스크래퍼를 먼저 실행해야 합니다.</p>
      </div>`;
    document.getElementById('loadingOverlay').classList.remove('show');
    return;
  }

  document.getElementById('loadingOverlay').classList.remove('show');"""

new_func = f"""function loadData() {{
  DB = {json_str};
  document.getElementById('totalBadge').textContent =
    `${{DB.length}}개교 · ${{DB.reduce((s,d)=>s+d.entries.length,0)}}일치 데이터`;"""

result = html.replace(old_func, new_func)

# async function loadData 호출도 동기로 변경 (await 없이)
result = result.replace('await loadData()', 'loadData()')
# 함수 선언 async 제거 (이미 function으로 바꿨으니 OK)

# ── 경기롯데 제품 키워드 추출 & 주입 ──
searcher_path = os.path.join(base, '검색기.html')
kw_set = set()
if os.path.exists(searcher_path):
    with open(searcher_path, encoding='utf-8') as f:
        sh = f.read()
    skip = {'기본','신제품','할인','세트','행사','상품','제품','학교','급식','전용',
            '시즌','특가','추가','구성','포함','사용','국내산','원산지'}
    for name in re.findall(r'name:"([^"]+)"', sh):
        for w in re.findall(r'[가-힣]{2,}', name):
            if w not in skip:
                kw_set.add(w)
    for cat in re.findall(r'category:"([^"]+)"', sh):
        for w in re.findall(r'[가-힣]{2,}', cat):
            if w not in skip:
                kw_set.add(w)
    kw_js = ', '.join(f'"{w}"' for w in sorted(kw_set))
    result = result.replace(
        'const PRODUCT_KW = new Set(); // __PRODUCT_KW_PLACEHOLDER__',
        f'const PRODUCT_KW = new Set([{kw_js}]);'
    )
    print(f'제품 키워드: {len(kw_set)}개 주입')

out = os.path.join(base, 'school_photo_viewer_standalone.html')
with open(out, 'w', encoding='utf-8') as f:
    f.write(result)

print(f'완료: {out}')
print(f'파일 크기: {os.path.getsize(out):,} bytes ({os.path.getsize(out)//1024} KB)')
