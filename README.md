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
```

## 빌드 설명

### MacOS
1. 개발자 인증서 발급은 공식 문서 참고
2. 사전 정보 입력
2.1. 정보 찾기
```zsh
security find-identity -p basic -v                                                                           
  1) XXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX "Apple Development: JOHN DOE (XXXXXXXXXX)"
  2) XXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX "Developer ID Application: JOHN DOE (XXXXXXXXXX)"
  ...
     N valid identities found
```
2.2. `Yonhwa Video Editor (MacOS).spec` (line 39)
```python
codesign_identity="Developer ID Application: JOHN DOE (XXXXXXXXXX)",
```
2.3. `resign_hook.py` (line 17)
```python
codesign_identity = "Apple Development: JOHN DOE (XXXXXXXXXX)"
```

3. 빌드
```bash
user@mac:/ $ pyinstaller lr2bga_mac.spec
```
3.1. 서명 확인
```bash
user@mac:/ $ cd dist
user@mac:/dist $ codesign --verify --verbose=4 ./LR2BGA-Converter.app   
./Yonhwa Video Editor.app: valid on disk
./Yonhwa Video Editor.app: satisfies its Designated Requirement
user@mac:/dist $ spctl -a -vvv -t install ./LR2BGA-Converter.app 
./Yonhwa Video Editor.app: rejected
source=Unnotarized Developer ID
origin=Developer IxD Application: JOHN DOE (XXXXXXXXXX)
```
3.2. 공증
```bash
user@mac:/dist $ xcrun notarytool store-credentials lr2bga-notarytool-password --team-id "개발자 팀 ID" --apple-id "개발자 이메일" --password "앱 비밀번호"
user@mac:/dist $ ditto -c -k --keepParent LR2BGA-Converter.app LR2BGA-Converter.app.zip
user@mac:/dist $ xcrun notarytool submit LR2BGA-Converter.app.zip --keychain-profile "lr2bga-notarytool-password" --wait
user@mac:/dist $ xcrun stapler staple LR2BGA-Converter.app
```
4. 확인
```bash
user@mac:/dist $ xcrun stapler validate LR2BGA-Converter.app
user@mac:/dist $ spctl -a -vvv -t install ./LR2BGA-Converter.app 
./Yonhwa Video Editor.app: accepted
source=Notarized Developer ID
origin=Developer ID Application: JOHN DOE (XXXXXXXXXX)
```

### Windows
```bash
user@windows:/ $ pyinstaller lr2bga_win.spec
```
