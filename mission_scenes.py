"""Seeded, illustrative mission-control displays drawn with the shared Canvas."""
from dataclasses import dataclass
import math

import numpy as np


@dataclass
class Mission:
    scene: str
    title: str
    subtitle: str
    metric: str
    value: str
    rows: tuple
    status: str
    data: dict


def make_mission(scene, rng):
    """Create all mission state once; drawing and telemetry consume this state."""
    ident = rng.randrange(10, 100)
    if scene == 'tracking':
        altitude = rng.uniform(400, 4800)
        inclination = rng.uniform(18, 78)
        phase = rng.uniform(0, 2 * math.pi)
        radius = 6371 + altitude
        period = 2 * math.pi * math.sqrt(radius ** 3 / 398600) / 60
        stations = tuple((rng.uniform(-1.1, 1.1), rng.uniform(-.75, .75)) for _ in range(3))
        data = dict(altitude=altitude, inclination=inclination, phase=phase,
                    radius_ratio=radius / 6371, period=period, stations=stations)
        return Mission(scene, 'ORBITAL TRACKING', f'FLIGHT DYNAMICS / ODYSSEY {ident}',
                       'ORBIT ALTITUDE', f'{altitude:04.0f} KM',
                       (('INCLINATION', f'{inclination:.1f} DEG'), ('PERIOD', f'{period:.1f} MIN'),
                        ('VELOCITY', f'{math.sqrt(398600/radius):.2f} KM/S')),
                       'TRACK / ACQUIRED', data)
    if scene == 'launch':
        elapsed = rng.uniform(35, 430)
        stages = rng.choice((2, 3))
        boosters = rng.choice((0, 2))
        slenderness = rng.uniform(.8, 1.2)
        times = np.linspace(0, elapsed, 80)
        velocity = 8 * times + .012 * times ** 2
        altitude = (4 * times ** 2 + .004 * times ** 3) / 1000
        active = min(stages, 1 + int(elapsed / 170))
        data = dict(elapsed=elapsed, stages=stages, boosters=boosters,
                    slenderness=slenderness, times=tuple(times), velocity=tuple(velocity),
                    altitude=tuple(altitude), active=active)
        return Mission(scene, 'ASCENT GUIDANCE', f'LAUNCH OPERATIONS / ATLAS {ident}',
                       'MISSION ELAPSED', f'T+{elapsed:05.1f}',
                       (('ALTITUDE', f'{altitude[-1]:.1f} KM'), ('VELOCITY', f'{velocity[-1]:.0f} M/S'),
                        ('ACTIVE STAGE', f'{active:02d} / {stages:02d}')),
                       'GUIDANCE / NOMINAL', data)
    if scene == 'probe':
        panels = rng.choice((2, 3, 4))
        dish_angle = rng.uniform(-.4, .4)
        boom = rng.uniform(.25, .46)
        distance = rng.uniform(1.2, 8.5)
        power = panels * 440 / distance ** 2
        yaw = rng.uniform(-25, 25)
        data = dict(panels=panels, dish_angle=dish_angle, boom=boom,
                    distance=distance, power=power, yaw=yaw)
        return Mission(scene, 'SPACECRAFT ENGINEERING', f'DEEP SPACE / PIONEER {ident}',
                       'HELIOCENTRIC RANGE', f'{distance:.2f} AU',
                       (('ARRAY OUTPUT', f'{power:.1f} W'), ('ARRAY BANKS', f'{panels*2:02d} ONLINE'),
                        ('ATTITUDE YAW', f'{yaw:+.1f} DEG')),
                       'ATTITUDE / HOLD', data)
    if scene == 'docking':
        dx, dy = rng.uniform(-.65, .65), rng.uniform(-.65, .65)
        distance = rng.uniform(35, 900)
        closing = rng.uniform(.05, .8)
        aligned = math.hypot(dx, dy) <= .28
        data = dict(dx=dx, dy=dy, distance=distance, closing=closing, aligned=aligned)
        return Mission(scene, 'RENDEZVOUS CONTROL', f'PROXIMITY OPERATIONS / PORT {ident}',
                       'RELATIVE RANGE', f'{distance:05.1f} M',
                       (('CLOSING RATE', f'{closing:.2f} M/S'), ('LATERAL X', f'{dx*10:+.2f} M'),
                        ('LATERAL Y', f'{dy*10:+.2f} M')),
                       'CORRIDOR / ALIGNED' if aligned else 'CORRECTION / REQUIRED', data)
    if scene == 'comms':
        frequency = rng.uniform(8400, 8450)
        snr = rng.uniform(3, 26)
        azimuth, elevation = rng.uniform(15, 345), rng.uniform(20, 75)
        locked = snr >= 10
        bins = np.linspace(-1, 1, 101)
        spectrum = tuple(.09 + .025 * math.sin(float(x)*73) ** 2
                         + (snr/32) * math.exp(-float(x)**2/.004) for x in bins)
        data = dict(frequency=frequency, snr=snr, azimuth=azimuth, elevation=elevation,
                    locked=locked, bins=tuple(bins), spectrum=spectrum)
        return Mission(scene, 'DEEP SPACE NETWORK', f'RECEIVER CONTROL / STATION {ident}',
                       'DOWNLINK CARRIER', f'{frequency:.1f}',
                       (('FREQUENCY UNIT', 'MHZ / X-BAND'), ('SIGNAL / NOISE', f'{snr:.1f} DB'),
                        ('POINTING', f'{azimuth:.0f} / {elevation:.0f} DEG')),
                       'CARRIER / LOCKED' if locked else 'CARRIER / SEARCH', data)
    if scene == 'descent':
        phase = rng.choice(('BRAKING', 'APPROACH', 'FINAL'))
        bounds = {'BRAKING': (900, 1500, 22, 45), 'APPROACH': (250, 850, 7, 20),
                  'FINAL': (40, 200, 1, 5)}[phase]
        altitude, rate = rng.uniform(*bounds[:2]), rng.uniform(*bounds[2:])
        target = rng.uniform(.67, .85)
        lander_x = target - {'BRAKING': .43, 'APPROACH': .26, 'FINAL': .08}[phase]
        roughness, offset = rng.uniform(35, 80), rng.uniform(0, 6)
        data = dict(altitude=altitude, rate=rate, target=target, lander_x=lander_x,
                    roughness=roughness, offset=offset, phase=phase)
        data['ground'] = terrain_height(data, lander_x)
        data['lander_height'] = data['ground'] + altitude
        return Mission(scene, 'LUNAR DESCENT', f'LANDING GUIDANCE / SELENE {ident}',
                       'RADAR ALTITUDE', f'{altitude:04.0f} M',
                       (('DESCENT RATE', f'{rate:.1f} M/S'), ('FLIGHT PHASE', phase),
                        ('TARGET RANGE', f'{(target-lander_x)*4000:.0f} M')),
                       'RADAR / VALID', data)
    raise ValueError(f'Unknown mission scene: {scene}')


def terrain_height(data, position):
    return 100 + data['roughness'] * (.65 * math.sin(position * 17 + data['offset'])
                                      + .35 * math.cos(position * 31))


class View:
    """Aspect-preserving drawing coordinates, with compact diagram helpers."""
    def __init__(self, canvas, box, lw, aspect=1.65):
        self.c, self.lw = canvas, lw
        x, y, w, h = box
        self.w = min(w, h * aspect)
        self.h = self.w / aspect
        self.x, self.y = x + (w-self.w)/2, y + (h-self.h)/2

    def p(self, x, y):
        return self.x+x*self.w, self.y+y*self.h

    def line(self, points, v=210, weight=1):
        self.c.line([self.p(*p) for p in points], self.lw*weight, v)

    def rect(self, x, y, w, h, v=180, weight=1):
        self.line([(x,y),(x+w,y),(x+w,y+h),(x,y+h),(x,y)],v,weight)

    def circle(self, x, y, r, v=210, weight=1):
        self.c.circle(*self.p(x,y),r*self.h,self.lw*weight,v)

    def ellipse(self, x, y, rx, ry, v=180):
        self.c.ellipse(*self.p(x,y),rx*self.w,ry*self.h,self.lw*.8,v)

    def text(self, x, y, text, v=175, size=.025, anchor='la'):
        self.c.text(*self.p(x,y),text,self.h*size,v,anchor=anchor,bold=False)

    def cross(self,x,y,r=.015,v=245):
        self.line([(x-r,y),(x+r,y)],v)
        self.line([(x,y-r),(x,y+r)],v)


def orbit_point(d, phase):
    """World-space orbit in Earth-radius units, shared by orbit and marker."""
    inc = math.radians(d['inclination'])
    r = d['radius_ratio']
    return r*math.cos(phase), r*math.sin(phase)*math.cos(inc), r*math.sin(phase)*math.sin(inc)


def tracking(v, m, busy):
    d=m.data
    def proj(x,y,z):
        return .48+x*.19, .51+y*.14-z*.28
    # Wireframe Earth with a three-quarter viewing angle.
    for lat in np.linspace(-math.pi/2,math.pi/2,9)[1:-1]:
        v.line([proj(math.cos(lat)*math.cos(t), math.cos(lat)*math.sin(t), math.sin(lat))
                for t in np.linspace(0,2*math.pi,100)],100,.65)
    for lon in np.linspace(0,2*math.pi,13)[:-1]:
        v.line([proj(math.cos(t)*math.cos(lon),math.cos(t)*math.sin(lon),math.sin(t))
                for t in np.linspace(-math.pi/2,math.pi/2,70)],120,.65)
    v.line([proj(*orbit_point(d,t)) for t in np.linspace(0,2*math.pi,180)],240,1.2)
    sat=proj(*orbit_point(d,d['phase']))
    v.rect(sat[0]-.012,sat[1]-.019,.024,.038,255)
    v.line([(sat[0]-.037,sat[1]),(sat[0]+.037,sat[1])],255)
    for i,(lon,lat) in enumerate(d['stations']):
        station=proj(math.cos(lat)*math.sin(lon),-math.cos(lat)*math.cos(lon),math.sin(lat))
        v.cross(*station,.006,200)
        v.line([station,sat],100,.6)
        if busy>.45: v.text(station[0]+.014,station[1],f'GS-{i+1:02}',140,.021)
    v.text(.03,.06,'EARTH / INERTIAL REFERENCE',180)
    v.text(.03,.91,f'ORBIT RADIUS / {d["radius_ratio"]:.3f} RE',200)
    v.text(.97,.91,'NORTH +Z',130,anchor='ra')


def launch(v, m, busy):
    d=m.data
    cx=.42; half=.043*d['slenderness']; top=.18; bottom=.84
    stage_h=(bottom-top)/d['stages']
    v.line([(cx-half,top),(cx,.045),(cx+half,top)],255,1.3)
    for i in range(d['stages']):
        yy=bottom-(i+1)*stage_h
        active=i+1==d['active']
        v.rect(cx-half,yy,half*2,stage_h,245 if active else 130)
        v.line([(cx-half*.8,yy+stage_h),(cx-half*1.2,yy+stage_h+.035),
                (cx+half*1.2,yy+stage_h+.035),(cx+half*.8,yy+stage_h)],180)
        v.line([(cx+half+.02,yy+stage_h*.5),(.71,yy+stage_h*.5)],100,.6)
        v.text(.72,yy+stage_h*.5,f'S{i+1:02}'+(' / ACTIVE' if active else ' / STAGE'),210 if active else 140)
        if busy>.4:
            for k in range(1,5):
                v.line([(cx-half,yy+stage_h*k/5),(cx+half,yy+stage_h*k/5)],90,.6)
    if d['boosters']:
        for sign in (-1,1):
            bx=cx+sign*(half+.042)
            v.rect(bx-.018,.53,.036,.31,210)
            v.line([(bx-.018,.53),(bx,.46),(bx+.018,.53)],220)
    v.line([(cx,.88),(cx-.024,.96),(cx+.024,.96),(cx,.88)],230)
    v.line([(.19,.07),(.19,.86)],120,.7)
    for i in range(11):
        yy=.07+i*.079
        v.line([(.18,yy),(.20,yy)],130,.7)
    v.text(.03,.04,'VEHICLE / ELEVATION',180)
    v.text(.72,.90,f'{d["boosters"]:02} BOOSTERS',150)


def probe(v, m, busy):
    d=m.data
    def p(x,y,z): return .50+x*.36-y*.12,.58+x*.10+y*.12-z*.46
    def edge(points,value=180,weight=1): v.line([p(*q) for q in points],value,weight)
    def box(x,y,z,w,h,t):
        base=[(x,y,z),(x+w,y,z),(x+w,y+h,z),(x,y+h,z),(x,y,z)]
        roof=[(a,b,z+t) for a,b,_ in base]
        edge(base,130);edge(roof,230)
        for a,b in zip(base,roof):edge([a,b],190)
    box(-.18,-.16,-.12,.36,.32,.32)
    for sign in (-1,1):
        edge([(sign*.18,0,0),(sign*1.03,0,0)],220)
        for i in range(d['panels']):
            xx=sign*(.27+i*.19)
            box(xx if sign>0 else xx-.16,-.25,-.015,.16,.50,.03)
            if busy>.3:
                for k in range(1,4):edge([(xx,-.25+k*.125,.02),(xx+sign*.16,-.25+k*.125,.02)],110,.6)
    # Steerable parabolic reflector, as concentric projected rings and ribs.
    angle=d['dish_angle']; center=p(.05+angle*.35,0,.61)
    v.line([p(0,0,.20),center],230)
    for radius in (.15,.105,.05):
        v.ellipse(center[0],center[1],radius,radius*(.35+abs(angle)),210)
    for theta in np.linspace(0,2*math.pi,9)[:-1]:
        v.line([center,(center[0]+.15*math.cos(theta),center[1]+.15*(.35+abs(angle))*math.sin(theta))],130,.7)
    boom_end=p(-.12,.3+d['boom'],.43)
    v.line([p(-.1,.1,.15),boom_end],230)
    v.circle(*boom_end,.025,255)
    v.text(.03,.04,'SPACECRAFT / AXONOMETRIC',180)
    v.text(.03,.92,f'ARRAY BANKS {d["panels"]*2:02} / DISH STEER {math.degrees(angle):+.1f} DEG',170)


def docking(v, m, busy):
    d=m.data
    cx,cy=.50,.48
    for rx,ry in ((.13,.19),(.20,.29),(.30,.40),(.43,.46)):
        v.rect(cx-rx,cy-ry,rx*2,ry*2,110)
    for sign in (-1,1):
        for sy in (-1,1):
            v.line([(cx+sign*.13,cy+sy*.19),(cx+sign*.43,cy+sy*.46)],160,.8)
    # The receiving port and its station truss.
    v.circle(cx,cy,.17,235)
    v.circle(cx,cy,.12,150)
    v.rect(.455,.415,.09,.13,245)
    for sign in (-1,1):
        v.rect(cx+sign*.29-.065,cy-.08,.13,.16,175)
        v.line([(cx+sign*.13,cy),(cx+sign*.225,cy)],210)
        if busy>.4:
            for k in range(1,4):
                xx=cx+sign*.29-.065+k*.13/4
                v.line([(xx,cy-.08),(xx,cy+.08)],100,.65)
    v.cross(cx+d['dx']*.16,cy-d['dy']*.24,.035,255)
    v.line([(cx-.025,cy),(cx+.025,cy)],130)
    v.line([(cx,cy-.04),(cx,cy+.04)],130)
    v.text(.03,.015,'OPTICAL APPROACH / PORT AXIS',180)
    v.text(.03,.96,m.status,220)


def comms(v, m, busy):
    d=m.data
    # Side elevation: the reflector's tilt follows the reported elevation.
    angle=math.radians(d['elevation'])
    axis=np.array((math.cos(angle)/1.65,-math.sin(angle)))
    perp=np.array((math.sin(angle)/1.65,math.cos(angle)))
    center=np.array((.5,.44))
    def dish(t):
        return tuple(center+perp*t+axis*(t*t*1.5))
    v.line([dish(t) for t in np.linspace(-.30,.30,80)],245,1.4)
    feed=tuple(center+axis*.19)
    for t in (-.30,0,.30):v.line([dish(t),feed],180,.8)
    v.circle(*feed,.018,255)
    for radius in (.06,.12,.18):
        # Short wavefront arcs emitted along the same pointing vector.
        wave=np.array(feed)+axis*radius
        v.line([tuple(wave+perp*t-axis*t*t) for t in np.linspace(-.09,.09,30)],110,.7)
    v.line([(.50,.46),(.39,.86),(.61,.86),(.50,.46)],210)
    v.rect(.32,.86,.36,.055,230)
    v.circle(.50,.51,.038,230)
    if busy>.4:
        for k in range(4):
            yy=.61+k*.055
            v.line([(.46,yy),(.54,yy)],110,.7)
    v.text(.03,.04,'ANTENNA / ELEVATION',180)
    v.text(.03,.96,f'AZ {d["azimuth"]:05.1f} DEG / EL {d["elevation"]:04.1f} DEG',200)


def descent(v, m, busy):
    d=m.data
    ceiling=max(400,d['lander_height']*1.25)
    def world(x,z):return .06+x*.88,.88-z/ceiling*.74
    samples=np.linspace(0,1,150)
    surface=[world(float(x),terrain_height(d,float(x))) for x in samples]
    v.line(surface,210)
    if busy>.3:
        for x in np.linspace(.02,.98,35):
            pt=world(x,terrain_height(d,x))
            v.line([pt,(pt[0]-.012,pt[1]+.04)],90,.6)
    target=world(d['target'],terrain_height(d,d['target']))
    v.cross(*target,.025,255)
    lander=world(d['lander_x'],d['lander_height'])
    lx,ly=lander
    v.line([(lx-.025,ly-.022),(lx+.025,ly-.022),(lx+.035,ly+.014),
            (lx-.035,ly+.014),(lx-.025,ly-.022)],255)
    for sign in (-1,1):
        v.line([(lx+sign*.02,ly+.014),(lx+sign*.045,ly+.042),
                (lx+sign*.06,ly+.042)],230)
    ground=world(d['lander_x'],d['ground'])
    v.line([(lx,ly+.05),ground],140,.7)
    # Predicted descent curve ends on the marked landing target.
    for i in range(0,30,2):
        pts=[]
        for t in np.linspace(i/30,(i+1)/30,4):
            pts.append((lx+(target[0]-lx)*t,ly+(target[1]-ly)*t**.8))
        v.line(pts,150,.7)
    v.text(.03,.035,'LUNAR SURFACE / RADAR PROFILE',180)
    for k in range(4):
        yy=.88-k*.74/3
        v.line([(.025,yy),(.045,yy)],100,.7)
        v.text(.047,yy-.025,f'{ceiling*k/3:.0f}',120,.019)
    v.text(.03,.96,'HORIZONTAL SCALE / 4000 M',150)
    v.text(.97,.96,f'AGL {d["altitude"]:.0f} M',220,anchor='ra')


def plot(c, box, xs, ys, lw, label, xmax=None, ymax=None):
    """Plot with fixed/bounded scales and a marked current sample."""
    x,y,w,h=box
    xmax=xmax or max(xs) or 1
    ymax=ymax or max(ys) or 1
    c.text(x,y,label,h*.14,175,bold=False)
    # Inset the plot so its endpoint marker stays within the instrument panel.
    inset=lw*3
    x+=inset
    w-=inset*2
    top=y+h*.30; ph=h*.55
    for i in range(5):
        yy=top+ph*i/4
        c.line([(x,yy),(x+w,yy)],lw*.5,65)
    c.line([(x,top),(x,top+ph),(x+w,top+ph)],lw*.7,120)
    points=[(x+w*float(a)/xmax,top+ph*(1-float(b)/ymax)) for a,b in zip(xs,ys)]
    c.line(points,lw,225)
    c.circle(*points[-1],lw*2,lw*.7,255)


def instruments(c, box, m, lw, busy):
    x,y,w,h=box
    d=m.data
    gap=w*.065
    if m.scene=='launch':
        for i,(key,label) in enumerate((('altitude','ALTITUDE / KM'),('velocity','VELOCITY / M/S'))):
            plot(c,(x+i*(w+gap)/2,y,(w-gap)/2,h),d['times'],d[key],lw,label)
    elif m.scene=='tracking':
        # Ground track latitude follows the very same orbital phase/inclination.
        phases=np.linspace(0,2*math.pi,100)
        latitudes=[math.degrees(math.asin(orbit_point(d,t)[2]/d['radius_ratio'])) for t in phases]
        plot(c,(x,y,w*.66,h),phases,[a+90 for a in latitudes],lw,'GROUND TRACK / LATITUDE + 90',2*math.pi,180)
        c.text(x+w*.72,y,'CURRENT LAT',h*.14,150,bold=False)
        latitude=math.degrees(math.asin(orbit_point(d,d['phase'])[2]/d['radius_ratio']))
        c.text(x+w*.72,y+h*.40,f'{latitude:+.1f} DEG',h*.24,235,bold=False)
    elif m.scene=='probe':
        for i,(name,value) in enumerate((('POWER / W',d['power']),('RANGE / AU',d['distance']),('YAW / DEG',d['yaw']))):
            xx=x+w*i/3
            c.text(xx,y,name,h*.14,150,bold=False)
            c.text(xx,y+h*.36,f'{value:+.1f}' if i==2 else f'{value:.1f}',h*.27,235,bold=False)
            if busy>.3:
                level=(d['power']/1300,d['distance']/9,abs(d['yaw'])/25)[i]
                for k in range(14):
                    c.line([(xx+w*.018*k,y+h*.82),(xx+w*.018*k,y+h*.65)],lw,210 if k/14<level else 65)
    elif m.scene=='docking':
        c.text(x,y,'RELATIVE POSITION / METRES',h*.14,150,bold=False)
        cx,cy=x+w*.25,y+h*.60
        rx,ry=w*.14,h*.30
        c.ellipse(cx,cy,rx,ry,lw*.7,100)
        c.line([(cx-rx,cy),(cx+rx,cy)],lw*.7,110)
        c.line([(cx,cy-ry),(cx,cy+ry)],lw*.7,110)
        px,py=cx+d['dx']*rx,cy-d['dy']*ry
        c.circle(px,py,lw*2,lw,255)
        c.line([(cx,cy),(px,py)],lw,200)
        c.text(x+w*.55,y+h*.30,'ALIGNMENT ERROR',h*.14,150,bold=False)
        c.text(x+w*.55,y+h*.54,f'{math.hypot(d["dx"],d["dy"])*10:.2f} M',h*.25,235,bold=False)
    elif m.scene=='comms':
        plot(c,box,[a+1 for a in d['bins']],d['spectrum'],lw,'RECEIVER SPECTRUM / CARRIER CENTRED',2,1)
    elif m.scene=='descent':
        # Altitude versus remaining horizontal distance, ending at the surface.
        t=np.linspace(0,1,60)
        plot(c,(x,y,w*.66,h),t,[d['altitude']*(1-a)**.8 for a in t],lw,'PREDICTED AGL / M',1,1600)
        c.text(x+w*.72,y,'DESCENT',h*.14,150,bold=False)
        c.text(x+w*.72,y+h*.4,f'{d["rate"]:.1f} M/S',h*.24,235,bold=False)


# Registry owns both the scene's drawing and its supporting instrument renderer.
MISSION_SCENES = {
    'tracking': tracking, 'launch': launch, 'probe': probe,
    'docking': docking, 'comms': comms, 'descent': descent,
}


def compose_mission(c, W, H, rng, scene, busy=.55, wordmark=None):
    m=make_mission(scene,rng)
    lw=max(.8,min(W,H)/800)
    fs=H*.017
    mx,my=W*.055,H*.075
    right,bottom=W-mx,H*.88
    split=mx+(right-mx)*.73
    def text(x,y,s,k=1,v=180,anchor='la'):
        c.text(x,y,s,fs*k,v,anchor=anchor,bold=False)
    c.rect(mx,my,right,bottom,lw*.7,95)
    c.line([(mx,my+H*.105),(right,my+H*.105)],lw,180)
    text(mx+W*.018,my+H*.022,'MISSION SYSTEMS / '+m.title,.95)
    text(mx+W*.018,my+H*.052,m.subtitle,1.65,255)
    text(right-W*.018,my+H*.025,'REMOTE / ONLINE',.85,180,'ra')
    c.line([(split,my+H*.105),(split,bottom)],lw*.7,110)
    bx,bw=mx+W*.018,split-mx-W*.036
    main_box=(bx,H*.205,bw,H*.43)
    MISSION_SCENES[scene](View(c,main_box,lw),m,busy)
    c.line([(bx,H*.675),(bx+bw,H*.675)],lw*.7,100)
    instruments(c,(bx,H*.697,bw,H*.126),m,lw,busy)
    text(bx,H*.85,'FLIGHT RECORD / '+scene.upper()+' / ENGINEERING DISPLAY',.75,125)
    sx=split+W*.018; sw=right-sx-W*.018
    text(sx,H*.215,'01 / FLIGHT STATUS',.85,150)
    text(sx,H*.27,m.metric,.8,165)
    text(sx,H*.307,m.value,min(2.4,sw/(len(m.value)*fs*.64)),255)
    for i,(label,value) in enumerate(m.rows):
        yy=H*(.415+i*.077)
        text(sx,yy,label,.76,140)
        text(sx,yy+H*.026,value,.98,225)
    c.line([(sx,H*.675),(sx+sw,H*.675)],lw*.7,100)
    text(sx,H*.702,'02 / CONTROL STATE',.8,150)
    # Split status into two lines, leaving room on the narrower laptop panel.
    for i,line in enumerate(m.status.split(' / ')):
        text(sx,H*(.752+i*.03),line,1.05,230 if i else 160)
    if busy>.5: text(sx,H*.837,'DATA / VALID',.73,140)
    if wordmark!='none':
        text(mx,bottom+H*.023,wordmark or 'MISSION OPERATIONS DIVISION',.85,140)
    text(right,bottom+H*.023,f'REC / {rng.randrange(1000,9999)}',.85,140,'ra')
    return m
