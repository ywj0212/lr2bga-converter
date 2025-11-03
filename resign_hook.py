# resign_hook.py
import os
import sys
import subprocess

def resign_python_lib():
    meipass = getattr(sys, '_MEIPASS', None)
    if meipass:
        # PyInstaller가 번들할 때, Python 공유 라이브러리는 보통 'Python' 또는 'Python.framework/Versions/3.11/Python' 경로에 위치함
        # 여기서는 예시로 _MEIPASS/Python 파일을 대상으로 함
        python_lib = os.path.join(meipass, 'Python')
        if os.path.exists(python_lib):
            print("Resigning Python shared library:", python_lib)
            # 기존 서명 제거
            subprocess.call(['codesign', '--remove-signature', python_lib])
            # Developer ID로 재서명 (아래의 Developer ID는 본인 환경에 맞게 수정)
            codesign_identity = "Developer ID Application: "
            subprocess.call([
                'codesign', '--force', '--timestamp',
                '--options', 'runtime', '--sign', codesign_identity, python_lib
            ])

if __name__ == '__main__':
    resign_python_lib()