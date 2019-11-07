import sys
import subprocess
from clams.serve import ClamApp
from clams.serialize import *
from clams.vocab import AnnotationTypes
from clams.vocab import MediaTypes
from clams.restify import Restifier
from lapps.discriminators import Uri  # TODO move to clams

PYTHON = sys.executable
GENTLEFA_BIN = "/opt/gentle/align.py"

class GentleFA(ClamApp):
    def appmetadata(self):
        metadata = {
            "name": "Gentle Forced Aligner Wrapper",
            "description": "This tool align transcript and audio track using Gentle. "
                           "Gentle is a robust yet lenient forced aligner built on Kaldi."
                           "See https://lowerquality.com/gentle/ .",
            "vendor": "Team CLAMS",
            "requires": [MediaTypes.T, MediaTypes.V],
            "produces": [AnnotationTypes.FA, Uri.TOKEN],
        }
        return metadata

    def sniff(self, mmif):
        # this mock-up method always returns true
        return True

    @staticmethod
    def run_gentle(video_path, text_path):
        cmd = [PYTHON, GENTLEFA_BIN, video_path, text_path]
        gentle_pipe = subprocess.Popen(cmd, stdout=subprocess.PIPE)
        return gentle_pipe.communicate()[0]

    @staticmethod
    def add_fa_ann(view, window, faid, transcript_text):
        fa_ann = view.new_annotation(f"fa_{faid}")

        fa_ann.attype = AnnotationTypes.FA
        fa_ann.start = round(window[0]["start"], 2)
        fa_ann.end = round(window[-1]["start"], 2)
        start_offset = window[0]["startOffset"]
        end_offset = window[-1]["endOffset"]
        fa_ann.add_feature("start_offset", start_offset)
        fa_ann.add_feature("end_offset", end_offset)
        fa_ann.add_feature("text", transcript_text[start_offset:end_offset])
        return fa_ann

    def annotate(self, mmif):

        if type(mmif) is not Mmif:
            mmif = Mmif(mmif)
        new_view = mmif.new_view()
        new_view.new_contain(Uri.TOKEN, "GentleFA")
        new_view.new_contain(AnnotationTypes.FA, "GentleFA")

        transcript_location = mmif.get_medium_location(MediaTypes.T)
        audio_location = mmif.get_medium_location(MediaTypes.V)
        fa = json.loads(self.run_gentle(audio_location, transcript_location))
        transcript_text = open(transcript_location).read()

        sync_window = 10
        tid = 1
        faid = 1
        window = []
        for word in fa["words"]:
            tok_ann = new_view.new_annotation(f"tok_{tid}")
            tok_ann.attype = Uri.TOKEN
            tok_ann.start = word["startOffset"]
            tok_ann.end = word["endOffset"]
            tok_ann.add_feature("word", word["word"])
            tid += 1
            if word["case"] == "success":
                window.append(word)
                if not len(window) < sync_window:
                    self.add_fa_ann(new_view, window, faid, transcript_text)
                    window = []
                    faid += 1
        if len(window) > 0:
            self.add_fa_ann(new_view, window, faid, transcript_text)

        for contain in new_view.contains.keys():
            mmif.contains.update({contain: new_view.id})
        return mmif


if __name__ == "__main__":
    gentle = GentleFA()
    gentle_service = Restifier(gentle)
    gentle_service.run()
