from pyyoutube import Api
import json
from datetime import datetime
import warnings

warnings.filterwarnings("ignore")

playlistIds = []
key = "" #API Key

with open('./json/key.json') as file:
    key = json.load(file)['key']

api = Api(api_key=key)
currentPlaylists = {}
date = ""
diffText = ""

def playlistRead():

    playlistIds = []
    global date

    with open("./json/config.json", "r") as file:
        obj = json.load(file)
        playlistIds = obj["playlistIds"]
        date = obj['date']

    return playlistIds

def scanPlaylist(id):

    playlist = api.get_playlist_by_id(playlist_id=id)
    name = playlist.items[0].to_dict()['id']#['snippet']['title']

    currentPlaylists[name] = {}

    #print(playlist.items[0].to_dict()['contentDetails'])
    playlistitems = api.get_playlist_items(playlist_id=id,count=None)

    print("Reading",len(playlistitems.items),"items from:",playlist.items[0].to_dict()['snippet']['title']+".")

    for i in range(len(playlistitems.items)):
        try:
            id = playlistitems.items[i].snippet.resourceId.videoId
            video_by_id = api.get_video_by_id(video_id=id)
            videoData = (video_by_id.items[0].to_dict())

            currentPlaylists[name][videoData['id']] = {}
            currentPlaylists[name][videoData['id']]['Title'] = videoData['snippet']['title']
            currentPlaylists[name][videoData['id']]['VideoUrl'] = "https://www.youtube.com/watch?v="+videoData['id']
            currentPlaylists[name][videoData['id']]['ChannelUrl'] = "https://www.youtube.com/channel/"+videoData['snippet']['channelId']
        except:
            currentPlaylists[name][i]={}
            currentPlaylists[name][i]['Title'] = "Failed to Retrieve"
            currentPlaylists[name][i]['VideoUrl'] = "" #"https://www.youtube.com/watch?v="+videoData['id']
            currentPlaylists[name][i]['ChannelUrl'] = "" #"https://www.youtube.com/channel/"+videoData['snippet']['channelId']

def comparePlaylist(id):

    updateStoredFlag = False
    toAdd = {}
    missing = {}

    global diffText

    playlist = api.get_playlist_by_id(playlist_id=id)
    name = playlist.items[0].to_dict()['snippet']['title']

    with open("./json/playlists.json", "r") as file:
        storedPlaylist = json.load(file)    
        
        if id not in storedPlaylist:
            print("\nPlaylist \""+name+"\" not previously stored, when prompted, say 'y' to update database to include it,\nand then run the program again.")
            return 

        for song in storedPlaylist[id].keys():
            #print(song)

            #Is song (From Stored) not in currentPlaylist? if not, it's ben removed.
            if song not in currentPlaylists[id] and song != "Failed to Retrieve":
                #print("\""+storedPlaylist[id][song]['Title']+"\" is missing.")
                missing[song]={}
                #print(storedPlaylist[id][song])
                missing[song]['Title'] = storedPlaylist[id][song]['Title']
                missing[song]['VideoUrl'] = storedPlaylist[id][song]['VideoUrl']
                missing[song]['ChannelUrl'] = storedPlaylist[id][song]['ChannelUrl']

        for song in currentPlaylists[id].keys():
            #Is song(From Current) not in storedPlaylist?
            if song not in storedPlaylist[id] and song != "Failed to Retrieve":
                toAdd[song] = currentPlaylists[id][song]
                updateStoredFlag = True
                #print(currentPlaylists[id][song])
                #print("New since last scan:",currentPlaylists[id][song]['Title'])

    if (updateStoredFlag):

        storedPlaylist = {}
        with open("./json/playlists.json",'r') as file:
            storedPlaylist = json.load(file)

        with open("./json/playlists.json", "w") as file:
            for song in toAdd:
                storedPlaylist[song] = toAdd[song]
                if 'ChannelUrl' not in toAdd[song].keys():
                    toAdd[song]['ChannelUrl'] = "NULL"
                if 'VideoUrl' not in toAdd[song].keys():
                    toAdd[song]['VideoUrl'] = "NULL"
                #print(currentPlaylists[id][song]['Title'],"added to database.")
            json.dump(storedPlaylist,file,indent=4)
        
    print("\nUpdates for",name+":")

    diffText+="\nUpdates for "+name+":\n"
    if len(missing)+len(toAdd) != 0:                
        for item in missing:
            if (missing[item]['Title'] == "Failed to Retrieve"):
                continue

            print("-",missing[item]['Title'],"From",missing[item]['ChannelUrl'])
            diffText+="- "+missing[item]['Title']+" From "+missing[item]['ChannelUrl']+"\n"
        for item in toAdd:
            if (toAdd[item]['Title'] == "Failed to Retrieve"):
                continue

            print("+",toAdd[item]['Title'],"From ",toAdd[item]['ChannelUrl'])
            diffText+="+ "+toAdd[item]['Title']+" From "+toAdd[item]['ChannelUrl']+"\n"
    else:
        print("No changes.")
        diffText+="No changes.\n"
        
def writeCurrentPlaylist():

    toWrite = {}

    #Remove absent data on rewriting database.
    for playlist in currentPlaylists.keys():
        #print(playlist)
        toWrite[playlist] = {} 
        for song in currentPlaylists[playlist]:
            #print(currentPlaylists[item][song])
            if not (currentPlaylists[playlist][song]['Title'] == 'Failed to Retrieve'):
              # del to[item][song]
              #print("Remove",currentPlaylists[item][song]['Title'],"?")
                toWrite[playlist][song] = currentPlaylists[playlist][song]
            #else:
                #print(currentPlaylists[playlist][song])

    with open("./json/playlists.json", "w") as file:
        json.dump(toWrite,file,indent=4)

    data = {}
    with open('./json/config.json','r') as file:
        data = json.load(file)

    data['date'] = datetime.now().strftime("%d/%m/%Y %H:%M:%S")
    with open('./json/config.json','w') as file:
        json.dump(data,file,indent=4)


print("Reading Playlists from IDs.")
playlistIds = playlistRead()

print("Reading Songs from Playlists.")
for playlist in playlistIds:
    scanPlaylist(playlist)

print("\nBackup Date: "+date+"\n")

for id in playlistIds:
    comparePlaylist(id)

with open("Diff.txt",'w') as file:
    file.write("[Scan Date: "+datetime.now().strftime("%d/%m/%Y %H:%M:%S")+"]\n[Last Backup Date: "+date+"]\n"+diffText)

print("\n\n[Your Backup Date: "+date+"]")
state = input("-----------------------------------------------------------------------------------------------------------------------\nReset latest backup playlist data? This action cannot be undone.\nNOTE: Any new songs discovered in this scan are automatically added to your backup.\n(Say 'y' the first time this program is run.) Y/N\n-----------------------------------------------------------------------------------------------------------------------\n")

if (state.lower() == 'y'):
    writeCurrentPlaylist()
    print("Rewrote playlists.")
else:
    print("Skipped writing over backup.")

input("Complete: Press Any Key To Exit")