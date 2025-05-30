#==========================================
#-----------------youtube------------------
#==========================================

import yt_dlp
import sys
import datetime

TARGET_SUB_LANGS = ['en', 'fa']

def format_bytes(size_bytes):
    return f"{size_bytes / (1024 * 1024):.0f}MB" if size_bytes else "?"

def get_video_info(url):
    ydl_opts = {
        'quiet': True,
        'skip_download': True,
    }
    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        return ydl.extract_info(url, download=False)

def list_formats(info):
    video_only_raw = []
    audio_only_raw = []

    for f in info['formats']:
        size = f.get('filesize') or f.get('filesize_approx')
        if not size or not f.get('url'): continue

        if f.get('vcodec') != 'none' and f.get('acodec') == 'none':
            fps = f.get('fps')
            if isinstance(fps, (int, float)) and float(fps).is_integer():
                video_only_raw.append(f)
        elif f.get('vcodec') == 'none' and f.get('acodec') != 'none':
            if '-drc' in f.get('format_id', ''): continue
            audio_only_raw.append(f)

    def describe_media_for_url_listing(f, media_type="video"):
        ext = f.get('ext', '')
        size = f.get('filesize') or f.get('filesize_approx') or 0
        direct_url = f.get('url')

        if media_type == "video":
            res = f"{f.get('height', '?')}p"
            fps = f.get('fps')
            if fps and float(fps).is_integer(): res += f" {int(fps)}f"
            return f"{res} ({ext}) - {format_bytes(size)}", direct_url, size, ext
        elif media_type == "audio":
            abr = int(f.get('abr') or 0)
            return f"{abr} kbps ({ext}) - {format_bytes(size)}", direct_url, size, ext
        return "", None, 0, ""

    def create_hyperlink(url, text):
        return f"\x1b]8;;{url}\x07{text}\x1b]8;;\x07"

    print("\n🎥 فقط ویدیو:")
    temp_video_display_data = {}
    for f_video in video_only_raw:
        if f_video.get('ext') == 'webm':
            continue
        desc_text, download_url, current_size, _ = describe_media_for_url_listing(f_video, "video")
        if not download_url: continue
        height_str = f"{f_video.get('height', '?')}p"
        fps_str = ""
        fps_val = f_video.get('fps')
        if fps_val and float(fps_val).is_integer(): fps_str = f" {int(fps_val)}f"
        ext_str = f_video.get('ext', '')
        unique_key_for_video = f"{height_str}{fps_str}_{ext_str}"
        if unique_key_for_video not in temp_video_display_data or current_size > temp_video_display_data[unique_key_for_video]['size']:
            temp_video_display_data[unique_key_for_video] = {'desc': desc_text, 'url': download_url, 'size': current_size}
    if not temp_video_display_data:
        print("  متاسفانه، فرمتی (غیر از webm) برای نمایش لینک مستقیم ویدیو یافت نشد.")
    else:
        for item_data in sorted(temp_video_display_data.values(), key=lambda x: x['size'], reverse=True):
            hyperlink_text = create_hyperlink(item_data['url'], item_data['desc'])
            print(f"  {hyperlink_text}")

    print("\n🔊 فقط صدا:")
    temp_audio_display_data = {}
    for f_audio in audio_only_raw:
        desc_text, download_url, current_size, _ = describe_media_for_url_listing(f_audio, "audio")
        if not download_url: continue
        abr_str = f"{int(f_audio.get('abr') or 0)}kbps"
        ext_str = f_audio.get('ext', '')
        unique_key_for_audio = f"{abr_str}_{ext_str}"
        if unique_key_for_audio not in temp_audio_display_data or current_size > temp_audio_display_data[unique_key_for_audio]['size']:
            temp_audio_display_data[unique_key_for_audio] = {'desc': desc_text, 'url': download_url, 'size': current_size}
    if not temp_audio_display_data:
        print("  متاسفانه، فرمتی برای نمایش لینک مستقیم صدا یافت نشد.")
    else:
        for item_data in sorted(temp_audio_display_data.values(), key=lambda x: x['size'], reverse=True):
            hyperlink_text = create_hyperlink(item_data['url'], item_data['desc'])
            print(f"  {hyperlink_text}")

    print(f"\n📜 زیرنویس‌ها:")
    subtitles_linked_count = 0

    
    manual_subs_data = info.get('subtitles', {})
    if manual_subs_data:
        for lang_code, sub_formats_list in manual_subs_data.items():
            if lang_code not in TARGET_SUB_LANGS or not sub_formats_list:
                continue
            
            general_lang_name = lang_code 
            if sub_formats_list[0].get('name'):
                name_from_yt = sub_formats_list[0].get('name').strip()
                if name_from_yt: 
                    general_lang_name = name_from_yt

            for sub_entry in sub_formats_list: 
                sub_url = sub_entry.get('url')
                sub_ext = sub_entry.get('ext', 'unknown') 
                
                if sub_ext == 'vtt' and sub_url:
                    desc_text = f"{general_lang_name} ({sub_ext})" 
                    hyperlink = create_hyperlink(sub_url, desc_text)
                    print(f"  - {hyperlink}")
                    subtitles_linked_count += 1
    
    
    auto_subs_data = info.get('automatic_captions', {})
    if auto_subs_data:
        for lang_code, sub_formats_list in auto_subs_data.items():
            if lang_code != 'en' or not sub_formats_list:
                continue

            general_lang_name_auto = lang_code 
            if sub_formats_list[0].get('name'):
                name_from_yt_auto = sub_formats_list[0].get('name').strip()
                if name_from_yt_auto:
                    general_lang_name_auto = name_from_yt_auto
            
            display_name_for_auto_link = f"{general_lang_name_auto} (ربات)"

            for sub_entry in sub_formats_list:
                sub_url = sub_entry.get('url')
                sub_ext = sub_entry.get('ext', 'unknown')

                if sub_ext == 'vtt' and sub_url:
                    desc_text = f"{display_name_for_auto_link} ({sub_ext})" 
                    hyperlink = create_hyperlink(sub_url, desc_text)
                    print(f"  - {hyperlink}")
                    subtitles_linked_count += 1

    if subtitles_linked_count == 0:
        print(f"  زیرنویس VTT مطابق با معیارهای درخواستی (دستی: {', '.join(TARGET_SUB_LANGS)}، خودکار: فقط انگلیسی) یافت نشد.")

    return None

def main():
    url = input().strip()

    print("\n⏳ در حال گرفتن اطلاعات اولیه ویدیو...")
    try:
        info = get_video_info(url)
        if not info:
            print("❌ اطلاعاتی برای این لینک یافت نشد یا لینک نامعتبر است.")
            return

        video_title = info.get('title', 'N/A')
        duration_seconds = info.get('duration')
        duration_string_from_yt = info.get('duration_string')
        channel_name = info.get('channel') or info.get('uploader') or 'N/A'
        view_count_int = info.get('view_count')
        upload_date_str = info.get('upload_date')

        formatted_duration = "00:00:00"
        if isinstance(duration_seconds, (int, float)):
            s = int(duration_seconds)
            if s < 0: s = 0
            hours, remainder = divmod(s, 3600)
            minutes, seconds_val = divmod(remainder, 60)
            formatted_duration = f"{hours:02}:{minutes:02}:{seconds_val:02}"
        elif duration_string_from_yt:
            try:
                parts = str(duration_string_from_yt).split(':')
                int_parts = [int(p) for p in parts]
                h, m, s_val = 0, 0, 0
                if len(int_parts) == 3: h, m, s_val = int_parts[0], int_parts[1], int_parts[2]
                elif len(int_parts) == 2: m, s_val = int_parts[0], int_parts[1]
                elif len(int_parts) == 1: s_val = int_parts[0]
                formatted_duration = f"{h:02}:{m:02}:{s_val:02}"
            except ValueError: pass
        
        formatted_view_count = "N/A"
        if isinstance(view_count_int, int):
            formatted_view_count = f"{view_count_int:,}"
        
        formatted_upload_date = "N/A"
        if isinstance(upload_date_str, str) and len(upload_date_str) == 8:
            try:
                year, month, day = upload_date_str[0:4], upload_date_str[4:6], upload_date_str[6:8]
                formatted_upload_date = f"{year}/{month}/{day}"
            except ValueError: pass

        print(f"🎬 عنوان: {video_title}")
        print(f"📺 کانال: {channel_name}")
        print(f"⏱ مدت زمان: {formatted_duration}")
        print(f"👁️ تعداد بازدید: {formatted_view_count}")
        print(f"📅 تاریخ آپلود: {formatted_upload_date}")
        
        list_formats(info) 
            
    except yt_dlp.utils.DownloadError as e:
        print(f"\n❌ خطای yt-dlp: {e}")
    except Exception as e:
        print(f"\n❌ خطای ناشناخته: {e}")

if __name__ == '__main__':
    main()