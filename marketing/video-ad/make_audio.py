import numpy as np, wave, sys
SR=44100; DUR=30.0; n=int(SR*DUR); t=np.arange(n)/SR
mix=np.zeros(n)
def add(sig, at, gain=1.0):
    i=int(at*SR); j=min(n,i+len(sig)); mix[i:j]+=sig[:j-i]*gain
bpm=112; beat=60/bpm
# kick
kt=np.arange(int(0.35*SR))/SR
kick=np.sin(2*np.pi*(45*kt+60*(1-np.exp(-kt*30))/30*1.0)*1)*np.exp(-kt*9)
kick=np.sin(2*np.pi*np.cumsum(50+90*np.exp(-kt*25))/SR)*np.exp(-kt*8)
rng=np.random.default_rng(1)
ht=np.arange(int(0.06*SR))/SR
hat=rng.standard_normal(len(ht))*np.exp(-ht*70); hat=np.diff(hat,prepend=0)
# tabla-ish "dha" tone
tt=np.arange(int(0.25*SR))/SR
tabla=(np.sin(2*np.pi*np.cumsum(220+160*np.exp(-tt*40))/SR))*np.exp(-tt*14)
k=0
while k*beat < DUR-1.0:
    at=k*beat
    if at>3.0 or k%2==0: add(kick,at,0.55)
    add(hat,at+beat/2,0.12)
    if k%4 in (1,3): add(tabla,at+beat*0.75,0.18)
    k+=1
# chord pad C G Am F (2 bars each)
def note(f,dur):
    tt=np.arange(int(dur*SR))/SR
    env=np.minimum(1,tt/0.05)*np.exp(-tt*0.8)
    s=sum(np.sin(2*np.pi*f*h*tt)/h**1.3 for h in range(1,5))
    return s*env
chords=[[261.6,329.6,392.0],[196.0,246.9,293.7],[220.0,261.6,329.6],[174.6,220.0,261.6]]
bar=beat*4; c=0
while c*bar < DUR-1.0:
    for f in chords[c%4]: add(note(f,bar),c*bar,0.07)
    add(note(chords[c%4][0]/2,bar),c*bar,0.10)
    # pluck melody
    mel=[0,2,1,2]
    for m in range(4):
        add(note(chords[c%4][mel[m]]*2,beat*0.9)*np.exp(-np.arange(int(beat*0.9*SR))/SR*5),c*bar+m*beat,0.05)
    c+=1
# sfx
pt=np.arange(int(0.12*SR))/SR
pop=np.sin(2*np.pi*np.cumsum(500+900*pt/0.12)/SR)*np.exp(-pt*30)
dt=np.arange(int(0.3*SR))/SR
ding=(np.sin(2*np.pi*1318*dt)+0.5*np.sin(2*np.pi*1975*dt))*np.exp(-dt*12)
wt=np.arange(int(0.4*SR))/SR
whoosh=rng.standard_normal(len(wt))*np.sin(np.pi*wt/0.4)**2
whoosh=np.convolve(whoosh,np.ones(40)/40,'same')
for at in [0.1,0.55,1.05,3.05,3.35,7.05,8.0,8.4,19.05,21.8,25.4,25.7,25.9,26.4]: add(pop,at,0.35)
for at in [3.0,7.0,10.0,19.0,21.8,25.0]: add(whoosh,at,0.5)
add(ding,5.9,0.35)   # stamp
add(pop,13.9,0.5)    # translate tap
add(ding,14.6,0.3)   # translated
add(whoosh,15.6,0.4) # send
add(ding,17.0,0.45)  # reply
for i in range(8): add(pop,22.15+i*0.13,0.25)
# fade out
fo=np.ones(n); fo[-int(1.5*SR):]=np.linspace(1,0,int(1.5*SR)); mix*=fo
mix=mix/np.max(np.abs(mix))*0.89
pcm=(mix*32767).astype(np.int16)
w=wave.open(sys.argv[1],'wb'); w.setnchannels(1); w.setsampwidth(2); w.setframerate(SR); w.writeframes(pcm.tobytes()); w.close()
