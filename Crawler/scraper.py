import re
import requests
from requests.sessions import Session
from bs4 import BeautifulSoup
import yaml
import eyed3
import os
import time
from urllib.parse import unquote, quote
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.chrome.options import Options
import pandas as pd
from typing import List
import random
# from fp.fp import FreeProxy 

options = Options()
options.add_argument('--headless')
options.add_argument("--log-level=3") 
options.add_argument("--window-size=1920,1080")

user_agent_list = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/123.0.0.0 Safari/537.36 dtm_reg_debug 898_1711468243249",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/123.0.0.0 Safari/537.36 dtm_reg_debug 898_1711468285141",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36 dtm_reg_debug 2803_1711471625311",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 AVG/116.0.0.0",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/123.0.0.0 Safari/537.36 chromeOs",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/123.0.0.0 Safari/537.36 dtm_reg_debug 898_1711468096499"
]


class Request:
    def __init__(self, cookie_file: str = None, headers: dict = None, proxy: dict = None):
        if cookie_file is None:
            self.cookie = None
        else:
            self.cookie_file = cookie_file
            try:
                self.cookie = self._parse_cookie_file()
            except:
                raise

        if headers is None:
            self.headers = None
        else:
            self.headers = headers

        if proxy is None:
            self.proxy = None
        else:
            self.proxy = proxy

    def _parse_cookie_file(self) -> dict:
        """Parse a cookies.txt file and return a dictionary of key value pairs
        compatible with requests."""

        cookies = {}
        with open(self.cookie_file, 'r') as fp:
            for line in fp:
                if not re.match(r'^\#', line):
                    line_fields = line.strip().split('\t')
                    cookies[line_fields[5]] = line_fields[6]
        return cookies

    def request(self) -> requests.Session:
        """Create session using requests library and set cookie and headers."""

        request_session = requests.Session()
        if self.headers is not None:
            request_session.headers.update(self.headers)
        if self.cookie is not None:
            request_session.cookies.update(self.cookie)
        if self.proxy is not None:
            request_session.proxies.update(self.proxy)

        return request_session

# proxies_list = open("free_proxies_list.txt", "r").read().strip().split("\n") 

class Scraper:
    def __init__(self, session: Session, log: bool = False, lastfm_api_key: str = None):
        self.session = session
        self.log = log
        self.lastfm_api_key = lastfm_api_key
        
    @staticmethod
    def _turn_artist_uri_to_url(url: str) -> str : 
        parts = url.split(":") 
        artist_id = parts[2] 
        artist_url = 'https://open.spotify.com/artist/' + artist_id
        return artist_url
        
    @staticmethod
    def _str_to_json(string: str) -> dict:
        string = unquote(string)
        json_acceptable_string = string.replace('\n', '').strip()
        converted_string = yaml.load(json_acceptable_string, Loader=yaml.FullLoader)

        return converted_string
    
    @staticmethod
    def _turn_url_to_embed(url: str) -> str:
        if 'embed' in url:
            return url
        else:
            return url.replace('/track/', '/embed/track/')
        
    @staticmethod
    def _ms_to_readable(millis: int) -> str:
        seconds = int(millis / 1000) % 60
        minutes = int(millis / (1000 * 60)) % 60
        hours = int(millis / (1000 * 60 * 60)) % 24
        if hours == 0:
            return "%d:%d" % (minutes, seconds)
        else:
            return "%d:%d:%d" % (hours, minutes, seconds)
        
    def get_track_url_info(self, url: str) -> dict:
        try:
            load_ok = False
            while not load_ok : 
                page_content = self.session.get(url=self._turn_url_to_embed(url=url), stream=True,timeout=10).content
                bs_instance = BeautifulSoup(page_content, "lxml")
                print(bs_instance.find("script", {"id": "__NEXT_DATA__"}))
                if bs_instance.find("script", {"id": "__NEXT_DATA__"}):
                    load_ok = True
                else : 
                    load_ok = False
                    time.sleep(5)
                
            url_information = self._str_to_json(string=bs_instance.find("script", {"id": "__NEXT_DATA__"}).contents[0])
            entity_information = url_information['props']['pageProps']['state']['data']['entity']
            track_id = entity_information['uri'].split(":")[2]
            title = entity_information['name']
            if entity_information['audioPreview'] != None : 
                preview_mp3 = entity_information['audioPreview']['url']
            else : 
                preview_mp3 = None
            duration = self._ms_to_readable(millis=int(entity_information['duration']))
            artist_name = entity_information['artists'][0]['name']
            if title == "" and artist_name == "" : 
                return {
                    'track_id' : None,
                    'preview_mp3': None,
                    'duration': None,
                    'artist_name': None,
                    'artist_url': None,
                    'release_date': None,
                    'cover_art' : None,
                    'is_explicit' : None,
                }
            artist_url = self._turn_artist_uri_to_url(url=entity_information['artists'][0]['uri']) 
            release_date = entity_information['releaseDate']['isoString'] 
            is_explicit = entity_information['isExplicit'] 
            cover_art = entity_information['coverArt']['sources'][0]["url"]
            
            track_info = {
                'track_id' : track_id,
                'preview_mp3': preview_mp3,
                'duration': duration,
                'artist_name': artist_name,
                'artist_url': artist_url, 
                'release_date': release_date,
                'cover_art' : cover_art,    
                'is_explicit' : is_explicit,
            }

            # print(track_info)
            return track_info
            
        except:
            raise
        
    def get_cover_art(self, url : str) -> dict :
        try:
            # rotate user-agent
            user_agent = random.choice(user_agent_list)
            headers = {"User-Agent": user_agent} 
            load_ok = False
            while not load_ok : 
                page_content = self.session.get(url=self._turn_url_to_embed(url=url), stream=True,timeout=10, headers=headers).content
                bs_instance = BeautifulSoup(page_content, "lxml")
                print(bs_instance.find("script", {"id": "__NEXT_DATA__"}))
                if bs_instance.find("script", {"id": "__NEXT_DATA__"}):
                    load_ok = True
                else : 
                    load_ok = False
                    time.sleep(5)
                
            url_information = self._str_to_json(string=bs_instance.find("script", {"id": "__NEXT_DATA__"}).contents[0])
            entity_information = url_information['props']['pageProps']['state']['data']['entity']
            track_id = entity_information['uri'].split(":")[2]
            title = entity_information['name']
            if entity_information['audioPreview'] != None : 
                preview_mp3 = entity_information['audioPreview']['url']
            else : 
                preview_mp3 = None
            duration = self._ms_to_readable(millis=int(entity_information['duration']))
            artist_name = entity_information['artists'][0]['name']
            if title == "" and artist_name == "" : 
                return {
                    'cover_art' : None,
                }
            artist_url = self._turn_artist_uri_to_url(url=entity_information['artists'][0]['uri']) 
            release_date = entity_information['releaseDate']['isoString'] 
            is_explicit = entity_information['isExplicit'] 
            cover_art = entity_information['coverArt']['sources'][0]["url"]
            
            track_info = {
                'cover_art' : cover_art,    
            }

            # print(track_info)
            return track_info
            
        except:
            raise
        
    def crawl_and_append_cover_art(self, tracks_df : pd.DataFrame) -> pd.DataFrame : 
        series = tracks_df['track_url'].apply(lambda url: self.get_cover_art(url)['cover_art'])
        tracks_df.insert(loc=10, column='cover_art',value=series)
        return tracks_df
    
    def crawl_and_append_track_info(self, tracks_df: pd.DataFrame):
        tracks_df['additional_info'] = tracks_df['track_url'].apply(lambda url: self.get_track_url_info(url))
        # Tách các cột mới thành các cột riêng biệt
        tracks_df = pd.concat([tracks_df.drop(['additional_info'], axis=1), tracks_df['additional_info'].apply(pd.Series)], axis=1)
        return tracks_df
    
    def get_playlist_tracks_info(self, playlist_urls : List[str], genre : str = "Pop") -> pd.DataFrame : 
        driver = webdriver.Chrome(options=options)  
        tracks_dict = {}
        retry_urls = [] 
        remaining_urls = []
        final_df = pd.DataFrame() 
        
        try:
            for playlist_url in playlist_urls : 
                
                if playlist_url in retry_urls:
                    # Bỏ qua các URL đã được thêm vào danh sách retry_urls
                    continue
                
                driver.get(playlist_url)
                driver.implicitly_wait(10) # because this is a dynamic website we need to used this implicitly_wait() function
                time.sleep(5)
                
                previous_dict_len = len(tracks_dict)
                
                initial_height = 1500

                while True : 
                    driver.execute_script(f"const panel = document.querySelectorAll('div[data-overlayscrollbars-viewport]')[1]; panel.scrollTo(0,{initial_height});") 
                    # lỗi StaleElementReferenceException thì điều chỉnh height cho phù hợp 
                    initial_height += 600
                    
                    track_elements = WebDriverWait(driver, 10).until(
                        EC.presence_of_all_elements_located((By.CSS_SELECTOR, '[data-testid="tracklist-row"]'))
                    )

                    for element in track_elements:
                        # Lấy thông tin title và url của track
                        track_title = element.find_element(By.CSS_SELECTOR, '[data-testid="internal-track-link"]').text
                        track_url = element.find_element(By.CSS_SELECTOR, '[data-testid="internal-track-link"]').get_attribute('href')
                        track_album = element.find_elements(By.CLASS_NAME, '_TH6YAXEzJtzSxhkGSqu')[0].text
                        # print(element.find_elements(By.CSS_SELECTOR, '.standalone-ellipsis-one-line'))
                        

                        # Thêm vào dictionary
                        tracks_dict[track_title] = [track_url, track_album, genre]
                    time.sleep(4)
                    
                    if len(tracks_dict) == previous_dict_len : 
                        break
                    
                    # print(len(tracks_dict))
                    previous_dict_len = len(tracks_dict) 
                    
        except Exception as e:
            print(f"Exception occurred: {str(e)}")
            # Thêm URL gặp lỗi vào danh sách retry_urls
            # retry_urls.append(playlist_url)
            remaining_urls.extend(playlist_urls[playlist_urls.index(playlist_url):])

        finally:
            driver.quit()
            # Nếu có URL trong danh sách retry_urls, thì restart driver và tiếp tục crawl
            if remaining_urls:
                # Gọi đệ quy và tích hợp kết quả vào biến tạm
                retry_df = self.get_playlist_tracks_info(remaining_urls, genre)
                final_df = pd.concat([final_df, retry_df], ignore_index=True)
          
          
        # Chuyển đổi tracks_dict thành DataFrame
        df = pd.DataFrame.from_dict(tracks_dict, orient='index', columns=['track_url', 'track_album','genre'])
        df.reset_index(inplace=True)
        df.rename(columns={'index': 'track_title'}, inplace=True)
        
        # Tích hợp kết quả từ các URL thành công vào biến tạm
        final_df = pd.concat([final_df, df], ignore_index=True)
        
        return df
        
    def _preview_mp3_downloader(self, url: str, file_name: str, path: str = '') -> None:
        if path == '' : 
            pass
        else : 
            path += "/"
        
        saving_directory = path + file_name + ".mp3"
        song = self.session.get(url=url, stream=True) 
        with open(saving_directory, 'wb') as f : 
            f.write(song.content) 
        
        return 
    
    def download_preview_mp3(self, df: pd.DataFrame, path: str) -> None : 
        for index, row in df.iterrows() : 
            url = row['preview_mp3'] 
            file_name = row['track_id'] 
            self._preview_mp3_downloader(url=url, file_name=file_name, path=path)
            
        return 
    
    def check_existed_track() :
        pass
    
    @staticmethod 
    def _convert_special_characters(track_name : str) : 
        allowed_special_characters = ['.', ',', ':', ';', '!', ' ']
        converted_track_name = ''
        
        for char in track_name:
            if char.isalnum() or char in allowed_special_characters:
                converted_track_name += char
            elif char == '/':
                converted_track_name += '%2F'
            else:
                converted_track_name += quote(char)
        
        return converted_track_name
    
    @staticmethod
    def _convert_lastfm_url(track_name : str, artist_name : str, api_key: str) -> str : 
        modified_track_name = "+".join(track_name.split(" "))
        modified_artist_name = "+".join(artist_name.split(" "))
        try : 
            response = requests.get(f"https://ws.audioscrobbler.com/2.0/?method=track.getcorrection&artist={modified_artist_name}&track={modified_track_name}&api_key={api_key}&format=json")
            response_json = response.json()
            # if we found the corrected name
            if 'name' in response_json['corrections']['correction']['track']:
                url = response_json['corrections']['correction']['track']['url']
                return url+"/+tags"
            else:
                return f"https://www.last.fm/music/{modified_artist_name}/_/{modified_track_name}/+tags"
        except : 
            raise
    
    def fix_untagged_df(self, df : pd.DataFrame, proxy : dict) -> pd.DataFrame: 
        temp_df = df.copy()
        
        for index, row in df.iterrows() : 
            track_name = row['track_title']
            artist_name = row['artist_name']
            lastfm_url = self._convert_lastfm_url(track_name=self._convert_special_characters(track_name), artist_name=artist_name, api_key=self.lastfm_api_key)
            print(lastfm_url)
            try : 
                tags_list = []         
                page_content = self.session.get(url=lastfm_url, stream=True, proxies=proxy,timeout=60).content
                bs_instance = BeautifulSoup(page_content, "lxml")
                page_title = bs_instance.find(class_="subpage-title")
                parent_elements = bs_instance.find_all(class_="big-tags-item-name")
                if not page_title :
                    print("Blocked by Last.fm")
                    return temp_df
        
                for parent_element in parent_elements : 
                    tag_text = parent_element.find("a").text.strip() 
                    tags_list.append(tag_text)

                if tags_list : 
                    temp_df.at[index, 'tags'] = tags_list
                else : 
                    temp_df.at[index, 'tags'] = ["untagged"]
                print(temp_df.loc[index,'tags']) 
                time.sleep(1)
                
            except : 
                raise 
        
        return temp_df
    
    
    def get_lastfm_tags_df(self, df : pd.DataFrame) -> pd.DataFrame: 
        if 'tags' not in df.columns:
            df['tags'] = None
        
        for index, row in df.iterrows() : 
            print("Iteration: ", index)
            artist_name = row['artist_name']
            track_name = row['track_title']
            tags = self.get_lastfm_tags_api(api_key=self.lastfm_api_key, artist_name=artist_name, track_name=self._convert_special_characters(track_name))
            df.at[index, 'tags'] = tags
            time.sleep(1)
        
        return df
        
    def get_lastfm_tags_api(self, api_key : str, artist_name : str, track_name : str) -> List[str] : 
        modified_artist_name = "+".join(artist_name.split(" "))
        modified_track_name = "+".join(track_name.split(" "))
        url = f"https://ws.audioscrobbler.com/2.0/?method=track.getInfo&api_key={api_key}&artist={modified_artist_name}&track={modified_track_name}&autocorrect=1&format=json"
        try : 
            response = self.session.get(url=url, stream=True)
            response_json = response.json() 
            # print(response_json)
            tags_list = [] 
            
            tags = response_json['track']['toptags']['tag'] 
            for tag in tags : 
                tags_list.append(tag['name'])
            
            print(tags_list)
            return tags_list
        except :
            return []
        
        