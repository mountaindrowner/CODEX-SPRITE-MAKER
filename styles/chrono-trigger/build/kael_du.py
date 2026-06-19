W,H=32,48
LEG=[(".","transparent"),("o","outline"),("b","hair"),("l","hair_light"),
("c","hair_shadow"),("s","skin"),("a","skin_shadow"),("t","tunic"),
("g","tunic_shadow"),("r","trim"),("p","trousers"),("q","trousers_shadow"),("u","boots")]
def build(view,phase):
    g=[['.' for _ in range(W)] for _ in range(H)]
    def setp(x,y,ch):
        if 0<=x<W and 0<=y<H: g[y][x]=ch
    def rect(x0,y0,x1,y1,ch):
        for y in range(y0,y1+1):
            for x in range(x0,x1+1): setp(x,y,ch)
    def sym(x,y,ch): setp(x,y,ch); setp(W-1-x,y,ch)
    def symrect(x0,y0,x1,y1,ch):
        rect(x0,y0,x1,y1,ch); rect(W-1-x1,y0,W-1-x0,y1,ch)
    def spike(ax,ay,h,lean=0,ch='b'):
        for i in range(h):
            y=ay+i; half=i//2; cx=ax+(lean*i)//2
            for x in range(cx-half,cx+half+1): setp(x,y,ch)
    # HAIR (compact short-spiky cut, hugs the head with headroom above)
    rect(11,12,20,15,'b')                                   # snug skull cap
    spike(13,9,4); spike(16,9,4,1); spike(11,11,3,-1); spike(19,11,3,1)  # short tips
    if view=='up':
        rect(11,15,20,20,'b')                              # back of head is hair
    for x,y in [(13,9),(16,9),(12,12),(13,12),(16,11)]: setp(x,y,'l')    # top light
    rect(11,15,20,15,'c'); setp(11,14,'c'); setp(20,14,'c')             # underside shadow
    if view=='down':
        rect(12,16,19,20,'s'); symrect(11,16,11,18,'c'); rect(14,21,17,21,'s')
        rect(18,18,18,19,'a'); setp(13,20,'a')      # cheek/jaw shadow (roundness)
    else:
        rect(11,20,20,20,'c'); rect(15,21,16,21,'s')  # narrow nape (no stray pixel)
    # TUNIC
    rect(10,22,21,25,'t'); rect(11,26,20,29,'t'); symrect(9,23,9,26,'t')
    symrect(10,23,11,26,'g'); rect(11,28,20,29,'g')
    if view=='down':
        sym(13,22,'r'); sym(14,23,'r'); setp(15,23,'r'); setp(16,23,'r'); sym(12,22,'r')
    else:
        rect(12,22,19,22,'r'); rect(15,23,16,28,'g')
    rect(11,29,20,29,'r')
    # HANDS (arm swing)
    lh,rh={0:(27,27),1:(28,26),2:(26,28)}[phase]
    setp(9,lh,'s'); setp(9,lh+1,'s'); setp(22,rh,'s'); setp(22,rh+1,'s')
    # LEGS + BOOTS (pronounced stride)
    def legL(x0,x1,top,boot_top,shine=None):
        rect(x0,top,x1,boot_top-1,'p'); setp(x1,top,'q'); rect(x1,top+1,x1,boot_top-1,'q')
        rect(x0,boot_top,x1,boot_top+4,'u')
        if shine: setp(shine,boot_top+1,'r')
    if phase==0:
        legL(11,14,30,37,12); legL(17,20,30,37,19)
    elif phase==1:            # left forward(out,down), right back(in,up)
        legL(10,13,30,37,11); legL(18,20,30,35)
    else:                     # right forward, left back
        legL(11,13,30,35); legL(18,21,30,37,20)
    # OUTLINE
    solid={(x,y) for y in range(H) for x in range(W) if g[y][x]!='.'}
    out=set()
    for (x,y) in solid:
        for dx in(-1,0,1):
            for dy in(-1,0,1):
                nx,ny=x+dx,y+dy
                if 0<=nx<W and 0<=ny<H and g[ny][nx]=='.': out.add((nx,ny))
    for (x,y) in out: g[y][x]='o'
    hs={'b','l','c'}
    for (x,y) in list(out):
        nb=[g[y+dy][x+dx] for dx in(-1,0,1) for dy in(-1,0,1) if 0<=x+dx<W and 0<=y+dy<H and not(dx==0 and dy==0)]
        body=[v for v in nb if v not in('.','o')]
        if body and all(v in hs for v in body): g[y][x]='c'
    if view=='down':
        setp(13,18,'o'); setp(18,18,'o'); setp(13,17,'r'); setp(18,17,'r'); setp(16,19,'a')
    for x in range(10,22): setp(x,42,'o')
    for x in range(12,20): setp(x,43,'o')
    return g
def write(g,name):
    lines=[f"name: {name}","size: 32x48","palette: kael","legend:"]
    for ch,nm in LEG: lines.append(f"  {ch}: {nm}")
    lines.append("grid: |")
    for r in g: lines.append("  "+"".join(r))
    open(f"styles/chrono-trigger/sprites/{name}.sprite","w").write("\n".join(lines)+"\n")
for ph in (0,1,2):
    write(build('down',ph),f'kael_down_{ph}'); write(build('up',ph),f'kael_up_{ph}')
print("rebuilt down/up")
