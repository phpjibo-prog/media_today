import yt_dlp

def fetch_youtube_formats(url):
    ydl_opts = {
        'quiet': True,
        'no_warnings': True,
    }
    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=False)
            formats = []
            
            # We filter for common usable formats (MP4 and Audio)
            for f in info.get('formats', []):
                if f.get('vcodec') != 'none' and f.get('acodec') != 'none': # Video + Audio
                    formats.append({
                        'ext': f['ext'],
                        'resolution': f.get('resolution', 'N/A'),
                        'url': f['url']
                    })
                elif f.get('vcodec') == 'none' and f.get('acodec') != 'none': # Audio only
                     formats.append({
                        'ext': 'mp3 (audio)',
                        'resolution': f.get('abr', 'N/A'),
                        'url': f['url']
                    })
            
            # Return top 6 useful formats to keep the UI clean
            return True, formats[:6]
    except Exception as e:
        return False, str(e)
