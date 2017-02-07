NAME = "Democracy Now"
PREFIX = '/video/democracynow'
BASE_URL = "https://www.democracynow.org"
SHOWS = "https://www.democracynow.org/shows"

ICON = 'icon-default.png'
ART = 'art-default.jpg'

####################################################################################################
def Start():

    ObjectContainer.title1 = NAME
    ObjectContainer.art = R(ART)
    DirectoryObject.thumb = R(ICON)
    HTTP.CacheTime = CACHE_1HOUR
    HTTP.Headers['User-Agent'] = 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_10_1) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/39.0.2171.95 Safari/537.36'

####################################################################################################
@handler(PREFIX, NAME, thumb=ICON, art=ART)
def MainMenu():

    oc = ObjectContainer()
    oc.add(DirectoryObject(key=Callback(Archive, title='Daily Shows'), title='Daily Shows'))
    oc.add(DirectoryObject(key=Callback(Videos, title='Web Exclusive', url='/categories/web_exclusive'), title='Web Exclusive'))
    return oc

####################################################################################################
@route(PREFIX + '/archive')
def Archive(title, form_field='year', url=''):

    oc = ObjectContainer(title2=title)
    html = HTML.ElementFromURL(SHOWS)

    for item in html.xpath('//form/select[@id="%s"]/option' %form_field):

        field_value = item.xpath('./@value')[0]
        field_title = item.xpath('./text()')[0]
        if 'Select' in field_title:
            continue
        if form_field=='year':
            field_url = '/shows/%s' %field_value
            oc.add(DirectoryObject(key = Callback(Archive, url=field_url, form_field='month', title='%s Shows' %field_title), title='%s Shows' %field_title))
        else:
            field_url = '%s/%s' %(url, field_value)
            oc.add(DirectoryObject(key = Callback(Episodes, url=field_url, title='%s %s' %(field_title, title)), title='%s %s' %(field_title, title)))

    if len(oc) < 1:
        Log ('still no value for objects')
        return ObjectContainer(header="Empty", message="There are no shows for this section." )
    else:
        return oc

####################################################################################################
@route(PREFIX + '/episodes')
def Episodes(title, url):

    oc = ObjectContainer(title2=title)
    html = HTML.ElementFromURL(BASE_URL + url)

    for item in html.xpath('//div[@class="show_preview"]'):

        url = item.xpath('.//a[contains(@data-ga-action, "Full Show")]/@href')[0]
        url = BASE_URL + url
        vid_title = item.xpath('.//h5/text()')[0]
        thumb = item.xpath('.//div[@class="media image"]/img/@src')[0]

        oc.add(
            CreateVideoClipObject(
                title = vid_title,
                url = url,
                thumb = thumb
            )
        )

    next_page = html.xpath('//button[@id="load_more"]/@data-url')
    if len(next_page) > 0:
        oc.add(NextPageObject(key=Callback(Episodes, title=title, url=next_page[0]),
            title =  L("Next Page ...")
        ))
    
    if len(oc) < 1:
        Log ('still no value for objects')
        return ObjectContainer(header="Empty", message="There are no shows for this listing." )
    else:
        return oc

####################################################################################################
@route(PREFIX + '/videos')
def Videos(url, title):

    oc = ObjectContainer(title2=title)
    html = HTML.ElementFromURL(BASE_URL + url)

    for item in html.xpath('//div[contains(@class, "primary_content")]/div[contains(@class, "news_item")]'):

        try: video_test = item.xpath('.//div[@class="play"]')[0]
        except: continue
        url = item.xpath('.//h3/a/@href')[0]
        url = BASE_URL + url
        vid_title = item.xpath('.//h3//text()')[0]
        thumb = item.xpath('./a/img/@src')[0]

        oc.add(
            CreateVideoClipObject(
                title = vid_title,
                url = url,
                thumb = thumb
            )
        )

    next_page = html.xpath('//span[@class="page"]/a[@rel="next"]/@href')
    if len(next_page) > 0:
        oc.add(NextPageObject(key=Callback(Videos, title=title, url=next_page[0]),
            title =  L("Next Page ...")
        ))
    
    if len(oc) < 1:
        Log ('still no value for objects')
        return ObjectContainer(header="Empty", message="There are no videos for this listing." )
    else:
        return oc

####################################################################################################
@route(PREFIX + '/createvideoclipobject', include_container=bool)
def CreateVideoClipObject(url, title, thumb, include_container=False, **kwargs):

    videoclip_obj = VideoClipObject(
        key = Callback(CreateVideoClipObject, url=url, title=title, thumb=thumb, include_container=True),
        rating_key = url,
        title = title,
        thumb = Resource.ContentsOfURLWithFallback(url=thumb),
        items = [
            MediaObject(
                parts = [
                    PartObject(key=Callback(PlayVideo, url=url, resolution=resolution))
                ],
                container = Container.MP4,
                video_codec = VideoCodec.H264,
                audio_codec = AudioCodec.AAC,
                audio_channels = 2,
                video_resolution = resolution
            ) for resolution in [480, 360]
        ]
    )

    if include_container:
        return ObjectContainer(objects=[videoclip_obj])
    else:
        return videoclip_obj

####################################################################################################
@route(PREFIX + '/playvideo', resolution=int)
@indirect
def PlayVideo(url, resolution):

    try:
        json_data = HTML.ElementFromURL(url).xpath('//div[@class="media_player"]/script/text()')[0]
        json = JSON.ObjectFromString(json_data)
    except:
        raise Ex.MediaNotAvailable
    if resolution==460:
        video_url = json['high_res_video']
    else:
        video_url = json['video']

    return IndirectResponse(VideoClipObject, key=video_url)
