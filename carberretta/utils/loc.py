import os

from pygount import SourceAnalysis

from carberretta.utils import ROOT_DIR


class CodeCounter:
    def __init__(self):
        self.code = 0
        self.docs = 0
        self.empty = 0

    def count(self):
        for subdir, _, files in os.walk(ROOT_DIR / "carberretta"):
            for file in (f for f in files if f.endswith(".py")):
                analysis = SourceAnalysis.from_file(f"{subdir}/{file}", "pygount", encoding="utf-8")
                self.code += analysis.code_count
                self.docs += analysis.documentation_count
                self.empty += analysis.empty_count
