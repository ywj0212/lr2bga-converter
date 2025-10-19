# KSX1001(완성형 2,350) → Unicode 코드포인트 범위 튜플(포함범위) 생성기
# 결과: KSX1001_HANGUL_RANGES  == [(0xAC00, 0xAC1B), ...]  (총 2,350자, 다수의 세그먼트)
import re, urllib.request
import csv, io

_JOYO_URLS = [
    # UTF-8 / EUC-JIS-2004 / Shift_JIS-2004 (모두 동일 내용)
    "https://x0213.org/joyo-kanji-code/joyo-kanji-code-u.csv",
    "https://x0213.org/joyo-kanji-code/joyo-kanji-code-euc.csv",
    "https://x0213.org/joyo-kanji-code/joyo-kanji-code-s.csv",
]
_HEX_PAT = re.compile(r'(?i)\bU\+([0-9A-F]{4,6})\b|^([0-9A-F]{4,6})$')


def build_ksx1001_hangul_codepoints():
    url = "https://www.unicode.org/Public/MAPPINGS/OBSOLETE/EASTASIA/KSC/KSX1001.TXT"
    txt = urllib.request.urlopen(url, timeout=30).read().decode("ascii", "ignore")

    cps = [int(m.group(1), 16)
           for m in re.finditer(r"^0x[0-9A-F]{4}\s+0x([0-9A-F]{4})\s+#\s+HANGUL",
                                txt, re.M)]
    cps.sort()
    return [f"0x{cp:04X}" for cp in cps]

def _normalize_key(s: str) -> str:
    # 열명 표기가 제각각일 수 있어, 영숫자만 남겨 소문자 비교
    return re.sub(r'[^a-z0-9]+', '', s.lower())

def _extract_cp_from_row(row):
    # 행의 모든 셀을 뒤에서부터 스캔하여 U+XXXX 또는 XXXX/XXXXX/XXXXXX를 찾음
    for cell in reversed(row):
        if not cell: 
            continue
        m = _HEX_PAT.search(cell.strip())
        if m:
            hx = (m.group(1) or m.group(2)).upper()
            return int(hx, 16)
    return None

def build_joyo_kanji_codepoints():
    last_err = None
    for url in _JOYO_URLS:
        try:
            raw = urllib.request.urlopen(url, timeout=30).read()
            # 우선 UTF-8 시도, 실패시 일본계 인코딩 폴백
            for enc in ("utf-8", "utf-8-sig", "cp932", "euc-jp"):
                try:
                    text = raw.decode(enc)
                    break
                except UnicodeDecodeError:
                    text = None
            if text is None:
                continue

            f = io.StringIO(text)
            sn = csv.Sniffer()
            # 콤마/탭 등 자동 추정
            try:
                dialect = sn.sniff('\n'.join(text.splitlines()[:5]))
            except Exception:
                dialect = csv.excel
            reader = csv.reader(f, dialect)

            rows = list(reader)
            if not rows:
                continue

            # 헤더 존재 시 UCS/Unicode 계열 열 인덱스 우선 탐색
            header = rows[0]
            norm2idx = {_normalize_key(h): i for i, h in enumerate(header)}
            ucs_idx = None
            for key in ("ucs", "unicode", "ucsunicode", "ucscodepoint"):
                if key in norm2idx:
                    ucs_idx = norm2idx[key]
                    break

            cps = []
            start_i = 1 if any(header) else 0
            for row in rows[start_i:]:
                if not any(row): 
                    continue
                cp = None
                if ucs_idx is not None and ucs_idx < len(row) and row[ucs_idx]:
                    m = _HEX_PAT.search(row[ucs_idx].strip())
                    if m:
                        hx = (m.group(1) or m.group(2)).upper()
                        cp = int(hx, 16)
                if cp is None:
                    cp = _extract_cp_from_row(row)
                if cp is not None:
                    cps.append(cp)

            cps = sorted(set(cps))
            # 기대치 검증(상용한자 2,136자, 일부 배포본은 경미 변동 가능)
            if len(cps) < 2000:
                raise ValueError(f"too few rows parsed: {len(cps)}")

            # 16진 문자열 배열로 반환 (가변 자릿수: 0x20B9F 등 대응)
            return [f"0x{cp:X}" for cp in cps]

        except Exception as e:
            last_err = e
            continue
    raise RuntimeError(f"Failed to fetch/parse Joyo CSV: {last_err}")

KSX1001_HANGUL_RANGES = build_ksx1001_hangul_codepoints()
JAPANESE_MIN_RANGES = build_joyo_kanji_codepoints() + [
    *[f"0x{cp:04X}" for cp in range(0x3041, 0x3097)],   # ぁ〜ゖ
    *[f"0x{cp:04X}" for cp in range(0x309D, 0x309F)],   # ゝゞ
    *[f"0x{cp:04X}" for cp in range(0x30A1, 0x30FB)],   # ァ〜・(직전)
    "0x30FB", "0x30FC", "0x30FD", "0x30FE",             # ・ーヽヾ
    "0x3001", "0x3002",                                 # 、。
    *[f"0x{cp:04X}" for cp in range(0x300C, 0x3012)],   # 「」『』【】
    *[f"0x{cp:04X}" for cp in range(0x31F0, 0x31FF)],   # 「」『』【】
    *[f"0x{cp:04X}" for cp in range(0xFF65, 0xFF9F)],   # 「」『』【】
    "0x301C"                                            # 〜
]

print(len(KSX1001_HANGUL_RANGES))  # 2350
print(len(JAPANESE_MIN_RANGES))      # 2136 (혹은 2137, 확장자 포함 시)

string = ""

string += "KSX1001_HANGUL_RANGES = ["
for cp in KSX1001_HANGUL_RANGES:
    string += cp + ", "
string = string[:-2]
string += "]\n"
string += "JAPANESE_MIN_RANGES = ["
for cp in JAPANESE_MIN_RANGES:
    string += cp + ", "
string = string[:-2]
string += "]\n"

with open("codepoints.py", "w") as f:
    f.write(string)