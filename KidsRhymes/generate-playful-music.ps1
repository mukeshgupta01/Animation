param([string]$Root = 'C:\KidsRhymes')
$ErrorActionPreference = 'Stop'
$out = Join-Path $Root 'output\baa-baa-black-sheep\audio'
$tmp = Join-Path $Root 'output\baa-baa-black-sheep\tmp'
New-Item -ItemType Directory -Force $out,$tmp | Out-Null
$midi = Join-Path $tmp 'baa-baa-playful-tune.mid'
$wav = Join-Path $out 'playful-bounce-arrangement.wav'
$museScore = 'C:\Program Files\MuseScore 4\bin\MuseScore4.exe'
if (-not (Test-Path $museScore)) { throw 'MuseScore 4 is required.' }

Add-Type -TypeDefinition @'
using System;
using System.IO;
using System.Collections.Generic;
using System.Linq;

public static class PlayfulBaaMidi {
  const int Q=480, E=240, S=120;
  class Ev { public int T,O; public byte[] D; public Ev(int t,int o,params byte[] d){T=t;O=o;D=d;} }
  static byte[] V(int n){var x=new List<byte>{(byte)(n&127)};while((n>>=7)>0)x.Insert(0,(byte)((n&127)|128));return x.ToArray();}
  static void BE(BinaryWriter w,int n,int count){for(int i=count-1;i>=0;i--)w.Write((byte)(n>>(8*i)));}
  static void N(List<Ev>x,int ch,int t,int d,int n,int v){x.Add(new Ev(t,1,(byte)(0x90|ch),(byte)n,(byte)v));x.Add(new Ev(t+d,0,(byte)(0x80|ch),(byte)n,0));}
  static void CC(List<Ev>x,int ch,int t,int cc,int val){x.Add(new Ev(t,-1,(byte)(0xB0|ch),(byte)cc,(byte)val));}
  static byte[] Tr(List<Ev>x,int end,int pg,int ch,string name,bool tempo=false){
    var nb=System.Text.Encoding.ASCII.GetBytes(name); x.Add(new Ev(0,-4,new byte[]{0xFF,0x03,(byte)nb.Length}.Concat(nb).ToArray()));
    if(tempo)x.Add(new Ev(0,-3,0xFF,0x51,0x03,0x09,0x89,0x68)); // 96 BPM
    if(ch!=9)x.Add(new Ev(0,-2,(byte)(0xC0|ch),(byte)pg));
    x.Add(new Ev(end,9,0xFF,0x2F,0)); var a=x.OrderBy(z=>z.T).ThenBy(z=>z.O);
    using(var m=new MemoryStream()){int last=0;foreach(var z in a){var d=V(z.T-last);m.Write(d,0,d.Length);m.Write(z.D,0,z.D.Length);last=z.T;}return m.ToArray();}
  }
  public static void Build(string path){
    int bars=28, bar=4*Q, end=bars*bar;
    int[][] chords={new[]{60,64,67},new[]{57,60,64},new[]{53,57,60},new[]{55,59,62}}; // C Am F G
    // Original two-bar “bounce and sparkle” hook. Zero means an eighth rest.
    int[][] hooks={
      new[]{72,0,76,79,76,74,72,67}, new[]{69,72,76,0,74,72,67,0},
      new[]{72,74,76,72,79,0,76,74}, new[]{72,69,67,69,72,0,67,0},
      new[]{76,76,74,72,69,72,74,0}, new[]{79,76,74,72,74,76,72,0},
      new[]{67,69,72,74,76,74,72,69}, new[]{67,0,72,0,76,74,72,0}
    };
    var uke=new List<Ev>();var bass=new List<Ev>();var bell=new List<Ev>();var pizz=new List<Ev>();var drum=new List<Ev>();var celesta=new List<Ev>();
    CC(uke,0,0,10,46);CC(bass,1,0,10,58);CC(bell,2,0,10,74);CC(pizz,3,0,10,34);CC(celesta,4,0,10,86);
    for(int b=0;b<bars;b++){
      int t=b*bar;var c=chords[b%4];bool intro=b<2,outro=b>=26,middle=b>=10&&b<18;
      // Ukulele-like off-beat strums with a softer first beat.
      for(int beat=0;beat<4;beat++){
        int bt=t+beat*Q;
        if(beat==0)foreach(int n in c)N(uke,0,bt,210,n,intro?38:48);
        foreach(int n in c)N(uke,0,bt+E,175,n+12,(beat==1||beat==3)?61:53);
      }
      // Walking marimba: root, fifth, octave, fifth.
      int[] walk={c[0]-24,c[2]-24,c[0]-12,c[2]-24};
      for(int beat=0;beat<4;beat++)N(bass,1,t+beat*Q,300,walk[beat],middle?70:62);
      // Pizzicato answers only in the second half of each bar, leaving vocal space.
      N(pizz,3,t+2*Q,190,c[1]+12,42);N(pizz,3,t+3*Q,190,c[2]+12,48);
      // Hook melody. Vary octave and instrument to create sections.
      var h=hooks[b%8];
      for(int i=0;i<8;i++)if(h[i]>0){int note=h[i]-(outro?12:0);N(bell,2,t+i*E,165,note,intro?54:(middle?68:62));}
      // Celesta call-and-response at phrase endings.
      if(b%4==3){N(celesta,4,t+2*Q,170,79,46);N(celesta,4,t+2*Q+E,170,76,43);N(celesta,4,t+3*Q,280,72,50);}
      // Light kick, shaker, claps on 2 and 4, plus a tiny fill every four bars.
      for(int beat=0;beat<4;beat++){
        int bt=t+beat*Q;N(drum,9,bt,60,beat==0||beat==2?36:42,beat==0?48:28);N(drum,9,bt+E,55,42,24);
        if(!intro&&(beat==1||beat==3))N(drum,9,bt,70,39,36);
      }
      if(b%4==3&&!outro){N(drum,9,t+3*Q,65,45,35);N(drum,9,t+3*Q+E,65,47,38);N(drum,9,t+3*Q+3*S,65,50,42);}
    }
    var tracks=new[]{Tr(uke,end,24,0,"Bouncy Ukulele",true),Tr(bass,end,12,1,"Walking Marimba"),Tr(bell,end,9,2,"Sparkle Hook"),Tr(pizz,end,45,3,"Pizzicato Answers"),Tr(celesta,end,8,4,"Celesta Response"),Tr(drum,end,0,9,"Claps and Percussion")};
    using(var f=File.Create(path))using(var w=new BinaryWriter(f)){w.Write(System.Text.Encoding.ASCII.GetBytes("MThd"));BE(w,6,4);BE(w,1,2);BE(w,tracks.Length,2);BE(w,Q,2);foreach(var tr in tracks){w.Write(System.Text.Encoding.ASCII.GetBytes("MTrk"));BE(w,tr.Length,4);w.Write(tr);}}
  }
}
'@
[PlayfulBaaMidi]::Build($midi)
if (Test-Path $wav) { Remove-Item -LiteralPath $wav -Force }
& $museScore -o $wav $midi
for ($attempt = 0; $attempt -lt 60 -and -not (Test-Path $wav); $attempt++) { Start-Sleep -Milliseconds 500 }
if (-not (Test-Path $wav)) { throw 'MuseScore did not create the playful arrangement.' }

# Create a quick audition using the corrected lead vocal and the most energetic opening section.
$voice = Join-Path $out 'female-lead-and-chorus.wav'
$preview = Join-Path $Root 'output\baa-baa-black-sheep\playful-tune-preview.mp3'
& ffmpeg -y -ss 0 -t 24 -i $wav -ss 0 -t 24 -i $voice -filter_complex '[0:a]volume=0.72[m];[1:a]volume=1.15[v];[m][v]amix=2:duration=longest:normalize=0,loudnorm=I=-15:LRA=7:TP=-1.5[a]' -map '[a]' -t 24 -c:a libmp3lame -b:a 192k $preview
if ($LASTEXITCODE) { throw 'Playful tune preview failed.' }
Write-Output "Playful arrangement: $wav"
Write-Output "Audition preview: $preview"
