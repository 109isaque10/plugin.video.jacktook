import requests
from lib.utils.kodi_utils import notification, translation
from lib import xmltodict
import re
import xbmc
from lib.utils.settings import get_jackett_timeout

class Jackett:
    def __init__(self, host, apikey, notification) -> None:
        self.host = host.rstrip("/")
        self.apikey = apikey
        self._notification = notification

    def search(self, query, mode, season, episode):
        try:
            if mode == "tv":
                url = f"{self.host}/api/v2.0/indexers/all/results/torznab/api?apikey={self.apikey}&t=tvsearch&q={query}&season={season}&ep={episode}"
            elif mode == "movie":
                url = f"{self.host}/api/v2.0/indexers/all/results/torznab/api?apikey={self.apikey}&q={query}"
            elif mode == "multi":
                url = f"{self.host}/api/v2.0/indexers/all/results/torznab/api?apikey={self.apikey}&t=search&q={query}"
            res = requests.get(url, timeout=get_jackett_timeout())
            if res.status_code != 200:
                notification(f"{translation(30229)} ({res.status_code})")
                return
            return self.parse_response(res,season,episode)
        except Exception as e:
            self._notification(f"{translation(30229)}: {str(e)}")

    def parse_response(self, res, season, episode):
        res = xmltodict.parse(res.content)
        if "item" in res["rss"]["channel"]:
            item = res["rss"]["channel"]["item"]
            results = []
            for i in item if isinstance(item, list) else [item]:
                title = i.get("title","").upper()
                season_pattern = r'S\d+'
                episode_pattern = r'E\d+'
                complete_pattern = 'COMPLETO'
                season_range = r'S\d+-\d+'
                pattern = r'\d+'
                temporada_pattern = r'(\d+)\s*(?:[ªºA]\s*)?TEMPORADA'
                seasonr_substrings = re.findall(season_range, title)
                season_substrings = re.findall(season_pattern, title)
                seasonf = f'S{season:02}'
                episodef = f'E{episode:02}'
                xbmc.log(title,level=xbmc.LOGINFO)
                if len(season_substrings) > 0 and len(seasonr_substrings) < 0 and seasonf not in season_substrings:
                    xbmc.log('not season: 'seasonf,level=xbmc.LOGINFO)
                    continue
                if len(seasonr_substrings) > 0:
                    seasont = re.findall(pattern, seasonr_substrings[0])
                    if not (int(seasont[1])-int(season))>=0:
                 # filtered_items.append(item)
                        continue
                episode_substrings = re.findall(episode_pattern, title)
                if len(episode_substrings) > 0 and episodef not in episode_substrings:
                    xbmc.log('not episode: '+episodef,level=xbmc.LOGINFO)
                    continue
                complete_substrings = re.findall(complete_pattern, title)
                if not len(complete_substrings) > 0:
        #  filtered_items.append(item)
                    continue 
                temporada_substrings = re.findall(temporada_pattern, title)
                if len(temporada_substrings) > 0 and int(season) not in str(temporada_substrings):
                    continue
                xbmc.log('approved',level=xbmc.LOGINFO)
                extract_result(results, i)
            return results


def extract_result(results, item):
    attributes = {
        attr["@name"]: attr["@value"] for attr in item.get("torznab:attr", [])
    }
    results.append(
        {
            "qualityTitle": "",
            "title": item.get("title", ""),
            "indexer": item.get("jackettindexer", {}).get("#text", ""),
            "publishDate": item.get("pubDate", ""),
            "guid": item.get("guid", ""),
            "downloadUrl": item.get("link", ""),
            "size": item.get("size", ""),
            "magnetUrl": attributes.get("magneturl", ""),
            "seeders": attributes.get("seeders", ""),
            "peers": attributes.get("peers", ""),
            "infoHash": attributes.get("infohash", ""),
        }
    )
