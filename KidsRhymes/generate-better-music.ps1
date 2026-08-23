param([string]$Root = $PSScriptRoot)
$ErrorActionPreference = 'Stop'
$out = Join-Path $Root 'output\baa-baa-black-sheep\audio'
$tmp = Join-Path $Root 'output\baa-baa-black-sheep\tmp'
New-Item -ItemType Directory -Force $out,$tmp | Out-Null
$midi = Join-Path $tmp 'baa-baa-arrangement.mid'
$wav = Join-Path $out 'storybook-arrangement.wav'
$museScore = 'C:\Program Files\MuseScore 4\bin\MuseScore4.exe'
if (-not (Test-Path $museScore)) { throw 'MuseScore 4 is required.' }

Add-Type -TypeDefinition @'
using System;
using System.IO;
using System.Collections.Generic;
using System.Linq;

public static class TinyTalesMidi {
  const int PPQ = 480;
  class E { public int T, O; public byte[] D; public E(int t,int o,params byte[] d){T=t;O=o;D=d;} }
  static byte[] VLQ(int value) {
    var b=new List<byte>(); b.Add((byte)(value&127));
    while((value>>=7)>0) b.Insert(0,(byte)((value&127)|128)); return b.ToArray();
  }
  static void BE(BinaryWriter w,int value,int bytes){ for(int i=bytes-1;i>=0;i--)w.Write((byte)(value>>(i*8))); }
  static void Note(List<E> e,int ch,int tick,int dur,int note,int vel){
    e.Add(new E(tick,1,(byte)(0x90|ch),(byte)note,(byte)vel));
    e.Add(new E(tick+dur,0,(byte)(0x80|ch),(byte)note,0));
  }
  static byte[] Track(List<E> events, int endTick, int program, int channel, string name, bool tempo=false) {
    events.Add(new E(0,-3,0xFF,0x03,(byte)name.Length));
    var nameBytes=System.Text.Encoding.ASCII.GetBytes(name);
    events[events.Count-1].D=events[events.Count-1].D.Concat(nameBytes).ToArray();
    if(tempo) events.Add(new E(0,-2,0xFF,0x51,0x03,0x09,0x89,0x68)); // 625000 us = 96 BPM
    if(channel!=9) events.Add(new E(0,-1,(byte)(0xC0|channel),(byte)program));
    events.Add(new E(endTick,9,0xFF,0x2F,0x00));
    var ordered=events.OrderBy(x=>x.T).ThenBy(x=>x.O).ToList();
    using(var m=new MemoryStream()){ int last=0; foreach(var x in ordered){
      var delta=VLQ(x.T-last); m.Write(delta,0,delta.Length); m.Write(x.D,0,x.D.Length); last=x.T;
    } return m.ToArray(); }
  }
  public static void Build(string path) {
    int bars=28, bar=PPQ*4, end=bars*bar;
    int[][] chords={new[]{60,64,67},new[]{55,59,62},new[]{57,60,64},new[]{53,57,60}};
    // Public-domain tune, phrased in C major. Each tuple is pitch and eighth-note length.
    int[][] melody={
      new[]{67,1,67,1,69,2,67,2,64,2}, new[]{64,2,62,2,60,4},
      new[]{67,1,67,1,69,2,67,2,64,2}, new[]{62,2,60,2,60,4},
      new[]{64,2,64,2,65,2,67,2}, new[]{69,2,67,2,64,4},
      new[]{62,2,62,2,64,2,65,2}, new[]{67,2,64,2,60,4}
    };
    var guitar=new List<E>(); var marimba=new List<E>(); var bells=new List<E>();
    var strings=new List<E>(); var drums=new List<E>();
    for(int b=0;b<bars;b++){
      int t=b*bar; var c=chords[b%4];
      for(int beat=0;beat<4;beat++){
        int bt=t+beat*PPQ;
        foreach(int n in c) Note(guitar,0,bt,350,n,beat==0?64:48);
        Note(marimba,1,bt,300,c[0]-24,beat==0?68:52);
        if(beat==1||beat==3) Note(strings,3,bt,260,c[1],42);
        Note(drums,9,bt,90,beat==0||beat==2?36:42,beat==0?46:28);
        Note(drums,9,bt+PPQ/2,60,42,20);
      }
      var phrase=melody[b%melody.Length]; int pos=t;
      for(int i=0;i<phrase.Length;i+=2){int ticks=phrase[i+1]*PPQ/2; Note(bells,2,pos,(int)(ticks*.78),phrase[i]+12,58); pos+=ticks;}
    }
    var tracks=new[]{
      Track(guitar,end,24,0,"Nylon Guitar",true), Track(marimba,end,12,1,"Marimba"),
      Track(bells,end,9,2,"Glockenspiel"), Track(strings,end,45,3,"Pizzicato Strings"),
      Track(drums,end,0,9,"Light Percussion")};
    using(var fs=File.Create(path)) using(var w=new BinaryWriter(fs)){
      w.Write(System.Text.Encoding.ASCII.GetBytes("MThd")); BE(w,6,4); BE(w,1,2); BE(w,tracks.Length,2); BE(w,PPQ,2);
      foreach(var tr in tracks){w.Write(System.Text.Encoding.ASCII.GetBytes("MTrk"));BE(w,tr.Length,4);w.Write(tr);}
    }
  }
}
'@
[TinyTalesMidi]::Build($midi)
if (Test-Path $wav) { Remove-Item -LiteralPath $wav -Force }
& $museScore -o $wav $midi
for ($attempt = 0; $attempt -lt 60 -and -not (Test-Path $wav); $attempt++) {
  Start-Sleep -Milliseconds 500
}
if (-not (Test-Path $wav)) { throw 'MuseScore did not create the expected WAV.' }
Write-Output "Arrangement: $wav"
