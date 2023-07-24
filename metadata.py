"""
The purpose of this file is to define the metadata of the app with minimal imports. 

DO NOT CHANGE the name of the file
"""

from lapps.discriminators import Uri
from mmif import DocumentTypes, AnnotationTypes

from clams.app import ClamsApp
from clams.appmetadata import AppMetadata


# DO NOT CHANGE the function name 
def appmetadata() -> AppMetadata:
    """
    Function to set app-metadata values and return it as an ``AppMetadata`` obj.
    Read these documentations before changing the code below
    - https://sdk.clams.ai/appmetadata.html metadata specification. 
    - https://sdk.clams.ai/autodoc/clams.appmetadata.html python API
    
    :return: AppMetadata object holding all necessary information.
    """
    
    # first set up some basic information
    metadata = AppMetadata(
        name="Gentle Forced Aligner Wrapper",
        description="This CLAMS app aligns transcript and audio track using Gentle. "
                    "Gentle is a robust yet lenient forced aligner built on Kaldi."
                    "This app only works when Gentle is already installed locally."
                    "Unfortunately, Gentle is not distributed as a Python package distribution."
                    "To get Gentle installation instruction, see https://lowerquality.com/gentle/ "
                    "Make sure install Gentle from the git commit specified in ``analyzer_version`` "
                    "in this metadata.",
        analyzer_version='f29245a',
        app_license='MIT',
        analyzer_license="MIT",
        url="https://github.com/clamsproject/app-gentle-forced-aligner-wrapper",
        identifier="gentle-forced-aligner-wrapper",
    )
    metadata.add_input(DocumentTypes.TextDocument)
    metadata.add_input(DocumentTypes.AudioDocument)
    metadata.add_input(AnnotationTypes.TimeFrame, required=False, frameType='speech')
    metadata.add_input(Uri.TOKEN, required=False)

    metadata.add_output(Uri.TOKEN)
    metadata.add_output(AnnotationTypes.TimeFrame, frameType='speech', timeUnit='milliseconds')
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


# DO NOT CHANGE the main block
if __name__ == '__main__':
    import sys
    metadata = appmetadata()
    for param in ClamsApp.universal_parameters:
        metadata.add_parameter(**param)
    sys.stdout.write(metadata.jsonify(pretty=True))
