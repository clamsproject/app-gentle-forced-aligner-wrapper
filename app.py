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
            "requires": [MediaTypes.T, MediaTypes.V, Uri.TOKEN],
            "produces": [AnnotationTypes.FA],
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

    def add_fa_ann(self, view, window, faid, transcript_text, pretokenzized_viewid, pretokenized_starts, pretokenized_ends):
        fa_ann = view.new_annotation(f"fa_{faid}")

        fa_ann.attype = AnnotationTypes.FA
        fa_ann.start = self.get_time_obj([word for word in window if "start" in word][0]["start"]).isoformat()
        # the way that words are appended to the window ensures the last one always has successful alignment
        fa_ann.end = self.get_time_obj(window[-1]["end"]).isoformat()
        fa_ann.add_feature("target_tokens",
                           [f'{pretokenzized_viewid}:{pretokenized_starts[word["startOffset"]]}'
                            for word in window
                            # due to the different tokenization scheme,
                            # some tokens from gentle might not exist in the existing tokenization
                            if word["startOffset"] in pretokenized_starts])
        fa_ann.add_feature("text", transcript_text[window[0]["startOffset"]:window[-1]["endOffset"]])
        return fa_ann

    def annotate(self, mmif):

        if type(mmif) is not Mmif:
            mmif = Mmif(mmif)
        new_view = mmif.new_view()
        new_view.new_contain(AnnotationTypes.FA, self.__class__.__name__)

        try:
            token_view = mmif.get_view_contains(Uri.TOKEN)
        except KeyError:
            # TODO (krim @ 11/8/19): mmif has to have a helper code to return errors
            return ""
        pre_tokens_start = {}
        pre_tokens_end = {}
        for ann in token_view['annotations']:
            if ann['attype'] == Uri.TOKEN:
                pre_tokens_start[ann['start']] = ann['id']
                pre_tokens_end[ann['end']] = ann['id']
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
            window.append(word)
            if word["case"] == "success":
                aligned_tokens += 1
            if not aligned_tokens < sync_window:
                self.add_fa_ann(new_view, window, faid, transcript_text, token_view['id'], pre_tokens_start, pre_tokens_end)
                window = []
                aligned_tokens = 0
                faid += 1
        if len(window) > 0:
            self.add_fa_ann(new_view, window, faid, transcript_text, token_view['id'], pre_tokens_start, pre_tokens_end)

        for contain in new_view.contains.keys():
            mmif.contains.update({contain: new_view.id})
        return mmif


if __name__ == "__main__":
    gentle = GentleFA()
    gentle_service = Restifier(gentle)
    gentle_service.run()
