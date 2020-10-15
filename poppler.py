# -*- coding: utf-8 -*-
import subprocess
from pathlib import Path
import chardet

class Poppler():
    def __init__(self):
        self.pdftocairo_path = Path('poppler/pdftocairo.exe')
        self.pdfinfo_path = Path('poppler/pdfinfo.exe')
        
    def pdftocairo(self, input_path, output_path, resolution):
        suffix = '-'+str(output_path.suffix).replace('.', '')
        cmd = [str(self.pdftocairo_path), suffix, '-r', str(resolution), str(input_path), str(output_path.stem)]
        r = self.subprocess_run(cmd)
        output = str(output_path.stem) + '-1.png'
        return output

    def subprocess_run(self, cmd):
        r = subprocess.run(cmd, stdout=subprocess.PIPE)
        r = r.stdout.decode('cp932')
        return r
