"""Read-only channel-wide view audit with verified local replacement sources."""
import hashlib
import json
from pathlib import Path
from datetime import datetime, timezone
from youtube_auth import authorized_service, atomic_json
from private_uploader import active_upload_rows, ledger_rows, PROJECT


def main():
    service, channel = authorized_service()
    try:
        uploads = service.channels().list(part='contentDetails', mine=True).execute()['items'][0]['contentDetails']['relatedPlaylists']['uploads']
        ids, page = [], None
        while True:
            response = service.playlistItems().list(part='contentDetails', playlistId=uploads, maxResults=50, pageToken=page).execute()
            ids.extend(item['contentDetails']['videoId'] for item in response['items'])
            page = response.get('nextPageToken')
            if not page:
                break
        ledger = {r['video_id']: r for r in active_upload_rows(ledger_rows())}
        videos = []
        for offset in range(0, len(ids), 50):
            response = service.videos().list(part='snippet,status,statistics,contentDetails', id=','.join(ids[offset:offset+50])).execute()
            for item in response['items']:
                if item['snippet']['channelId'] != channel['channel_id']:
                    raise RuntimeError('Unexpected channel in audit response.')
                row = ledger.get(item['id'], {})
                source = Path(row.get('source_path', '__missing__'))
                if not source.is_file():
                    source = PROJECT / 'output' / row.get('source_name', '__missing__')
                verified = False
                if item.get('statistics', {}).get('viewCount') == '0' and source.is_file() and row.get('sha256'):
                    verified = hashlib.sha256(source.read_bytes()).hexdigest().upper() == row['sha256'].upper()
                videos.append({'id': item['id'], 'title': item['snippet']['title'],
                    'published_at': item['snippet']['publishedAt'], 'views': item.get('statistics', {}).get('viewCount'),
                    'privacy': item['status']['privacyStatus'], 'source': str(source) if source.is_file() else None,
                    'source_sha256_verified': verified, 'metadata': row.get('metadata_path'),
                    'live': item})
        zero = [v for v in videos if v['views'] == '0']
        report = {'checked_at': datetime.now(timezone.utc).isoformat(), 'channel': channel, 'read_only': True,
                  'total': len(videos), 'zero_view_count': len(zero), 'videos': videos}
        atomic_json(Path(__file__).parent / 'runtime/zero-view-audit.json', report)
        print(json.dumps({'total': len(videos), 'zero_view_count': len(zero),
            'zero_view_videos': [{k:v[k] for k in ('id','title','published_at','privacy','source_sha256_verified')} for v in zero]}, indent=2))
    finally:
        service.close()


if __name__ == '__main__':
    main()
