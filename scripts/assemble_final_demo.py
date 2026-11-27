"""Combine a user-supplied real voice file with the genuine saved-LIVE capture."""
import argparse
import json
from pathlib import Path
import shutil
import subprocess

ROOT=Path(__file__).resolve().parents[1]

def probe(path):
    raw=subprocess.check_output(['ffprobe','-v','error','-show_streams','-show_format','-of','json',str(path)])
    return json.loads(raw)

def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--voice',type=Path,required=True,help='Actual user-supplied narration file; never synthetic voice.')
    parser.add_argument('--output',type=Path,default=ROOT/'reports/private/recording/RE-MEMORY-final-demo.mp4')
    args=parser.parse_args()
    if not shutil.which('ffmpeg') or not shutil.which('ffprobe'):parser.error('ffmpeg and ffprobe are required.')
    if not args.voice.is_file():parser.error('The supplied voice file does not exist.')
    if args.output.exists():parser.error('Output already exists; preserve it and select a new filename.')
    source=ROOT/'reports/private/recording/RE-MEMORY-screen-silent.mp4'
    voice=probe(args.voice);screen=probe(source)
    if not any(s['codec_type']=='audio' for s in voice['streams']):parser.error('Voice file has no audio track.')
    voice_duration=float(voice['format']['duration']);screen_duration=float(screen['format']['duration'])
    if not 60<=voice_duration<=176:parser.error('Narration must be60–176seconds so final video stays within1–3minutes.')
    duration=max(screen_duration,voice_duration+4)
    args.output.parent.mkdir(parents=True,exist_ok=True)
    subprocess.run(['ffmpeg','-hide_banner','-loglevel','error','-i',str(source),'-i',str(args.voice),
                    '-filter_complex','[0:v]tpad=stop_mode=clone:stop_duration=30[v];[1:a]adelay=2000:all=1,apad[a]',
                    '-map','[v]','-map','[a]','-t',str(duration),'-c:v','libx264','-preset','fast','-crf','22',
                    '-pix_fmt','yuv420p','-c:a','aac','-b:a','128k','-movflags','+faststart',str(args.output)],check=True)
    final=probe(args.output)
    assert 60<=float(final['format']['duration'])<=180
    assert any(s['codec_type']=='audio' for s in final['streams'])
    metadata={'mode':'GENUINE_UI_WITH_USER_SUPPLIED_VOICE','duration_seconds':float(final['format']['duration']),
              'voice_duration_seconds':voice_duration,'voice_source':'USER_SUPPLIED_REAL_NARRATION',
              'audio_video_sync_playback':'PENDING_HUMAN_AND_ASSISTANT_REVIEW','new_api_calls':0}
    args.output.with_suffix('.json').write_text(json.dumps(metadata,ensure_ascii=False,indent=2)+'\n')
    print(json.dumps({'output':str(args.output),'duration_seconds':metadata['duration_seconds'],'audio_track':True,'playback_review':'REQUIRED'}))

if __name__=='__main__':main()
