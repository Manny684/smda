import datetime
import json
import os

from smda.DisassemblyStatistics import DisassemblyStatistics
from .SmdaFunction import SmdaFunction


class SmdaReport(object):

    architecture = None
    base_addr = None
    binary_size = None
    binweight = None
    bitness = None
    code_areas = None
    component = None
    confidence_threshold = None
    disassembly_errors = None
    execution_time = None
    family = None
    filename = None
    identified_alignment = None
    is_library = None
    message = None
    sha256 = None
    smda_version = None
    statistics = None
    # status can be "ok", "timeout", "error"
    status = None
    timestamp = None
    version = None
    xcfg = None

    def __init__(self, disassembly=None):
        if disassembly is not None:
            self.architecture = disassembly.binary_info.architecture
            self.base_addr = disassembly.binary_info.base_addr
            self.binary_size = disassembly.binary_info.binary_size
            self.binweight = 0
            self.bitness = disassembly.binary_info.bitness
            self.code_areas = disassembly.binary_info.code_areas
            self.component = disassembly.binary_info.component
            self.confidence_threshold = disassembly.getConfidenceThreshold()
            self.disassembly_errors = disassembly.errors
            self.execution_time = disassembly.getAnalysisDuration()
            self.family = disassembly.binary_info.family
            self.filename = os.path.basename(disassembly.binary_info.file_path)
            self.identified_alignment = disassembly.identified_alignment
            self.is_library = disassembly.binary_info.is_library
            self.message = "Analysis finished regularly."
            self.sha256 = disassembly.binary_info.sha256
            self.smda_version = disassembly.smda_version
            self.statistics = DisassemblyStatistics(disassembly)
            self.status = disassembly.getAnalysisOutcome()
            if self.status == "timeout":
                self.message = "Analysis was stopped when running into the timeout."
            self.timestamp = datetime.datetime.utcnow().strftime("%Y-%m-%dT%H-%M-%S")
            self.version = disassembly.binary_info.version
            self.xcfg = self._convertCfg(disassembly)

    def _convertCfg(self, disassembly):
        function_results = {}
        for function_offset in disassembly.functions:
            if self.confidence_threshold and function_offset in disassembly.candidates and disassembly.candidates[function_offset].getConfidence() < self.confidence_threshold:
                continue
            smda_function = SmdaFunction(disassembly, function_offset)
            function_results[function_offset] = smda_function
            self.binweight += smda_function.binweight
        return function_results

    def getFunction(self, function_addr):
        return self.xcfg[function_addr] if function_addr in self.xcfg else None

    def getFunctions(self):
        for _, smda_function in sorted(self.xcfg.items()):
            yield smda_function

    @classmethod
    def fromFile(cls, file_path):
        smda_json = {}
        if os.path.isfile(file_path):
            with open(file_path, "r") as fjson:
                smda_json = json.load(fjson)
        return SmdaReport.fromDict(smda_json)

    @classmethod
    def fromDict(cls, report_dict):
        smda_report = cls(None)
        smda_report.architecture = report_dict["architecture"]
        smda_report.base_addr = report_dict["base_addr"]
        smda_report.binary_size = report_dict["binary_size"]
        smda_report.bitness = report_dict["bitness"]
        smda_report.code_areas = report_dict["code_areas"]
        smda_report.confidence_threshold = report_dict["confidence_threshold"]
        smda_report.disassembly_errors = report_dict["disassembly_errors"]
        smda_report.execution_time = report_dict["execution_time"]
        smda_report.identified_alignment = report_dict["identified_alignment"]
        if "metadata" in report_dict:
            if "binweight" in report_dict["metadata"]:
                smda_report.binweight = report_dict["metadata"]["binweight"]
            if "component" in report_dict["metadata"]:
                smda_report.component = report_dict["metadata"]["component"]
            if "family" in report_dict["metadata"]:
                smda_report.family = report_dict["metadata"]["family"]
            if "filename" in report_dict["metadata"]:
                smda_report.filename = report_dict["metadata"]["filename"]
            if "is_library" in report_dict["metadata"]:
                smda_report.is_library = report_dict["metadata"]["is_library"]
            if "version" in report_dict["metadata"]:
                smda_report.version = report_dict["metadata"]["version"]
        smda_report.message = report_dict["message"]
        smda_report.sha256 = report_dict["sha256"]
        smda_report.smda_version = report_dict["smda_version"]
        smda_report.statistics = DisassemblyStatistics.fromDict(report_dict["statistics"])
        smda_report.status = report_dict["status"]
        smda_report.timestamp = datetime.datetime.strptime(report_dict["timestamp"], "%Y-%m-%dT%H-%M-%S")
        smda_report.xcfg = {int(function_addr): SmdaFunction.fromDict(function_dict) for function_addr, function_dict in report_dict["xcfg"].items()}
        return smda_report

    def toDict(self):
        return {
            "architecture": self.architecture,
            "base_addr": self.base_addr,
            "binary_size": self.binary_size,
            "bitness": self.bitness,
            "code_areas": self.code_areas,
            "confidence_threshold": self.confidence_threshold,
            "disassembly_errors": self.disassembly_errors,
            "execution_time": self.execution_time,
            "identified_alignment": self.identified_alignment,
            "metadata" : {
                "binweight": self.binweight,
                "component": self.component,
                "family": self.family,
                "filename": self.filename,
                "is_library": self.is_library,
                "version": self.version,
            },
            "message": self.message,
            "sha256": self.sha256,
            "smda_version": self.smda_version,
            "statistics": self.statistics.toDict(),
            "status": self.status,
            "timestamp": self.timestamp,
            "xcfg": {function_addr: smda_function.toDict() for function_addr, smda_function in self.xcfg.items()}
        }

    def __str__(self):
        return "{:>6.3f}s -> (architecture: {}.{}bit, base_addr: 0x{:08x}): {} functions".format(self.execution_time, self.architecture, self.bitness, self.base_addr, len(self.xcfg))
