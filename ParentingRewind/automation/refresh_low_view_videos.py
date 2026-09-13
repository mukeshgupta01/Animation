"""One-time, user-selected low-view replacements through the existing hourly queue."""
import argparse
import ctypes
from contextlib import contextmanager
import json
from pathlib import Path
import shutil
import time
from youtube_auth import authorized_service, atomic_json, SafetyError
import private_uploader as u

RUNTIME = Path(__file__).parent / 'runtime'
PLAN = RUNTIME / 'low-view-refresh-plan.json'
JOURNAL = RUNTIME / 'low-view-refresh-journal.json'
INTRO = {
 'pYp1xPnL0xk': 'Does bedtime keep stretching after the last story? See a warm, clear way to end the routine without turning every extra request into another negotiation.',
 'fJly770ChhY': 'Both children want the same kitchen job? Turn a vague request to help into one clear, age-appropriate task for each child, with examples you can use at dinner time.',
 'fkSCCKhHoMk': 'Water, a blanket, another trip down the hallway: bedtime requests can pile up after goodnight. This short shows how to prepare predictable needs before the final story while staying responsive to illness or safety concerns.',
 'T1UfMOBRxqY': 'A little comfort can fit inside a clear bedtime routine. See how a familiar comfort choice gives a school-age child a say without starting a brand-new bedtime activity.',
 'DRYjvKGsln8': 'One more book has become five more books? Set the reading plan before opening the first page, offer two choices that fit your limit, and close bedtime warmly.',
 'SnGnEAaXPHY': 'Soccer practice is over, but leaving is the hard part. Try a small choice about carrying the ball or water bottle while keeping the ending clear.',
 'XtuQ126oRqQ': 'Time to leave the playground, and your preschooler refuses? Watch a calm approach: move close, name one concrete final turn, and follow through together.',
 'tE8ozO-oDJM': 'When your teen starts sharing a friendship problem, can you pause the warnings long enough to hear the whole story? This short offers a calm question that helps you understand what support they want.',
 'EbpWyH8kE_8': 'Your toddler refuses the car seat. Keep the safety boundary clear, use fewer words, and offer a small choice about getting into the seat while the car stays parked.',
 '83UWWA7A2iE': 'A toddler bites during a toy struggle. Respond to the immediate safety problem without calling the child bad: separate calmly, check the other child, then teach a safer action when everyone has settled.',
 'gIQ9ODvDYZQ': 'A friendship message has upset your child. Before drafting their reply for them, try asking whether they want you to listen or help think of ideas.',
 'ejL84TaFAEE': 'Do the arguments get more attention than the teamwork? Notice a specific helpful action during dinner preparation and tell your children exactly what made a difference.',
 '1aGtaQWy0HI': 'Leaving the library can feel sudden to a preschooler absorbed in books. Preview a few clear steps before the final story ends, then guide the transition one step at a time.',
}


@contextmanager
def upload_mutex():
    kernel = ctypes.WinDLL('kernel32', use_last_error=True)
    kernel.CreateMutexW.argtypes = [ctypes.c_void_p, ctypes.c_bool, ctypes.c_wchar_p]
    kernel.CreateMutexW.restype = ctypes.c_void_p
    kernel.WaitForSingleObject.argtypes = [ctypes.c_void_p, ctypes.c_uint32]
    kernel.ReleaseMutex.argtypes = [ctypes.c_void_p]
    kernel.CloseHandle.argtypes = [ctypes.c_void_p]
    handle = kernel.CreateMutexW(None, False, 'Global\\ParentingRewindPublicUploader')
    if not handle:
        raise ctypes.WinError(ctypes.get_last_error())
    acquired = False
    try:
        acquired = kernel.WaitForSingleObject(handle, 0) in (0, 128)
        if not acquired:
            raise SafetyError('An upload cycle is active. Retry after it finishes.')
        yield
    finally:
        if acquired:
            kernel.ReleaseMutex(handle)
        kernel.CloseHandle(handle)


def prepare():
    audit = json.loads((RUNTIME / 'under-10-views.json').read_text())
    rows = {r['video_id']: r for r in u.active_upload_rows(u.ledger_rows())}
    cfg = u.config()
    folder = u.source_directory(cfg)
    items = []
    for video in audit['videos']:
        ident = video['id']
        if ident not in INTRO:
            continue
        row = rows[ident]
        source = folder / row['source_name']
        if u.sha256(source) != row['sha256'].upper() or not u.ffprobe_ok(source):
            raise SafetyError(f'Invalid replacement source: {source.name}')
        body, meta_path, meta = u.upload_metadata(source, cfg)
        if body['snippet']['title'] != video['title']:
            raise SafetyError('Local and live titles differ.')
        description = INTRO[ident] + '\n\nPause. Rewind. Repair.\n\nSubscribe for practical parenting ideas for adults and caregivers.\n\nGeneral parenting education; adapt suggestions to your child and family. This is not individual medical or therapeutic advice.\n\nResearch and further reading:\n' + '\n'.join(u.research_urls(meta)) + '\n\n#ParentingTips #PositiveParenting #ParentingRewind'
        items.append(dict(id=ident, title=video['title'], prior_views=int(video['views']),
                          prior_privacy=video['privacy'], source=str(source), sha256=row['sha256'],
                          metadata=str(meta_path), new_description=description))
    if len(items) != 13:
        raise SafetyError('Expected exactly the 13 user-selected ordinary videos.')
    plan = dict(channel_id='UCGb-IUQX2KQa_KA24MwE_aQ', prepared_at=u.utc_text(),
                action='Delete selected videos only if still below 10 views; queue public replacements at existing hourly cadence.',
                excludes='All Fathers Day videos', items=items)
    atomic_json(PLAN, plan)
    review = '# Parenting Rewind replacement plan\n\n13 selected ordinary videos; Father\'s Day videos excluded. Existing one-hour public upload cadence. Local masters are hash-verified. Old URLs will be permanently removed.\n\n'
    for item in items:
        review += f"## {item['title']}\n\nOld ID: {item['id']}; views: {item['prior_views']}; visibility: {item['prior_privacy']}.\n\n{item['new_description']}\n\n"
    (RUNTIME / 'low-view-refresh-plan.md').write_text(review, encoding='utf-8')
    print(f'Prepared {len(items)} replacements; no video changed.')


def apply():
    plan = json.loads(PLAN.read_text())
    if {i['id'] for i in plan['items']} != set(INTRO):
        raise SafetyError('Plan differs from the user-selected IDs.')
    journal = json.loads(JOURNAL.read_text()) if JOURNAL.exists() else {'items': {}}
    with upload_mutex():
        service, channel = authorized_service()
        try:
            if channel['channel_id'] != plan['channel_id']:
                raise SafetyError('Channel mismatch.')
            for item in plan['items']:
                ident = item['id']
                state = journal['items'].get(ident, {})
                if state.get('status') == 'queued':
                    continue
                source, meta_path = Path(item['source']), Path(item['metadata'])
                if u.sha256(source) != item['sha256'].upper() or not u.ffprobe_ok(source):
                    raise SafetyError('Replacement source changed.')
                live = service.videos().list(part='snippet,status,statistics', id=ident).execute().get('items', [])
                if not live and state.get('status') not in ('delete-requested', 'deleted'):
                    raise SafetyError('Video missing before our recorded deletion; inspect manually.')
                if live:
                    actual = live[0]
                    if actual['snippet']['channelId'] != channel['channel_id'] or actual['snippet']['title'] != item['title']:
                        raise SafetyError('Live identity/title changed.')
                    views = actual.get('statistics', {}).get('viewCount')
                    if views is None or int(views) >= 10:
                        state.update(status='skipped-view-count-changed', live_views=views)
                        journal['items'][ident] = state; atomic_json(JOURNAL, journal)
                        continue
                    if actual['status']['privacyStatus'] != item['prior_privacy']:
                        raise SafetyError('Live privacy changed since selection.')
                    backup = RUNTIME / 'low-view-refresh-backups' / ident
                    backup.mkdir(parents=True, exist_ok=True)
                    if not (backup / 'metadata.json').exists():
                        shutil.copy2(meta_path, backup / 'metadata.json')
                        atomic_json(backup / 'live-video.json', actual)
                    meta = json.loads(meta_path.read_text(encoding='utf-8'))
                    meta['description'] = item['new_description']
                    atomic_json(meta_path, meta)
                    state.update(status='delete-requested', requested_at=u.utc_text())
                    journal['items'][ident] = state; atomic_json(JOURNAL, journal)
                    service.videos().delete(id=ident).execute()
                for attempt in range(6):
                    if not service.videos().list(part='id', id=ident).execute().get('items'):
                        break
                    if attempt == 5:
                        raise SafetyError('Deletion not yet verified; no replacement queued. Retry this resumable journal after propagation.')
                    time.sleep(2)
                state.update(status='deleted', deletion_verified_at=u.utc_text())
                journal['items'][ident] = state; atomic_json(JOURNAL, journal)
                if not any(r.get('missing_video_id') == ident for r in u.ledger_rows()):
                    u.append_ledger(dict(event='remote-video-missing', missing_video_id=ident,
                        verified_utc=u.utc_text(), reason='User-authorized under-10-view replacement, excluding Fathers Day',
                        source_name=source.name, sha256=item['sha256'], replacement_status='queued-hourly'))
                state.update(status='queued', source=str(source), queued_at=u.utc_text())
                journal['items'][ident] = state; atomic_json(JOURNAL, journal)
                print(f'Queued replacement: {item["title"]}', flush=True)
        finally:
            service.close()


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('command', choices=['prepare', 'apply'])
    parser.add_argument('--confirm-selected-deletions', action='store_true')
    args = parser.parse_args()
    if args.command == 'prepare':
        prepare()
    elif args.confirm_selected_deletions:
        apply()
    else:
        parser.error('Deletion requires --confirm-selected-deletions')
