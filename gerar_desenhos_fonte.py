from pathlib import Path
import zipfile, xml.etree.ElementTree as ET, json, math, html, csv, io, base64, unicodedata
import numpy as np
from PIL import Image, ImageDraw, ImageFont

ROOT=Path(__file__).resolve().parent
OUT=ROOT/'Desenhos_Tecnicos_Anderson'
OUT.mkdir(exist_ok=True)
SOURCE=Path(r'C:\Users\Juan Santos\Desktop\Trabalho anderson\trabalho anderson finalizado.3mf')
W,H=1400,780
FONT=Path(r'C:\Windows\Fonts\arial.ttf')
BOLD=Path(r'C:\Windows\Fonts\arialbd.ttf')
def font(size,bold=False): return ImageFont.truetype(str(BOLD if bold else FONT),size)
def fmt(x): return f'{x:.2f}'.replace('.',',')
def ascii_text(t): return unicodedata.normalize('NFKD',t).encode('ascii','ignore').decode()

class Drawing:
    def __init__(self):
        self.im=Image.new('RGB',(W,H),'white'); self.d=ImageDraw.Draw(self.im)
        self.elements=[]; self.entities=[]
    def text(self,p,t,size=23,color='#172635',anchor='la',bold=False):
        self.d.text(p,t,font=font(size,bold),fill=color,anchor=anchor)
        a='middle' if anchor[0]=='m' else ('end' if anchor[0]=='r' else 'start')
        # Pillow's ascender anchor is approximately 0.8 em above the SVG baseline.
        self.elements.append(f'<text x="{p[0]:.3f}" y="{p[1]+size*.85:.3f}" font-family="Arial,sans-serif" font-size="{size}" text-anchor="{a}" fill="{color}" font-weight="{700 if bold else 400}">{html.escape(t)}</text>')
        self.entities.append(('TEXT',p,t,size))
    def line(self,a,b,kind='visible'):
        widths={'visible':3,'hidden':2,'thin':1.3,'axis':1.4,'reference':1.2}
        colors={'visible':'#16202a','hidden':'#687480','thin':'#324e64','axis':'#597b8e','reference':'#a9b6bf'}
        patterns={'hidden':[12,7],'axis':[24,5,3,5],'reference':[2,6]}
        width=widths[kind]; color=colors[kind]; pat=patterns.get(kind)
        a=np.asarray(a,float);b=np.asarray(b,float);length=float(np.linalg.norm(b-a))
        if length<.01:return
        if pat:
            off=0.;i=0
            while off<length:
                end=min(length,off+pat[i%len(pat)])
                if i%2==0:self.d.line([tuple(a+(b-a)*off/length),tuple(a+(b-a)*end/length)],fill=color,width=max(1,round(width)))
                off=end;i+=1
        else:self.d.line([tuple(a),tuple(b)],fill=color,width=max(1,round(width)))
        dash=f' stroke-dasharray="{",".join(map(str,pat))}"' if pat else ''
        self.elements.append(f'<line x1="{a[0]:.3f}" y1="{a[1]:.3f}" x2="{b[0]:.3f}" y2="{b[1]:.3f}" stroke="{color}" stroke-width="{width}"{dash}/>')
        self.entities.append(('LINE',a,b,kind))
    def background(self,im):
        self.im.paste(im); self.d=ImageDraw.Draw(self.im)
        buf=io.BytesIO();im.save(buf,format='PNG')
        data=base64.b64encode(buf.getvalue()).decode()
        self.elements.insert(0,f'<image x="0" y="0" width="{W}" height="{H}" href="data:image/png;base64,{data}"/>')
    def dim(self,a,b,label,vertical=False):
        a=np.array(a,float);b=np.array(b,float)
        self.line(a,b,'thin')
        u=(b-a)/max(np.linalg.norm(b-a),1e-12);n=np.array([-u[1],u[0]])
        for p,d in [(a,1),(b,-1)]:
            self.line(p,p+d*u*12+n*4,'thin'); self.line(p,p+d*u*12-n*4,'thin')
        mid=(a+b)/2
        if vertical:self.text((mid[0]-12,mid[1]-13),label,22,anchor='ra')
        else:self.text((mid[0],mid[1]+8),label,22,anchor='ma')
    def save(self,path,scale):
        self.im.save(path.with_suffix('.png'),dpi=(169.333,169.333))
        svg=f'<svg xmlns="http://www.w3.org/2000/svg" width="210mm" height="117mm" viewBox="0 0 {W} {H}"><rect width="100%" height="100%" fill="white"/>'+''.join(self.elements)+'</svg>'
        path.with_suffix('.svg').write_text(svg,encoding='utf-8')
        def pair(c,v):return f'{c}\n{v}\n'
        s='0\nSECTION\n2\nHEADER\n9\n$ACADVER\n1\nAC1015\n9\n$INSUNITS\n70\n4\n0\nENDSEC\n0\nSECTION\n2\nTABLES\n'
        ltypes={'CONTINUOUS':[],'HIDDEN':[3,-1.5],'CENTER':[6,-1,0,-1],'DOTTED':[0,-1]}
        s+='0\nTABLE\n2\nLTYPE\n70\n4\n'
        for name,pat in ltypes.items():
            s+='0\nLTYPE\n2\n'+name+'\n70\n0\n3\n'+name+'\n72\n65\n73\n'+str(len(pat))+'\n40\n'+str(sum(abs(v) for v in pat))+'\n'
            for v in pat:s+='49\n'+str(v)+'\n74\n0\n'
        s+='0\nENDTAB\n0\nTABLE\n2\nLAYER\n70\n6\n'
        for name,typ,col,lw in [('VISIBLE','CONTINUOUS',7,50),('HIDDEN','HIDDEN',8,25),('THIN','CONTINUOUS',7,18),('AXIS','CENTER',4,18),('REFERENCE','DOTTED',8,13),('TEXT','CONTINUOUS',7,18)]:
            s+=f'0\nLAYER\n2\n{name}\n70\n0\n62\n{col}\n6\n{typ}\n370\n{lw}\n'
        s+='0\nENDTAB\n0\nENDSEC\n0\nSECTION\n2\nENTITIES\n'
        for e in self.entities:
            if e[0]=='LINE':
                _,a,b,k=e;s+=f'0\nLINE\n8\n{k.upper()}\n10\n{a[0]/scale}\n20\n{(H-a[1])/scale}\n30\n0\n11\n{b[0]/scale}\n21\n{(H-b[1])/scale}\n31\n0\n'
            else:
                _,p,t,sz=e;s+=f'0\nTEXT\n8\nTEXT\n10\n{p[0]/scale}\n20\n{(H-p[1]-sz)/scale}\n30\n0\n40\n{sz/scale}\n1\n{ascii_text(t)}\n'
        s+='0\nENDSEC\n0\nEOF\n';path.with_suffix('.dxf').write_text(s,encoding='ascii')

def parse():
    z=zipfile.ZipFile(SOURCE);root=ET.fromstring(z.read('3D/3dmodel.model'))
    ns={'m':root.tag.split('}')[0][1:]}; assert root.get('unit')=='millimeter'
    settings=ET.fromstring(z.read('Metadata/model_settings.config'))
    objects={o.get('id'):o for o in root.findall('m:resources/m:object',ns)}
    names={o.get('id'):o.find("metadata[@key='name']").get('value') for o in settings.findall('object')}
    piece_names=['Placa: círculo / quadrado / triângulo','Estrela','Trevo','Placa: estrela / coração','Hexágono','Placa: hexágono / trevo','Coração','Quadrado com cantos arredondados','Círculo','Pentágono','Losango','Triângulo achatado','Triângulo','Placa: losango / pentágono / triângulo']
    names={str(2*(i+1)):name for i,name in enumerate(piece_names)}
    plates={}
    for p in settings.findall('plate'):
        pid=p.find("metadata[@key='plater_id']").get('value')
        for i in p.findall('model_instance'):plates[i.find("metadata[@key='object_id']").get('value')]=pid
    for index,item in enumerate(root.findall('m:build/m:item',ns),1):
        oid=item.get('objectid');comp=objects[oid].find('m:components/m:component',ns);mid=comp.get('objectid');o=objects[mid]
        v=np.array([[float(a.get(k)) for k in ['x','y','z']] for a in o.findall('m:mesh/m:vertices/m:vertex',ns)])
        f=np.array([[int(a.get(k)) for k in ['v1','v2','v3']] for a in o.findall('m:mesh/m:triangles/m:triangle',ns)])
        A=np.array(list(map(float,item.get('transform').split()))[:9]).reshape(3,3)
        C=np.array(list(map(float,comp.get('transform').split()))[:9]).reshape(3,3)
        A=C@A
        # Left polar factor preserves all scaling/shear while removing bed rotation.
        ev,Q=np.linalg.eigh(A@A.T);stretch=(Q*np.sqrt(ev))@Q.T
        v=v@stretch
        depth_axis=1 if mid in ['1','15','17','19','23'] else 2
        if depth_axis==2:v=v[:,[0,2,1]]*np.array([1,-1,1])
        v-=(v.max(axis=0)+v.min(axis=0))/2
        # Weld coincident vertices so internal triangulation is removed reliably.
        _,idx,inv=np.unique(np.round(v,5),axis=0,return_index=True,return_inverse=True)
        v=v[idx];f=inv[f]
        normals=np.cross(v[f[:,1]]-v[f[:,0]],v[f[:,2]]-v[f[:,0]])
        norm=np.linalg.norm(normals,axis=1);good=norm>1e-9;f=f[good];normals=normals[good]/norm[good,None]
        edges={}
        for fi,tri in enumerate(f):
            for a,b in zip(tri,np.roll(tri,-1)):edges.setdefault(tuple(sorted((a,b))),[]).append(fi)
        ed=np.array(list(edges),int);adj=list(edges.values())
        # A two-degree threshold retains small chamfers but hides smooth facet seams.
        crease=np.array([len(a)!=2 or np.dot(normals[a[0]],normals[a[1]])<math.cos(math.radians(25)) for a in adj])
        yield {'id':index,'object':oid,'mesh':mid,'name':names[oid],'plate':plates[oid],'v':v,'f':f,'n':normals,'edges':ed,'adj':adj,'crease':crease,'dims':np.ptp(v,axis=0),'stretch':stretch.diagonal().tolist(),'depth_axis':depth_axis,'nonmanifold':sum(len(a)!=2 for a in adj)}

def profile_contours(p):
    edges=[e for e,a in zip(p['edges'],p['adj']) if len(a)==2 and ((p['n'][a[0],1]<-1e-7)!=(p['n'][a[1],1]<-1e-7))]
    graph={}
    for a,b in edges:graph.setdefault(a,set()).add(b);graph.setdefault(b,set()).add(a)
    groups=[]
    while graph:
        stack=[next(iter(graph))];seen=set()
        while stack:
            a=stack.pop()
            if a in seen:continue
            seen.add(a);stack.extend(graph.pop(a,set())-seen)
        q=p['v'][list(seen)][:,[0,2]]
        if min(np.ptp(q,axis=0))>20:groups.append(q)
    return groups

def circle_fit(q):
    if len(q)<40:return None
    sol=np.linalg.lstsq(np.column_stack([2*q,np.ones(len(q))]),(q*q).sum(1),rcond=None)[0]
    c=sol[:2];r=np.linalg.norm(q-c,axis=1)
    if np.ptp(r)<.025 and min(np.ptp(q,axis=0))>1.98*r.mean():return c,r.mean()
    return None

def render(piece,view,scale):
    v=piece['v'];f=piece['f'];n=piece['n']; iso=view=='ISOMETRIC'
    if view=='FRONT':B=np.array([[1,0,0],[0,0,-1],[0,1,0]])
    elif view=='SIDE':B=np.array([[0,0,1],[1,0,0],[0,1,0]])
    elif view=='TOP':B=np.array([[1,0,0],[0,1,0],[0,0,1]])
    else:
        d=np.array([1.,-1.,1.]);d/=np.linalg.norm(d);u=np.array([1.,1.,0.]);u/=np.linalg.norm(u);up=np.cross(d,u);B=np.column_stack([u,up,d])
    p=v@B;pn=n@B
    if iso:scale=min(920/np.ptp(p[:,0]),475/np.ptp(p[:,1]))
    p[:,:2]-=(p[:,:2].max(axis=0)+p[:,:2].min(axis=0))/2
    xy=p[:,:2]*[scale,-scale]+[760,355]
    zbuf=np.full((H,W),-np.inf,np.float32)
    shade=np.full((H,W),255,np.uint8)
    for fi,t in enumerate(f):
        tri=xy[t];dep=p[t,2]
        lo=np.maximum(np.floor(tri.min(axis=0)).astype(int),[0,0]);hi=np.minimum(np.ceil(tri.max(axis=0)).astype(int),[W-1,H-1])
        if np.any(hi<lo):continue
        a,b,c=tri;den=(b[1]-c[1])*(a[0]-c[0])+(c[0]-b[0])*(a[1]-c[1])
        if abs(den)<1e-7:continue
        xx,yy=np.meshgrid(np.arange(lo[0],hi[0]+1),np.arange(lo[1],hi[1]+1))
        wa=((b[1]-c[1])*(xx-c[0])+(c[0]-b[0])*(yy-c[1]))/den
        wb=((c[1]-a[1])*(xx-c[0])+(a[0]-c[0])*(yy-c[1]))/den;wc=1-wa-wb
        zz=wa*dep[0]+wb*dep[1]+wc*dep[2]
        old=zbuf[lo[1]:hi[1]+1,lo[0]:hi[0]+1]
        mask=(wa>=-1e-6)&(wb>=-1e-6)&(wc>=-1e-6)&(zz>old)
        old[mask]=zz[mask]
        if iso:shade[lo[1]:hi[1]+1,lo[0]:hi[0]+1][mask]=int(np.clip(190+50*np.dot(n[fi],[.2,-.4,.8]),135,245))
    draw=Drawing()
    if iso:
        rgb=np.stack([shade,shade,shade],axis=2);draw.background(Image.fromarray(rgb))
    xmin,ymin=xy.min(axis=0);xmax,ymax=xy.max(axis=0)
    if not iso:
        # Dotted envelope is an explicit construction reference, not a part edge.
        for a,b in [((xmin,ymin),(xmax,ymin)),((xmax,ymin),(xmax,ymax)),((xmax,ymax),(xmin,ymax)),((xmin,ymax),(xmin,ymin))]:draw.line(a,b,'reference')
    lines={'hidden':[],'visible':[]}
    for ei,(a,b) in enumerate(piece['edges']):
        adj=piece['adj'][ei]
        silhouette=len(adj)==2 and ((pn[adj[0],2]>1e-7) != (pn[adj[1],2]>1e-7))
        if not(piece['crease'][ei] or silhouette):continue
        pa,pb=xy[a],xy[b];length=np.linalg.norm(pb-pa)
        if length<.3:continue
        count=max(2,int(math.ceil(length/.65))+1);t=np.linspace(0,1,count)
        pts=pa[None,:]+t[:,None]*(pb-pa)[None,:];zs=p[a,2]+t*(p[b,2]-p[a,2])
        ix=np.clip(np.rint(pts[:,0]).astype(int),0,W-1);iy=np.clip(np.rint(pts[:,1]).astype(int),0,H-1)
        # Edge-adjacent pixels include the face that owns the edge. Taking the minimum
        # finite sample avoids declaring a silhouette hidden due to pixel rounding.
        nearby=[];boundary=np.zeros(count,dtype=bool)
        for dx,dy in [(0,0),(-1,0),(1,0),(0,-1),(0,1),(-2,0),(2,0),(0,-2),(0,2)]:
            vv=zbuf[np.clip(iy+dy,0,H-1),np.clip(ix+dx,0,W-1)]
            boundary|=~np.isfinite(vv)
            nearby.append(np.where(np.isfinite(vv),vv,np.inf))
        nearest=np.min(nearby,axis=0)
        visible=(zs>=nearest-max(.035,.07/scale))|(~np.isfinite(nearest))
        if silhouette:visible|=boundary
        changes=np.r_[0,np.where(visible[1:]!=visible[:-1])[0]+1,count]
        for st,en in zip(changes[:-1],changes[1:]):
            kind='visible' if visible[st] else 'hidden'
            if iso and kind=='hidden':continue
            start=pts[max(0,st-1)];end=pts[min(count-1,en)]
            if np.linalg.norm(end-start)>.25:lines[kind].append((start,end))
    # Draw hidden geometry first: continuous visible edges have priority.
    for k in ['hidden','visible']:
        for a,b in lines[k]:draw.line(a,b,k)
    if view=='FRONT':
        for q in profile_contours(piece):
            fit=circle_fit(q)
            if fit:
                c,r=fit;center=c*[scale,-scale]+[760,355];rad=r*scale+13
                draw.line(center-[rad,0],center+[rad,0],'axis')
                draw.line(center-[0,rad],center+[0,rad],'axis')
    titles={'FRONT':'FRONT | VISTA FRONTAL','SIDE':'SIDE | LATERAL DIREITA','TOP':'TOP | VISTA SUPERIOR','ISOMETRIC':'ISOMETRIC | ISOMÉTRICA'}
    draw.text((38,20),titles[view],29,bold=True)
    draw.text((38,60),f"P{piece['id']:02d} • {piece['name']} • medidas em mm",21)
    dims=piece['dims'];dx,dy,dz=dims
    if not iso:
        horiz,vert={'FRONT':(dx,dz),'SIDE':(dy,dz),'TOP':(dx,dy)}[view]
        for xx in [xmin,xmax]:draw.line((xx,ymax+6),(xx,650),'thin')
        draw.dim((xmin,638),(xmax,638),fmt(horiz))
        for yy in [ymin,ymax]:draw.line((xmin-6,yy),(155,yy),'thin')
        draw.dim((170,ymin),(170,ymax),fmt(vert),True)
        draw.text((38,713),{'FRONT':'Observação de -Y; plano XZ.','SIDE':'Observação de +X; plano YZ.','TOP':'Observação de +Z; plano XY.'}[view],20)
        draw.text((38,743),'Cotas totais da malha; envelope pontilhado = referência auxiliar.',18,color='#5f707d')
    else:
        draw.text((38,675),f'X = {fmt(dx)}    Y = {fmt(dy)}    Z = {fmt(dz)} mm',24,bold=True)
        draw.text((38,715),'Projeção paralela; faces sombreadas; arestas ocultas omitidas nesta vista.',19)
        org=np.array([125.,540.])
        for i,label in enumerate('XYZ'):
            end=org+B[i,:2]*[65,-65];draw.line(org,end,'thin');draw.text(end+[-7,-25],label,20,bold=True)
    return draw,scale,{'visible_segments':len(lines['visible']),'hidden_segments':len(lines['hidden'])}

def make_sheet(piece,drawings,folder):
    sheet=Image.new('RGB',(2800,1980),'white');d=ImageDraw.Draw(sheet)
    d.rectangle((22,22,2778,1958),outline='#1e3649',width=3)
    d.text((55,37),f"TRABALHO ANDERSON  /  PEÇA P{piece['id']:02d}",font=font(34,True),fill='#172635')
    d.text((55,85),f"Peça: {piece['name']}  |  objeto {piece['object']}  |  mesa {piece['plate']}",font=font(23),fill='#42596b')
    pos={'SIDE':(0,132),'FRONT':(1400,132),'ISOMETRIC':(0,912),'TOP':(1400,912)}
    for name,dr in drawings.items():sheet.paste(dr.im,pos[name])
    d=ImageDraw.Draw(sheet);d.line((40,1704,2760,1704),fill='#1e3649',width=2)
    d.text((55,1724),'LEGENDA DE LINHAS',font=font(24,True),fill='#172635')
    legend=[('Contorno visível — contínua grossa',None,3),('Aresta oculta — tracejada fina',[12,7],2),('Cota / extensão — contínua fina',None,1),('Eixo / centro — traço-ponto (quando aplicável)',[24,5,3,5],1),('Envelope auxiliar — pontilhada fina',[2,6],1)]
    for i,(label,pat,width) in enumerate(legend):
        yy=1777+i*32;off=0;ii=0
        if pat:
            while off<120:
                en=min(120,off+pat[ii%len(pat)])
                if ii%2==0:d.line((55+off,yy,55+en,yy),fill='#324e64',width=width)
                off=en;ii+=1
        else:d.line((55,yy,175,yy),fill='#172635',width=width)
        d.text((195,yy-15),label,font=font(21),fill='#172635')
    notes=[f"Dimensões X × Y × Z: {' × '.join(fmt(x) for x in piece['dims'])} mm",'1º diedro: lateral direita à esquerda; superior abaixo da frontal.', 'Formato A3 horizontal • imprimir ajustado; prevalecem as cotas.', 'Escala gráfica variável por peça; vistas ortogonais na mesma escala.', 'Reconstruído do 3MF: curvas facetadas; cotas arredondadas a 0,01 mm.', 'Material, tolerâncias, acabamento e ajustes: não especificados.', 'Cotas gerais; não constitui detalhamento completo para fabricação.']
    for i,t in enumerate(notes):d.text((1260,1727+i*32),t,font=font(20),fill='#324e64')
    sheet.save(folder/f"P{piece['id']:02d}_PRANCHA.png",dpi=(169.333,169.333))
    # SVG sheet retains editable linework and text; raster shading only in isometric.
    parts=['<svg xmlns="http://www.w3.org/2000/svg" width="420mm" height="297mm" viewBox="0 0 2800 1980"><rect width="2800" height="1980" fill="white"/>']
    parts.append(f'<text x="55" y="66" font-family="Arial" font-size="34" font-weight="bold">TRABALHO ANDERSON / PEÇA P{piece["id"]:02d}</text>')
    parts.append(f'<text x="55" y="110" font-family="Arial" font-size="23">{html.escape(piece["name"])} | objeto {piece["object"]} | mesa {piece["plate"]}</text>')
    for name,dr in drawings.items():
        x,y=pos[name];parts.append(f'<g transform="translate({x},{y})">'+''.join(dr.elements)+'</g>')
    for i,(label,pat,width) in enumerate(legend):
        y=1777+i*32;dash=f' stroke-dasharray="{",".join(map(str,pat))}"' if pat else ''
        parts.append(f'<line x1="55" y1="{y}" x2="175" y2="{y}" stroke="#172635" stroke-width="{width}"{dash}/><text x="195" y="{y+6}" font-family="Arial" font-size="21">{html.escape(label)}</text>')
    for i,t in enumerate(notes):parts.append(f'<text x="1260" y="{1746+i*32}" font-family="Arial" font-size="20">{html.escape(t)}</text>')
    parts.append('</svg>');(folder/f"P{piece['id']:02d}_PRANCHA.svg").write_text(''.join(parts),encoding='utf8')
    return sheet

def details(piece,front,folder):
    if piece['dims'][1]>10:return []
    groups=[q for q in profile_contours(piece) if max(np.ptp(q,axis=0))<150]
    groups.sort(key=lambda q:(-q.mean(0)[1],q.mean(0)[0]))
    if not groups:return []
    im=Image.new('RGB',(2500,1280),'white');im.paste(front.im,(0,110));d=ImageDraw.Draw(im)
    d.text((45,25),f"P{piece['id']:02d} / MEDIDAS DOS RECORTES",font=font(36,True),fill='#172635')
    d.text((45,78),'Valores extraídos do contorno projetado da malha; unidade: mm.',font=font(23),fill='#42596b')
    scale=min(930/max(piece['dims'][:2]),460/max(piece['dims'][1:]))
    records=[]
    for i,q in enumerate(groups,1):
        lo=q.min(0);hi=q.max(0);center=(lo+hi)/2;size=hi-lo
        p=center*[scale,-scale]+[760,465]
        d.rectangle((p[0]-27,p[1]-18,p[0]+27,p[1]+17),fill='white')
        d.text((p[0],p[1]-16),f'R{i}',font=font(24,True),fill='#075a98',anchor='ma')
        yy=175+(i-1)*215
        fit=circle_fit(q); desc=f'Diâmetro ajustado à malha: {fmt(2*fit[1])} mm' if fit else 'Largura × altura do recorte projetado'
        d.text((1420,yy),f'R{i}   {fmt(size[0])} × {fmt(size[1])} mm',font=font(29,True),fill='#172635')
        d.text((1420,yy+43),desc,font=font(22),fill='#42596b')
        d.text((1420,yy+81),f'Limite esquerdo: X = {fmt(lo[0]+85)} mm',font=font(23),fill='#172635')
        d.text((1420,yy+115),f'Limite inferior: Z = {fmt(lo[1]+85)} mm',font=font(23),fill='#172635')
        d.text((1420,yy+149),f'Centro do envelope: ({fmt(center[0]+85)}; {fmt(center[1]+85)})',font=font(22),fill='#42596b')
        records.append({'peca':f"P{piece['id']:02d}",'recorte':f'R{i}','largura_mm':float(size[0]),'altura_mm':float(size[1]),'X_esquerda_mm':float(lo[0]+85),'Z_inferior_mm':float(lo[1]+85),'diametro_ajustado_mm':float(2*fit[1]) if fit else None})
    notes=['Referencial dos recortes: X = 0 na extrema esquerda e Z = 0 na extrema inferior da placa (envelope de 170 × 170 mm).',
           'Os valores descrevem o contorno da abertura na projeção frontal; arredondamentos de borda podem alterar a boca da abertura.',
           'Os centros listados são centros dos envelopes, não necessariamente centros geométricos ou eixos de simetria.',
           'Espessura total: '+fmt(piece['dims'][1])+' mm. Para conferir mais casas decimais, consulte medidas_dos_recortes.csv.',
           'Perfis livres e recortes não circulares: a largura e a altura não substituem o perfil vetorial fornecido.',
           'Encaixes periféricos, raios e chanfros permanecem representados no desenho, sem cotagem individual completa.']
    for i,t in enumerate(notes):d.text((45,950+i*44),t,font=font(23),fill='#324e64')
    im.save(folder/f"P{piece['id']:02d}_DETALHES_RECORTES.png",dpi=(180,180))
    return records

def main():
    rows=[];thumbs=[];qa=[];recortes=[]
    for piece in parse():
        folder=OUT/f"P{piece['id']:02d}_objeto_{piece['object']}";folder.mkdir(exist_ok=True)
        dx,dy,dz=piece['dims'];scale=min(930/max(dx,dy),460/max(dy,dz))
        drawings={};views={}
        for view in ['FRONT','SIDE','TOP','ISOMETRIC']:
            dr,s,counts=render(piece,view,scale);dr.save(folder/f"P{piece['id']:02d}_{view}",s)
            drawings[view]=dr;views[view]=counts
        sheet=make_sheet(piece,drawings,folder)
        recortes.extend(details(piece,drawings['FRONT'],folder))
        thumb=drawings['FRONT'].im.copy();thumb.thumbnail((700,390));thumbs.append(thumb)
        row={'peca':f"P{piece['id']:02d}",'objeto_3mf':piece['object'],'malha_3mf':piece['mesh'],'nome_original':piece['name'],'mesa':piece['plate'],'X_mm':round(dx,5),'Y_mm':round(dy,5),'Z_mm':round(dz,5),'triangulos':len(piece['f']),'escala_X_original':piece['stretch'][0],'escala_Y_original':piece['stretch'][1],'escala_Z_original':piece['stretch'][2],'eixo_profundidade_original':'XYZ'[piece['depth_axis']],'pasta':folder.name}
        rows.append(row);qa.append({'peca':row['peca'],'arestas_nao_manifold':piece['nonmanifold'],'vistas':views})
        print(json.dumps(row,ensure_ascii=False),flush=True)
    (OUT/'inventario.json').write_text(json.dumps(rows,ensure_ascii=False,indent=2),encoding='utf8')
    if recortes:
        with (OUT/'medidas_dos_recortes.csv').open('w',newline='',encoding='utf-8-sig') as f:
            writer=csv.DictWriter(f,fieldnames=list(recortes[0]),delimiter=';');writer.writeheader();writer.writerows(recortes)
    (OUT/'verificacao.json').write_text(json.dumps(qa,ensure_ascii=False,indent=2),encoding='utf8')
    with (OUT/'medidas_das_pecas.csv').open('w',newline='',encoding='utf-8-sig') as f:
        writer=csv.DictWriter(f,fieldnames=list(rows[0]),delimiter=';');writer.writeheader();writer.writerows(rows)
    contact=Image.new('RGB',(2800,1560),'#e5ebef')
    for i,im in enumerate(thumbs):contact.paste(im,((i%4)*700,(i//4)*390))
    contact.save(OUT/'CATALOGO_PECAS.png')
    css='body{font:16px Arial;background:#eef2f5;color:#193047;margin:32px}main{max-width:1400px;margin:auto}article{background:white;padding:24px;margin:24px 0;border-radius:10px}img{max-width:100%}a{color:#075a98}table{border-collapse:collapse;width:100%}td,th{padding:10px;text-align:left;border-bottom:1px solid #ddd}.links{display:flex;gap:20px;flex-wrap:wrap}@media print{body{background:white;margin:0}article{break-before:page;padding:0}.links{display:none}}'
    page=['<!doctype html><html lang="pt-BR"><meta charset="utf-8"><title>Trabalho Anderson — Desenhos técnicos</title><style>'+css+'</style><main><h1>Trabalho Anderson</h1><p>14 peças · 56 vistas · medidas em milímetros · fonte: trabalho anderson finalizado.3mf</p><p>Abra cada prancha para ver as quatro vistas. PNG: imagem; SVG: desenho vetorial; DXF: linhas e textos editáveis em CAD.</p><p>As escalas do projeto foram aplicadas. A rotação de impressão foi removida para orientar as peças. FRONT mostra o perfil principal; Y corresponde à profundidade. As placas de mesmo nome são objetos distintos e têm pranchas separadas.</p><p>Contínua grossa: contorno visível. Tracejada fina: aresta oculta. Contínua fina: cotas e extensões. Pontilhada: envelope auxiliar de cotagem. Traço-ponto: eixos/centros, somente quando identificados; não confundir com pontilhada.</p><p>As cotas indicam as dimensões totais da malha, arredondadas a 0,01 mm. A precisão exibida não constitui tolerância de fabricação. O 3MF não contém desenhos paramétricos nem especificações de tolerância, material ou acabamento. Os desenhos não incluem cotagem completa de cada recorte/raio e não devem ser usados como detalhamento final de fabricação.</p><p>Referência geral para convenções de linhas: <a href="https://www.iso.org/standard/83355.html">ISO 128-2:2022</a>. Não se declara certificação ou conformidade integral.</p><p><a href="medidas_das_pecas.csv">Tabela de medidas (CSV)</a> · <a href="CATALOGO_PECAS.png">Catálogo visual</a></p><table><tr><th>Peça / objeto</th><th>Nome no projeto</th><th>X × Y × Z (mm)</th><th>Mesa</th></tr>']
    for r in rows:page.append(f'<tr><td><a href="#{r["peca"]}">{r["peca"]} / {r["objeto_3mf"]}</a></td><td>{html.escape(r["nome_original"])}</td><td>{fmt(r["X_mm"])} × {fmt(r["Y_mm"])} × {fmt(r["Z_mm"])}</td><td>{r["mesa"]}</td></tr>')
    page.append('</table>')
    for r in rows:
        stem=f'{r["pasta"]}/{r["peca"]}';page.append(f'<article id="{r["peca"]}"><h2>{r["peca"]} — objeto {r["objeto_3mf"]}</h2><p>{html.escape(r["nome_original"])}</p><a href="{stem}_PRANCHA.png"><img loading="lazy" src="{stem}_PRANCHA.png"></a><p><a href="{stem}_PRANCHA.svg">Prancha vetorial SVG</a></p><div class="links">')
        for view in ['ISOMETRIC','FRONT','SIDE','TOP']:page.append(f'<span>{view}: '+ ' · '.join(f'<a href="{stem}_{view}.{ext}">{ext.upper()}</a>' for ext in ['png','svg','dxf'])+'</span>')
        if (OUT/f'{stem}_DETALHES_RECORTES.png').exists():page.append(f'<span><a href="{stem}_DETALHES_RECORTES.png">Medidas e posições dos recortes</a></span>')
        page.append('</div></article>')
    page.append('</main></html>');(OUT/'ABRIR_CATALOGO.html').write_text(''.join(page),encoding='utf8')
    (OUT/'LEIA-ME.txt').write_text('TRABALHO ANDERSON - DESENHOS TECNICOS\n\nAbra ABRIR_CATALOGO.html no navegador.\n14 pastas de pecas, 4 vistas por peca em PNG, SVG e DXF, e prancha PNG/SVG.\nOs DXF contem linhas e textos, com geometria das vistas ortogonais em mm (1:1); cotas explodidas, nao associativas. A isometrica DXF e uma projecao 2D.\nPranchas SVG: A3 horizontal, 1o diedro. PNG: 2800 x 1980 pixels. Escala de apresentacao variavel; prevalecem cotas numericas.\n\nUnidade do 3MF: milimetro. Todas as escalas de instancia foram aplicadas. Rotacao/translacao da mesa removidas. Y foi escolhido como eixo de profundidade.\nOs nomes dos objetos foram preservados no inventario; nomes iguais ou sufixos 2x nao foram interpretados como quantidade. Cada instancia do build recebeu uma prancha.\n\nLinhas: continua grossa = contorno visivel; tracejada fina = aresta oculta; continua fina = cotas e extensoes; pontilhada = envelope auxiliar; traco-ponto = eixo/centro quando geometricamente identificado (nao aplicado como falsa simetria).\nA malha triangulada foi projetada ortograficamente com teste de profundidade para visibilidade. Curvas continuam facetadas. Isometrica sem arestas ocultas.\n\nCotas gerais de envelope, arredondadas a 0,01 mm; nao sao tolerancias. Nao ha cotagem individual completa de furos, recortes, raios ou encaixes. Material, acabamento e tolerancias de fabricacao nao especificados. Uso academico de representacao; detalhamento de fabricacao exige modelo CAD parametrico ou levantamento complementar.\nReferencia geral de linhas: https://www.iso.org/standard/83355.html\n',encoding='utf8')

if __name__=='__main__':main()
