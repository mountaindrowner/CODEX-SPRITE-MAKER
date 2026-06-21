W,H=32,48
LEG=[(".","transparent"),("o","outline"),("b","hair"),("l","hair_light"),
("c","hair_shadow"),("s","skin"),("a","skin_shadow"),("t","tunic"),
("g","tunic_shadow"),("r","trim"),("p","trousers"),("q","trousers_shadow"),("u","boots")]
def build_left(phase):
    g=[['.' for _ in range(W)] for _ in range(H)]
    def setp(x,y,ch):
        if 0<=x<W and 0<=y<H: g[y][x]=ch
    def rect(x0,y0,x1,y1,ch):
        for y in range(y0,y1+1):
            for x in range(x0,x1+1): setp(x,y,ch)
    def row(y,x0,x1,ch): rect(x0,y,x1,y,ch)
    # HAIR (compact short-spiky cut, profile facing left)
    rect(10,12,17,15,'b')                                              # snug skull cap (front->back)
    rect(12,9,13,11,'b'); rect(14,10,16,11,'b'); rect(10,11,11,12,'b')  # short top spikes
    setp(16,12,'b'); setp(17,13,'b')                                   # small back tuft
    for x,y in [(12,9),(11,12),(12,12),(15,10)]: setp(x,y,'l')          # top/front light
    row(15,11,16,'c'); setp(17,14,'c')                                  # underside shadow
    # FACE
    rect(10,16,15,20,'s'); setp(10,17,'s'); setp(9,18,'s')
    setp(12,17,'o'); setp(12,16,'r'); setp(11,19,'a'); setp(12,19,'a'); rect(16,16,16,17,'c')
    setp(14,19,'a')                                           # jaw shadow
    rect(14,21,16,21,'s')
    # TUNIC (narrow profile)
    rect(12,22,17,29,'t'); rect(11,23,11,27,'t'); setp(11,27,'s'); setp(11,28,'s')
    rect(17,22,17,28,'g'); rect(12,28,17,29,'g'); rect(13,21,15,21,'r')
    rect(12,29,17,29,'r'); setp(13,22,'r')
    # LEGS + BOOTS (pronounced fore/aft stride) + trouser shadow
    def legp(x0,x1,top,boot_top,toe0,toe1,shine=None):
        rect(x0,top,x1,boot_top-1,'p'); rect(x1,top+1,x1,boot_top-1,'q')
        rect(toe0,boot_top,toe1,boot_top+4,'u')
        if shine: setp(shine,boot_top+1,'r')
    if phase==0:
        legp(12,14,30,37,11,15,12); legp(15,17,30,37,15,18)
    elif phase==1:            # front(left) leg forward, rear leg back+up
        legp(11,13,30,37,9,13,10); legp(16,17,30,35,16,18)
    else:                     # rear(right) leg forward, front leg trails+up
        legp(12,13,30,35,11,13); legp(15,17,30,37,14,18,16)
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
    for x in range(10,20): setp(x,42,'o')
    for x in range(12,18): setp(x,43,'o')
    return g
def write(g,name):
    lines=[f"name: {name}","size: 32x48","palette: kael","legend:"]
    for ch,nm in LEG: lines.append(f"  {ch}: {nm}")
    lines.append("grid: |")
    for r in g: lines.append("  "+"".join(r))
    open(f"styles/chrono-trigger/sprites/{name}.sprite","w").write("\n".join(lines)+"\n")
for ph in (0,1,2): write(build_left(ph),f'kael_left_{ph}')
print("rebuilt left 0,1,2")
