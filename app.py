import argparse
import multiprocessing
import tempfile

import concatrim
import gentle
from clams.app import ClamsApp
from clams.appmetadata import AppMetadata
from clams.restify import Restifier
from gentle import metasentence
from gentle.transcription import Word
from lapps.discriminators import Uri
from mmif.serialize import *
from mmif.vocabulary import AnnotationTypes
from mmif.vocabulary import DocumentTypes

__version__ = '0.1.0'


class GentleForcedAligner(ClamsApp):

    silence_gap = 1.0  # seconds to insert between segments when patchworking
    # multipliers to convert to milliseconds
    timeunit_conv = {'milliseconds': 1, 'seconds': 1000}

    def _appmetadata(self) -> AppMetadata:
        metadata = AppMetadata(
            name="Gentle Forced Aligner Wrapper",
            description="This CLAMS app aligns transcript and audio track using Gentle. "
                        "Gentle is a robust yet lenient forced aligner built on Kaldi."
                        "This app only works when Gentle is already installed locally."
                        "Unfortunately, Gentle is not distributed as a Python package distribution."
                        "To get Gentle installation instruction, see https://lowerquality.com/gentle/ "
                        "Make sure install Gentle from the git commit specified in ``wrappee_version`` "
                        "in this metadata.",
            app_version=__version__,
            wrappee_version='2148efc',
            license='MIT',
            wrappee_license='MIT',
            identifier=f"http://apps.clams.ai/gentle-forced-aligner-wrapper/{__version__}",
        )
        metadata.add_input(DocumentTypes.TextDocument)
        metadata.add_input(DocumentTypes.AudioDocument)
        metadata.add_input(AnnotationTypes.TimeFrame, required=False, frameType='speech')
        metadata.add_input(Uri.TOKEN, required=False)
        
        metadata.add_output(Uri.TOKEN)
        metadata.add_output(AnnotationTypes.TimeFrame, frameType='speech')
        metadata.add_output(AnnotationTypes.Alignment)  # TODO (krim @ 7/9/21): specify src/tgt types?
        
        metadata.add_parameter(name='use_speech_segmentation', type='boolean', 
                               description='When set true, use exising "speech"-typed ``TimeFrame`` annotations '
                                           'and run aligner only on those frames, instead of entire audio files.', 
                               default='true')
        metadata.add_parameter(name='use_tokenization', type='boolean',
                               description='When set true, ``Alignment`` annotation output will honor existing '
                                           'latest tokenization (``Token`` annotations). Due to a limitation of the '
                                           'way Kaldi reads in English tokens, existing tokens must not contain '
                                           'whitespaces. ',
                               default='true')
        return metadata

    @staticmethod
    def run_gentle(audio_path: str, text_content: str, tokenization_view: View = None):

        with gentle.resampled(audio_path) as audio_file:
            resources = gentle.Resources()
            aligner = gentle.ForcedAligner(resources, text_content, 
                                           nthreads=multiprocessing.cpu_count(), 
                                           disfluencies={'uh', 'um'},
                                           disfluency=True,
                                           conservative=False)
            if tokenization_view is not None:
                aligner.ms._seq = []
                for token in tokenization_view.get_annotations(Uri.TOKEN):
                    print(token.serialize(pretty=True))
                    start = token.properties['start']
                    end = token.properties['end']
                    token_text = text_content[start:end]
                    kaldi_token = {'start': start, 'end': end, 
                                   'token': metasentence.kaldi_normalize(token_text, aligner.ms.vocab)}
                    aligner.ms._seq.append(kaldi_token)
            result = aligner.transcribe(audio_file)
            return result

    def _annotate(self, mmif, **params):

        if not isinstance(mmif, Mmif):
            mmif = Mmif(mmif)
        new_view = mmif.new_view()
        self.sign_view(new_view, self.get_configuration(**params))
        new_view.new_contain(AnnotationTypes.TimeFrame, timeUnit='milliseconds')
        new_view.new_contain(AnnotationTypes.Alignment, sourceType=Uri.TOKEN, targetType=AnnotationTypes.TimeFrame)
        use_speech_segmentation = params.get('use_speech_segmentation', True)
        use_tokenization = params.get('use_tokenization', True)
        
        # get paths from the first of each types
        audio = mmif.get_documents_by_type(DocumentTypes.AudioDocument)[0]
        transcript = mmif.get_documents_by_type(DocumentTypes.TextDocument)[0]
        audio_f = audio.location_path()
        trimmer = concatrim.Concatrimmer(audio_f, 1000)
        
        if use_speech_segmentation:
            segment_views = [view for view in mmif.get_views_for_document(audio.id) 
                                 if AnnotationTypes.TimeFrame in view.metadata.contains]

            if len(segment_views) > 1:
                # TODO (krim @ 11/30/20): we might want to actually handle 
                # this situation; e.g. for evaluating multiple segmenter
                raise ValueError('got multiple segmentation views for a document with TimeFrames')
            elif len(segment_views) == 1:
                view = segment_views[0]
                timeunit = view.metadata.contains[AnnotationTypes.TimeFrame]['timeUnit']
                for ann in view.get_annotations(AnnotationTypes.TimeFrame, frameType='speech'):
                    trimmer.add_spans((int(ann.properties['start'] * self.timeunit_conv[timeunit]),
                                       int(ann.properties['end'] * self.timeunit_conv[timeunit])))
                outdir = tempfile.TemporaryDirectory()
                audio_f = trimmer.concatrim(outdir.name)
                
        if use_tokenization:
            token_view = mmif.get_view_contains(Uri.TOKEN)
        else:
            token_view = None
        if transcript.location == '':
            transcript_text = transcript.text_value
        else:
            with open(transcript.location_path()) as transcript_file:
                transcript_text = transcript_file.read()
            
        gentle_alignment = self.run_gentle(audio_f, transcript_text, token_view)
        for pre_token, gentle_word in zip(token_view.get_annotations(Uri.TOKEN) if token_view is not None else iter(lambda: None, 1),
                                          gentle_alignment.words):  # result.words must be a sorted list of Word objects
            if pre_token is None:
                token_ann = new_view.new_annotation(Uri.TOKEN,
                                                    start=gentle_word.startOffset,
                                                    end=gentle_word.endOffset,
                                                    word=gentle_word.word,
                                                    document=transcript.id)
                token_id = token_ann.id
            else:
                token_id = f"{token_view.id}:{pre_token.id}"
                
            if gentle_word.case == Word.SUCCESS:  # means this word is successfully aligned
                tf_ann = new_view.new_annotation(AnnotationTypes.TimeFrame,
                                                 frameType='speech', 
                                                 start=trimmer.conv_to_original(int(self.timeunit_conv['seconds'] * gentle_word.start)),
                                                 end=trimmer.conv_to_original(int(self.timeunit_conv['seconds'] * gentle_word.end)))
                new_view.new_annotation(AnnotationTypes.Alignment, 
                                        source=token_id, 
                                        target=tf_ann.id)

        return mmif


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument(
        '--production',
        action='store_true',
        help='run gunicorn server'
    )
    parsed_args = parser.parse_args()

    gentlewrapper = GentleForcedAligner()
    gentle_service = Restifier(gentlewrapper)
    if parsed_args.production:
        gentle_service.serve_production()
    else:
        gentle_service.run()
