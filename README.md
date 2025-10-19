# LR2BGA Converter

DearPyGui 기반 LR2 BGA 변환 GUI 도구.

## 기능
- 프리셋/수동 명령 모드
- FFmpeg/FFprobe 내장 사용(PyInstaller onefile)
- 자동 MUX 탐색, 진행률 표시
- 다국어(i18n: 한국어/English/日本語)

## 실행
```bash
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate
pip install -r requirements.txt
python main.py
