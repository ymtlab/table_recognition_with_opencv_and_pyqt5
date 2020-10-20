# -*- coding: utf-8 -*-
import subprocess
from pathlib import Path

class Tesseract():
    def __init__(self, parent):
        self.tesseract = 'Tesseract-OCR/tesseract.exe'

    def command(self, filename, output_file):
        return [self.tesseract, str(filename), output_file.stem]

    def OCR(self, filename):
        output_file = Path('__temp__.txt')
        cmd = [self.tesseract, str(filename), output_file.stem]

        startupinfo = subprocess.STARTUPINFO()
        startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW
        startupinfo.wShowWindow = subprocess.SW_HIDE
        
        returncode = subprocess.Popen(cmd, startupinfo=startupinfo)
        returncode.wait()
        
        try:
            with open(output_file, 'r', encoding='utf-8') as file:
                output = file.readline()
            return output
        except:
            return ''
