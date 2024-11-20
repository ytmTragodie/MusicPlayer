import os
import sys
import threading
import wave
from time import time

import demo
import librosa
import pyaudio
import soundfile as sf
from PyQt5.QtCore import QDir, Qt, pyqtSignal, pyqtSlot
from PyQt5.QtWidgets import (QApplication, QDialog, QFileDialog, QHeaderView,
                             QTableWidgetItem)
from Ui_Dialog import Ui_Retrive

CHUNK = 512
FORMAT = pyaudio.paInt16
CHANNELS = 1
RATE = 44100



class QmyDialog(QDialog):
    doubleClickSong = pyqtSignal(str,int)

    def __init__(self,parent = None):
        super().__init__(parent)
        self.ui = Ui_Retrive()
        self.ui.setupUi(self)
        self.setWindowFlag(Qt.WindowStaysOnTopHint)
        self.setMatchSongTable()

        self.Songs = parent.songdata.Songs if parent else None
        self.FPs = parent.songdata.Fingerprints if parent else None
        self.songpath = None
        self.record_flag = True # 录音开始与停止的公共访问量，控制录音进程的结束
        self.frames = []

    def setMatchSongTable(self):
        self.ui.MatchSongTable.setColumnWidth(0,220)
        self.ui.MatchSongTable.setColumnWidth(1,65)
        self.ui.MatchSongTable.setColumnWidth(2,70)
        self.ui.MatchSongTable.verticalHeader().setSectionResizeMode(QHeaderView.Stretch)

    @pyqtSlot(bool)
    def on_RecordBtn_clicked(self,ischecked):
        def recording():
            
            while self.record_flag:
                data = stream.read(CHUNK)
                self.frames.append(data)
            stream.stop_stream()
            stream.close()
            p.terminate()
            self.record_flag = True 

        if ischecked:
            self.ui.RecordBtn.setChecked(True)
            p = pyaudio.PyAudio()
            stream = p.open(format=FORMAT,
            channels=CHANNELS,
            rate=RATE,
            input=True,
            frames_per_buffer=CHUNK)
            
            t1 = threading.Thread(target=recording)
            t1.start()
        else:
            self.ui.RecordBtn.setChecked(False)
            self.record_flag = False
            while not self.record_flag:
                pass
            curPath=QDir.currentPath()    #获取系统当前目录
            dlgTitle="保存录音"       #对话框标题
            filter="音频文件(*.mp3 *.wav)"   #文件过滤器
            file,filterUsed=QFileDialog.getSaveFileName(self,dlgTitle,curPath,filter)
            if file:
                p = pyaudio.PyAudio()
                wf = wave.open(file, 'wb')
                wf.setnchannels(CHANNELS)
                wf.setsampwidth(p.get_sample_size(FORMAT))
                wf.setframerate(RATE)
                wf.writeframes(b''.join(self.frames))
                wf.close()
                p.terminate()
                self.frames= []
                self.songpath = file
                # y,sr = librosa.load(file)
                # sf.write(file,y*10,sr)
                self.ui.SongPathLbl.setText("当前选择音频:"+self.songpath)

    @pyqtSlot()
    def on_ImportBtn_clicked(self):
        curPath=QDir.currentPath()    #获取系统当前目录
        dlgTitle="添加音乐"       #对话框标题
        filter="音频文件(*.mp3 *.aac *.wav)"   #文件过滤器
        file,filterUsed=QFileDialog.getOpenFileName(self,dlgTitle,curPath,filter,options=QFileDialog.ReadOnly)
        if file:
            self.songpath = file
            self.ui.SongPathLbl.setText("当前选择音频:"+self.songpath)

    @pyqtSlot()
    def on_RetriveBtn_clicked(self):
        if self.FPs and self.Songs and self.songpath:
            t1 = time(  )
            fingerprint = demo.calculate_fingerprint(-1,self.songpath)
            fingercount = sum(len(v) for v in fingerprint.values())
            match_heap = demo.compare_fingerprint(self.FPs,len(self.Songs.keys()),fingerprint)
            match_time = time()-t1
            match_heap.sort(key=lambda x:x[0],reverse=True)
            for i,(max_count,match_id,match_timediff) in enumerate(match_heap):
                if self.Songs.get(match_id):
                    match_song = self.Songs[match_id]
                else:
                    match_song = 'NotFound'
                timeInfo = str(match_timediff)
                self.ui.MatchSongTable.setItem(i,0,QTableWidgetItem(match_song))
                self.ui.MatchSongTable.setItem(i,1,QTableWidgetItem(timeInfo.split('.')[0]+'.'+timeInfo.split('.')[1][:2]+'s'))
                self.ui.MatchSongTable.setItem(i,2,QTableWidgetItem(str(max_count/(fingercount+1)*100)[:4]+'%'))
            self.ui.MatchInfoLbl.setText("匹配耗时: {}s".format(match_time))

    @pyqtSlot(int,int)
    def on_MatchSongTable_cellDoubleClicked(self,row,col):
        songname = self.ui.MatchSongTable.item(row,0).text()
        pos = self.ui.MatchSongTable.item(row,1).text()
        pos = int(float(pos[:-1])*1000)
        self.doubleClickSong.emit(songname,pos)


if __name__ == "__main__":
    app = QApplication(sys.argv)
    form = QmyDialog()
    form.show()
    sys.exit(app.exec_())
