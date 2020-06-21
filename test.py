import discodo

AudioFifo = discodo.AudioFifo()
Loader = discodo.Loader('https://r7---sn-ab02a0nfpgxapox-jwwk.googlevideo.com/videoplayback?expire=1592732951&ei=t9juXsbNNo7g4gKf-paYDQ&ip=182.209.5.10&id=o-AFU3CUsMYWeadEFtZe6HyhBnMWnsYjp8X5guJArhCwJ6&itag=251&source=youtube&requiressl=yes&mh=8q&mm=31%2C26&mn=sn-ab02a0nfpgxapox-jwwk%2Csn-npoeenll&ms=au%2Conr&mv=m&mvi=6&pcm2cms=yes&pl=24&usequic=no&initcwndbps=2771250&vprv=1&mime=audio%2Fwebm&gir=yes&clen=5176245&dur=290.261&lmt=1577178022320736&mt=1592711248&fvip=3&keepalive=yes&c=WEB&txp=5531432&sparams=expire%2Cei%2Cip%2Cid%2Citag%2Csource%2Crequiressl%2Cvprv%2Cmime%2Cgir%2Cclen%2Cdur%2Clmt&sig=AOq0QJ8wRAIgTEI9UUxYHHOHou1paTvG3E_0EnBAhLN5pFcigEyJ_u8CIDXuoqJ1aaBKqRwiqJi-YLS5UwGHAL3IXuGIICrIEOmp&lsparams=mh%2Cmm%2Cmn%2Cms%2Cmv%2Cmvi%2Cpcm2cms%2Cpl%2Cusequic%2Cinitcwndbps&lsig=AG3C_xAwRAIge4_aFAernIdSj_Cy7RquIwfwT0M608okz5BUqHjX0z4CIGqvJspU5wDD1Tu2qxSYu9rSSVGOqaPb-62sHZlNBY9u&ratebypass=yes', AudioFifo)
Loader.start()

while True:
    print(AudioFifo.read())