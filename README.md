# Getting Media Files from Internet Archive
###
### Scripts to list, get sizes and download media files on internet archive.
Inspired by Adam Jacobs and his collection.  https://blockclubchicago.org/2026/04/10/from-early-nirvana-to-phish-a-chicago-fans-secret-recordings-of-10000-shows-are-now-online/?utm_content=bufferfdba3&utm_medium=social&utm_source=twitter.com&utm_campaign=buffer

#### Scripts:

#### get_file_list_and_estimate_size.py
Get list of flac files on the drive and estimate size to download.  
Variables from .env file:
COLLECTION_ID - Which Archive.org collection to analyze (e.g. aadamjacobs) {input}
PERFORMANCE_SUMMARY - Output summary report will be saved {output}
PERFORMANCE_LIST_WITH_SIZES - Output list of each of the performances with size detail {output}

#### download_flacs_to_usb_claude-grok.py
find and download the flac files from a repo on internet archive to a local location.  

#### convert_flac_to_wav.py
Convert file format from flac to wav for transformation and playback.  (Lossless)

#### find_artist_wavs.py
Find files of specific artists from file location for transform

#### batch_clean_wav.py
Transforms based on configurations found in 'Transform_Configuration' directory location to improve audio quality.

#### diagnose_audio.py
Simple diagnostic of levels in the WAV file.

#### Transform_Configuration
Configurations in txt file within that designate levels for audio improvement.

#### Mock_dot_env_file
Create your .env file with this format - configure with your own path files.  Save this at the same folder location as the scripts.

