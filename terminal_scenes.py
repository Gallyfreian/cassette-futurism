"""Purpose-built monochrome terminal compositions; no external image assets."""
import math
import numpy as np

from mission_scenes import MISSION_SCENES, compose_mission

SCENES = ('ship', 'archive', 'survey', *MISSION_SCENES)


def ship(c, b, rng, lw):
    """Axonometric service tug with pressure hull, tanks and radiator ribs."""
    x, y, w, h = b
    fitted=min(w,h*1.8)
    x+=(w-fitted)/2
    w=fitted
    def p(a, d, z):
        return x + w * (.48 + .42*a - .24*d), y + h * (.55 + .20*a + .21*d - .62*z)
    def edge(points, v=220, weight=1):
        c.line([p(*q) for q in points], lw*weight, v)
    def box(a, d, z, aa, dd, zz, v=200):
        bottom = [(a,d,z),(aa,d,z),(aa,dd,z),(a,dd,z),(a,d,z)]
        top = [(q[0],q[1],zz) for q in bottom]
        edge(bottom,v,.7); edge(top,v)
        for low, high in zip(bottom[:4],top[:4]): edge([low,high],v,.8)
    box(-.62,-.30,-.15,.55,.30,.28)
    box(-.26,-.26,.28,.16,.26,.58,245)
    box(.55,-.22,-.08,.83,.22,.19,245)
    # cockpit windows, exposed structural ribs and twin engine pods
    for d in [-.19,-.04,.11]: box(.65,d,.19,.79,d+.08,.25,150)
    for a in np.linspace(-.59,.51,rng.choice((8,10,12))):
        edge([(a,-.30,-.15),(a,-.30,.28),(a,.30,.28),(a,.30,-.15)],125,.6)
    for d in [-.53,.37]:
        box(-.76,d,-.23,-.18,d+.16,.06,235)
        for a in np.linspace(-.74,-.21,8):
            edge([(a,d,-.23),(a,d,.06),(a,d+.16,.06)],155,.65)
        box(-.25,d+.055,-.06,.26,d+.105,.015,130)
    # antenna mast and cargo truss
    edge([(-.05,0,.58),(-.05,0,.88)],255)
    edge([(-.28,0,.83),(.18,0,.83)],180)
    for a in np.linspace(-.56,.45,7):
        edge([(a,.32,-.15),(a+.12,.32,.26)],120,.6)
    for point, label, dx, dy in [((-.55,-.45,0),'02 / ION DRIVE',-.16,.19),
                                ((.12,0,.56),'01 / PRESSURE HULL',.08,-.20),
                                ((.75,0,.1),'03 / OPTICAL ARRAY',.04,.20)]:
        px,py=p(*point); ex,ey=px+w*dx,py+h*dy
        c.circle(px,py,lw*2,lw*.6,230)
        c.line([(px,py),(ex,ey),(ex+w*.08,ey)],lw*.6,140)
        c.text(ex,ey-h*.025,label,h*.025,180,anchor='ls')


def archive(c, b, rng, lw):
    """Front elevation of a reel transport, with mechanical detail."""
    x,y,w,h=b
    s=min(w/1.35,h); ox=x+(w-s*1.35)/2; oy=y+(h-s)/2
    def rect(a,d,aa,dd,v=200): c.rect(ox+s*a,oy+s*d,ox+s*aa,oy+s*dd,lw,v)
    rect(.03,.03,1.32,.97); rect(.06,.06,1.29,.73,120)
    for cx,phase in [(.38,rng.uniform(0,1)),(.97,rng.uniform(0,1))]:
        xx,yy=ox+s*cx,oy+s*.36
        for r,v in [(.253,230),(.231,110),(.165,130),(.073,235),(.027,235)]:
            c.circle(xx,yy,s*r,lw*.8,v)
        for k in range(6):
            a=k*math.pi/3+phase
            c.line([(xx+s*.085*math.cos(a),yy+s*.085*math.sin(a)),
                    (xx+s*.213*math.cos(a),yy+s*.213*math.sin(a))],lw*1.8,195)
    c.line([(ox+s*.38,oy+s*.61),(ox+s*.53,oy+s*.68),
            (ox+s*.82,oy+s*.68),(ox+s*.97,oy+s*.61)],lw*1.3,255)
    rect(.58,.59,.77,.72,240)
    for a in [.10,.18,1.17,1.25]:
        for d in [.1,.92]: c.circle(ox+s*a,oy+s*d,s*.009,lw*.6,155)
    for i in range(5): rect(.13+i*.135,.80,.23+i*.135,.89,210 if i==2 else 115)
    rect(.91,.79,1.22,.90,175)
    c.text(ox+s*1.065,oy+s*.845,'IPS  15',s*.027,230,anchor='mm')
    for k in range(16):
        a=.16+k*.061
        c.line([(ox+s*a,oy+s*.95),(ox+s*(a+.028),oy+s*.95)],lw*.65,120)


def survey(c, b, rng, lw):
    """Connected sampled terrain, with shared heights along both grid axes."""
    x,y,w,h=b
    fitted=min(w,h*2.0)
    x+=(w-fitted)/2
    w=fitted
    peaks=[(rng.uniform(-.65,.65),rng.uniform(-.6,.6),rng.uniform(.12,.32)) for _ in range(5)]
    def p(a,d):
        z=sum(v*math.exp(-((a-px)**2+(d-py)**2)/.13) for px,py,v in peaks)
        z+=.018*math.sin(a*17+d*8)
        return x+w*(.5+.25*a-.21*d),y+h*(.53+.15*a+.16*d-z*.65)
    grid=np.linspace(-1,1,29)
    for d in grid: c.line([p(a,d) for a in grid],lw*.65,155)
    for a in grid: c.line([p(a,d) for d in grid],lw*.65,195)
    outline=[p(-1,-1),p(1,-1),p(1,1),p(-1,1),p(-1,-1)]
    c.line(outline,lw,240)
    for px,py,v in peaks[:3]:
        xx,yy=p(px,py)
        c.line([(xx,yy-h*.13),(xx,yy)],lw*.7,200)
        c.circle(xx,yy-h*.13,lw*2,lw*.7,255)
    c.text(x+w*.5,y+h*.88,'SECTOR 07 / ELEVATION MESH / 29 x 29',h*.027,170,anchor='mm')


DRAW = {'ship': ship, 'archive': archive, 'survey': survey}
TITLES = {'ship': ('VEHICLE INSPECTION','SERVICE TUG / MK. IV','HULL INTEGRITY','98.4 %'),
          'archive': ('MAGNETIC ARCHIVE','TRANSPORT / DECK 02','TAPE REMAINING','084 MIN'),
          'survey': ('SURFACE TELEMETRY','TOPOGRAPHIC SURVEY','ALTITUDE ASL','2408 M')}


def compose_terminal(c, W, H, rng, scene='ship', busy=.55, wordmark=None):
    if scene == 'auto': scene=rng.choice(SCENES)
    if scene in MISSION_SCENES:
        return compose_mission(c, W, H, rng, scene, busy, wordmark)
    title,sub,metric,value=TITLES[scene]
    lw=max(.8,min(W,H)/800)
    mx,my=W*.055,H*.075
    right,bottom=W-mx,H*.88   # reserve menu bar and Dock margins
    fs=min(H*.020,W*.018)
    def text(x,y,s,k=1,v=185,anchor='la'):
        c.text(x,y,s,fs*k,v,anchor=anchor,bold=False)
    c.rect(mx,my,right,bottom,lw*.7,95)
    c.line([(mx,my+H*.105),(right,my+H*.105)],lw,180)
    text(mx+W*.018,my+H*.021,'SYSTEM / 04     '+title,.9,180)
    text(mx+W*.018,my+H*.050,sub,1.65,255)
    text(right-W*.018,my+H*.025,'ONLINE / LOCAL',.85,210,'ra')
    split=mx+(right-mx)*.73
    c.line([(split,my+H*.105),(split,bottom)],lw*.7,100)
    bx,by,bw,bh=mx+W*.015,my+H*.14,split-mx-W*.03,H*.50
    # faint datum marks provide structure without competing with the object
    for i in range(17):
        xx=bx+bw*i/16
        c.line([(xx,by),(xx,by+H*.006)],lw*.5,90)
    DRAW[scene](c,(bx,by,bw,bh),rng,lw)
    text(bx,bottom-H*.09,'FIG. 0'+str(SCENES.index(scene)+1)+' / '+scene.upper()+' DIAGNOSTIC',.85,150)
    text(bx,bottom-H*.055,'ORTHOGRAPHIC RECORD  /  REV. 06',.72,120)
    sx=split+W*.018; sw=right-sx-W*.018
    text(sx,by,'01 / STATUS',.8,160)
    text(sx,by+H*.052,metric,.78,170)
    # fit long numeric readouts even on a laptop aspect ratio
    text(sx,by+H*.081,value,min(2.4,sw/(len(value)*fs*.64)),255)
    rows={'ship':[('PRESSURE','101.3 KPA'),('O2 RESERVE','86.2 %'),('REACTOR','STANDBY')],
          'archive':[('REEL','A-0048'),('TRACKS','08 / SYNC'),('CHECKSUM','VERIFIED')],
          'survey':[('GRID','07-N / 42-E'),('RETURN','94.7 %'),('DATUM','LOCAL / M')]}[scene]
    for i,(label,val) in enumerate(rows):
        yy=by+H*(.18+i*.065)
        text(sx,yy,label,.70,130)
        text(sx,yy+H*.023,val,.88,220)
    yy=by+H*.405
    c.line([(sx,yy),(sx+sw,yy)],lw*.7,110)
    text(sx,yy+H*.020,'02 / SIGNAL RETURN',.72,150)
    n=32
    for i in range(n):
        a=i/(n-1)
        amp=.15+.7*abs(math.sin(a*8.2)*math.cos(a*3.1))
        c.line([(sx+sw*a,yy+H*.12),(sx+sw*a,yy+H*(.12-.055*amp))],lw,180)
    if busy > .25:
        text(sx,yy+H*.145,'LOCKED  /  NO FAULT',.72,180)
    footer=wordmark if wordmark and wordmark != 'none' else 'REMOTE SYSTEMS DIVISION'
    if wordmark != 'none': text(mx,bottom+H*.023,footer,.8,140)
    text(right,bottom+H*.023,'REC / '+str(rng.randrange(1000,9999)),.8,140,'ra')
