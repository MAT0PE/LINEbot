import requests
from datetime import datetime, timedelta
from bs4 import BeautifulSoup
import sqlite3
import sys


# get data by scraping
def fetch_data(url1, url2):
    today = {}
    tomorrow = {}
    r = requests.get(url1)
    if r.status_code == 200:
        soup = BeautifulSoup(r.text, 'html.parser')
        rain = soup.find_all("tr", class_="rain-probability")
        today['rain'] = [p.text for p in rain[0].find_all("td")]
        tomorrow['rain'] = [p.text for p in rain[1].find_all("td")]
        temperature = soup.find_all("div", class_="weather-wrap clearfix")
        today['temperature'] = [p.text for p in temperature[0].find_all("span", class_="value")]
        tomorrow['temperature'] = [p.text for p in temperature[1].find_all("span", class_="value")]
        today['wind'] = soup.find_all("td", colspan="4")[0].text
        tomorrow['wind'] = soup.find_all("td", colspan="4")[1].text
    r2 = requests.get(url2)
    if r2.status_code == 200:
        soup = BeautifulSoup(r2.text, 'html.parser')
        today['comments'] = [c.text for c in soup.find_all("span", class_="indexes-telop-1")[:3]]
        tomorrow['comments'] = [c.text for c in soup.find_all("span", class_="indexes-telop-1")[3:]]
    return today, tomorrow


# create record of new postalcode in today and tomorrow
def insert_record(postalcode):
    url1, url2 = postalcode_to_urls(postalcode)
    today, tomorrow = fetch_data(url1, url2)
    conn = sqlite3.connect("file:/root/LINEbot/weather.db", uri=True)
    cur = conn.cursor()
    cur.execute('INSERT INTO today VALUES(?, ?, ?, ?, ?)', (postalcode, str(today['rain']), str(today['temperature']), today['wind'], str(today['comments'])))
    cur.execute('INSERT INTO tomorrow VALUES(?, ?, ?, ?, ?)', (postalcode, str(tomorrow['rain']), str(tomorrow['temperature']), tomorrow['wind'], str(tomorrow['comments'])))
    conn.commit()
    cur.close()
    conn.close()


# update record of given postalcode in today and tomorrow
def update_record(postalcode):
    url1, url2 = postalcode_to_urls(postalcode)
    today, tomorrow = fetch_data(url1, url2)
    conn = sqlite3.connect("file:/root/LINEbot/weather.db", uri=True)
    cur = conn.cursor()
    cur.execute('UPDATE today SET rain = ?, temperature = ?, wind = ?, comments = ? where postalcode = ?', (str(today['rain']), str(today['temperature']), today['wind'], str(today['comments']), postalcode))
    cur.execute('UPDATE tomorrow SET rain = ?, temperature = ?, wind = ?, comments = ? where postalcode = ?', (str(tomorrow['rain']), str(tomorrow['temperature']), tomorrow['wind'], str(tomorrow['comments']), postalcode))
    conn.commit()
    cur.close()
    conn.close()


# update all records
def update_all():
    postalcodes = get_all_postalcodes()
    for postalcode in postalcodes:
        # postalcode can be None
        if postalcode:
            update_record(postalcode)
    print(datetime.now()+timedelta(hours=9), " -> updated")


# create record of new user in ipm
def create_user(lineid):
    conn = sqlite3.connect("file:/root/LINEbot/weather.db", uri=True)
    cur = conn.cursor()
    cur.execute('INSERT INTO ipm VALUES(?, ?, 0)',(lineid, None))
    conn.commit()
    cur.close()
    conn.close()


# change postalcode in ipm
def change_postalcode(lineid, postalcode):
    conn = sqlite3.connect("file:/root/LINEbot/weather.db", uri=True)
    cur = conn.cursor()
    cur.execute('UPDATE ipm SET postalcode = ? where lineid = ?', (postalcode, lineid))
    conn.commit()
    cur.close()
    conn.close()


# set mute to 1 in ipm
def muted(lineid):
    conn = sqlite3.connect("file:/root/LINEbot/weather.db", uri=True)
    cur = conn.cursor() 
    cur.execute('UPDATE ipm SET mute = 1 where lineid = ?', (lineid,))
    conn.commit()
    cur.close()
    conn.close()


# set mute to 0 in ipm
def unmuted(lineid):
    conn = sqlite3.connect("file:/root/LINEbot/weather.db", uri=True)
    cur = conn.cursor()
    cur.execute('UPDATE ipm SET mute = 0 where lineid = ?', (lineid,))
    conn.commit()
    cur.close()
    conn.close()


# get all postalcodes
def get_all_postalcodes():
    conn = sqlite3.connect("file:/root/LINEbot/weather.db", uri=True)
    cur = conn.cursor()
    cur.execute('SELECT postalcode FROM pu')
    ret = column_to_list(cur.fetchall())
    cur.close()
    conn.close()
    return ret


# get all lineids
def get_all_lineids():
    conn = sqlite3.connect("file:/root/LINEbot/weather.db", uri=True)
    cur = conn.cursor()
    cur.execute('SELECT DISTINCT lineid FROM ipm')
    ret = column_to_list(cur.fetchall())
    cur.close()
    conn.close()
    return ret


# get all non-muted lineids
def get_all_nonmuted_lineids():
    conn = sqlite3.connect("file:/root/LINEbot/weather.db", uri=True)
    cur = conn.cursor()
    cur.execute('SELECT DISTINCT lineid FROM ipm where mute is not 1')
    ret = column_to_list(cur.fetchall())
    cur.close()
    conn.close()
    return ret


# convert list of column into list
def column_to_list(d):
    ret = []
    for a in d:
        ret.append(a[0])
    return ret


# convert string into list
def string_to_list(s):
    return s[1:-1].split(", ")


# get postalcode of given lineid
def lineid_to_postalcode(lineid):
    conn = sqlite3.connect("file:/root/LINEbot/weather.db", uri=True)
    cur = conn.cursor()
    cur.execute("SELECT postalcode FROM ipm WHERE lineid = ?",(lineid,))
    try:
        ret = column_to_list(cur.fetchall())[0]
        cur.close()
        conn.close()
        return ret
    except Exception as e:
        print("There was an error:" + str(e))


# get urls of given postalcode
def postalcode_to_urls(postalcode):
    conn = sqlite3.connect("file:/root/LINEbot/weather.db", uri=True)
    cur = conn.cursor()
    cur.execute('SELECT url1, url2 FROM pu WHERE postalcode = ?', (postalcode,))
    ret = cur.fetchall()[0]
    cur.close()
    conn.close()
    return ret


# get today's data
def get_today(lineid):
    postalcode = lineid_to_postalcode(lineid)
    if postalcode:
        try:
            conn = sqlite3.connect("file:/root/LINEbot/weather.db", uri=True)
            cur = conn.cursor()
            cur.execute('SELECT * FROM today WHERE postalcode = ?', (postalcode,))
            t = cur.fetchall()[0]
            ret = {
                'rain': string_to_list(t[1]),
                'temperature': string_to_list(t[2]),
                'wind': t[3],
                'comments': string_to_list(t[4])
            }
            cur.close()
            conn.close()
            return ret
        except Exception as e:
            print("There was an error:" + str(e))


# get tomorrow's data
def get_tomorrow(lineid):
    postalcode = lineid_to_postalcode(lineid)
    if postalcode:
        try:
            conn = sqlite3.connect("file:/root/LINEbot/weather.db", uri=True)
            cur = conn.cursor()
            cur.execute('SELECT * FROM tomorrow WHERE postalcode = ?', (postalcode,))
            t = cur.fetchall()[0]
            ret = {
                'rain': string_to_list(t[1]),
                'temperature': string_to_list(t[2]),
                'wind': t[3],
                'comments': string_to_list(t[4])
            }
            cur.close()
            conn.close()
            return ret
        except Exception as e:
            print("There was an error:" + str(e))


# get urls of given postalcode
def fetch_urls(postalcode):
    r = requests.get("https://tenki.jp/search/?keyword={}".format(postalcode))
    if r.status_code == 200:
        soup = BeautifulSoup(r.text, 'html.parser')
        search_entry_data = soup.find("p", class_="search-entry-data")
        if search_entry_data:
            relative =  search_entry_data.find("a").get('href')[9:]
            return "https://tenki.jp/forecast{}".format(relative), "https://tenki.jp/indexes/dress{}".format(relative)



# create new record in pu
def insert_record_pu(postalcode, url1, url2):
    conn = sqlite3.connect("file:/root/LINEbot/weather.db", uri=True)
    cur = conn.cursor()
    cur.execute('INSERT INTO pu VALUES(?, ?, ?)', (postalcode, url1, url2))
    conn.commit()
    cur.close()
    conn.close()


# tables are created when this file is executed with argument "initialize"
if __name__ == '__main__':
    try:
        if sys.argv[1] == 'initialize':
            conn = sqlite3.connect("file:/root/LINEbot/weather.db", uri=True)
            cur = conn.cursor()
            cur.execute('CREATE TABLE today(postalcode, rain, temperature, wind, comments)') # str, str(list), str(list), str, str(list)
            cur.execute('CREATE TABLE tomorrow(postalcode, rain, temperature, wind, comments)') # str, str(list), str(list), str, str(list)
            cur.execute('CREATE TABLE ipm(lineid, postalcode, mute)') # str, str, int(mute=0 not muted, mute=1 muted)
            cur.execute('CREATE TABLE pu(postalcode, url1, url2)') # str, str, str
            conn.commit()
            cur.close()
            conn.close()
        else:
            update_all()
            print('argument for initializing is "initialize"')
    except:
        update_all()
