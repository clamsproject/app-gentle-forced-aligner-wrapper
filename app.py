import sys
import subprocess
import tempfile
from clams.serve import ClamApp
from clams.serialize import *
from clams.vocab import AnnotationTypes
from clams.vocab import MediaTypes
from clams.restify import Restifier
from lapps.discriminators import Uri  # TODO move to clams

PYTHON_BIN = sys.executable
GENTLEFA_BIN = "/opt/gentle/align.py"
FFMPEG_BIN = "ffmpeg"

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
        tmp_wav = tempfile.mkstemp()[1]
        demux_cmd = [FFMPEG_BIN, "-i", video_path, "-y", "-vn", "-f", "wav", "-ab", "8000", tmp_wav]
        subprocess.run(demux_cmd, stderr=subprocess.DEVNULL)

        forcedalign_cmd = [PYTHON_BIN, GENTLEFA_BIN, tmp_wav, text_path]
        gentle_pipe = subprocess.Popen(forcedalign_cmd, stdout=subprocess.PIPE, stderr=subprocess.DEVNULL)
        return gentle_pipe.communicate()[0]

    @staticmethod
    def get_time_obj(fp_seconds):
        i_part = int(fp_seconds)
        f_part = int((fp_seconds % 1) * 1000000)
        h = i_part // 3600
        m = (i_part % 3600) // 60
        s = i_part % 60
        return datetime.time(hour=h, minute=m, second=s, microsecond=f_part)

    def add_fa_ann(self, view, window, faid, transcript_text):
        fa_ann = view.new_annotation(f"fa_{faid}")

        fa_ann.attype = AnnotationTypes.FA
        fa_ann.start = self.get_time_obj([word for word in window if "start" in word][0]["start"]).isoformat()
        # the way that words are appended to the window ensures the last one always has successful alignment
        fa_ann.end = self.get_time_obj(window[-1]["end"]).isoformat()
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
        aligned_tokens = 0
        for word in fa["words"]:
            tok_ann = new_view.new_annotation(f"tok_{tid}")
            tok_ann.attype = Uri.TOKEN
            tok_ann.start = word["startOffset"]
            tok_ann.end = word["endOffset"]
            tok_ann.add_feature("word", word["word"])
            tid += 1
            window.append(word)
            if word["case"] == "success":
                aligned_tokens += 1
            if not aligned_tokens < sync_window:
                self.add_fa_ann(new_view, window, faid, transcript_text)
                window = []
                aligned_tokens = 0
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
