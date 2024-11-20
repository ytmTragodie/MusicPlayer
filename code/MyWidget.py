import sys,os
import re


from demo import SongData
from MyDialog import QmyDialog
from PyQt5 import QtCore
from PyQt5.QtCore import QDir, QEvent, Qt, QUrl, pyqtSlot, QPoint
from PyQt5.QtMultimedia import QMediaContent, QMediaPlayer, QMediaPlaylist
from PyQt5.QtWidgets import (QApplication, QFileDialog, QListWidgetItem,
                             QMessageBox, QWidget)

from PyQt5.QtCore import QTimer
from Ui_Widget import Ui_MusicPlayer

from utility import lyricsDisplayer
import qtawesome


class QmyWidget(QWidget):
    def __init__(self, load_path ,parent = None):
        super().__init__(parent)
        self.ui = Ui_MusicPlayer()
        self.lyricsDisplayer = lyricsDisplayer()
        self.ui.lyricsDisplayer = self.lyricsDisplayer
        self.ui.setupUi(self)

        # self.ui.gridLayout_2.addWidget(self.lyricsDisplayer, 1, 0, 2, 10)
        self.songdata = SongData(load_path)
        self.addsongflag = False
        print(len(self.songdata.Songs.keys()))

        self.setWindowOpacity(0.95) # 设置窗口透明度
        self.setAttribute(QtCore.Qt.WA_TranslucentBackground) # 设置窗口背景透明
        self.setWindowFlag(QtCore.Qt.FramelessWindowHint) # 隐藏边框

        self.__curpos = "0:00"
        self.__duration = "0:00"
        self.player = QMediaPlayer()
        self.playlist = QMediaPlaylist()
        self.player.setPlaylist(self.playlist)
        self.playlist.setPlaybackMode(QMediaPlaylist.Loop)
        self.init_playlist()

        self.player.positionChanged.connect(self.do_positionChanged)
        self.player.durationChanged.connect(self.do_durationChanged)
        self.playlist.currentIndexChanged.connect(self.do_currentChanged)

        #歌词
        self.timer = QTimer()
        self.timer.timeout.connect(self.updateLyrics)
        self.nowname = 'None'
        self.lyrics_info={
            'name' : 'None',
        }
        self.paused = True 

        self._is_dragging = False
        self.isMaximized = False
        self._start_position = QPoint()
        self.LyricsItem =  ""
    


# # 自定义功能函数
    def updateLyrics(self):
        nowtime =  self.player.position()
        nowtime = nowtime / 1000
        nowname = self.ui.SongList.currentItem().text()
        if nowname != self.nowname and nowname is not None:
            self.nowname = nowname
            self.lyricsDisplayer.load_lyrics(self.nowname)
        self.lyricsDisplayer.update(current_time=nowtime)
        # print(nowtime)


    def init_playlist(self):
        for v in self.songdata.Songs.values():
            filename = self.songdata.datapath+'/MusicData/'+v+'.mp3'
            aItem = QListWidgetItem()
            aItem.setText(v)
            aItem.setSelected(True)
            self.ui.SongList.addItem(aItem)
            song = QMediaContent(QUrl.fromLocalFile(filename))
            self.playlist.addMedia(song)

    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            self._is_dragging = True
            self._start_position = event.globalPos() - self.frameGeometry().topLeft()
            event.accept()

    def mouseMoveEvent(self, event):
        if self._is_dragging and event.buttons() == Qt.LeftButton:
            self.move(event.globalPos() - self._start_position)
            event.accept()

    def mouseReleaseEvent(self, event):
        self._is_dragging = False
        event.accept()
# # 自动关联的槽函数
    @pyqtSlot()
    def on_PlayPauseBtn_clicked(self):
        # if self.ui.SongList.currentRow() > -1:
        #     self.playlist.setCurrentIndex(self.ui.SongList.currentRow())
        #     self.player.play()
        #     self.timer.start()
        #     self.ui.console_button_3.setIcon(qtawesome.icon('fa.pause', color='#F76677', font=18))  #正在播放，标识换成暂停键
        if self.paused is False:
            self.paused = True
            self.player.pause()
            self.timer.stop()
            self.ui.console_button_3.setIcon(qtawesome.icon('fa.play', color='#F76677', font=18))
        elif self.ui.SongList.currentRow() > -1:
            self.paused = False
            self.player.play()
            self.timer.start(200)
            self.ui.console_button_3.setIcon(qtawesome.icon('fa.pause', color='#F76677', font=18))  #正在播放，标识换成暂停键
        # if self.paused :  #之前处于暂停状态
        #     if self.ui.SongList.currentRow() > -1:
        #         self.playlist.setCurrentIndex(self.ui.SongList.currentRow())
        #     self.player.play()
        #     self.timer.start()
        #     self.ui.console_button_3.setIcon(qtawesome.icon('fa.pause', color='#F76677', font=18))  #正在播放，标识换成暂停键
        #     if self.ui.SongList.currentItem() is not None:
        #         if self.ui.SongList.currentItem().text() != self.LyricsItem :
        #             self.LyricsItem = self.ui.SongList.currentItem().text()
        #             self.lyricsDisplayer.load_lyrics(self.ui.SongList.currentItem().text())
        #             self.lyricsDisplayer.start_scroll_lyrics()
        #         else:
        #             self.lyricsDisplayer.Continue()
        #         self.paused = False  
        #     else:
        #         print("请选择一首歌曲")
        # else:
        #     # self.lyricsDisplayer.pause()#歌词停
        #     self.timer.stop()
        #     self.player.pause()
        #     self.ui.console_button_3.setIcon(qtawesome.icon('fa.play', color='#F76677', font=18))
        #     self.paused = True
        #print(self.ui.SongList.currentItem().text())
        # self.lyricsDisplayer.start_scroll_lyrics()


    @pyqtSlot()
    def on_CloseBtn_clicked(self):
        self.close()  # 关闭窗口

    @pyqtSlot()
    def on_MiniBtn_clicked(self):
        self.showMinimized()  # 最小化窗口

    @pyqtSlot()
    def on_RestoreBtn_clicked(self):
        if self.isMaximized:
            # 还原窗口
            self.showNormal()
        else:
            # 最大化窗口
            self.showMaximized()

        # 切换状态
        self.isMaximized = not self.isMaximized
        

    @pyqtSlot()
    def on_BackwardBtn_clicked(self):
        # 后退功能
        current_position = self.player.position() # 获取当前播放位置（以毫秒为单位）
        new_position = max(0, current_position - 5000)  # 后退 5 秒
        self.player.setPosition(new_position)  # 设置新的播放位置
        #self.ui.MusicPositionSlider.setSliderPosition(new_position)
        
    @pyqtSlot()
    def on_ForwardBtn_clicked(self):
        # 快进功能
        current_position = self.player.position()  # 获取当前播放位置（以毫秒为单位）
        duration = self.player.duration()  # 获取音频总时长
        new_position = min(duration, current_position + 5000)  # 快进 5 秒
        self.player.setPosition(new_position)  # 设置新的播放位置


    @pyqtSlot()
    def on_RetriveSongBtn_clicked(self):
        # 非模态调用Dialog，将Dialog中的歌曲点击信号发射，与播放匹配歌曲相连
        retriveDialog = QmyDialog(self)
        retriveDialog.setAttribute(Qt.WA_DeleteOnClose)
        retriveDialog.doubleClickSong.connect(self.do_playMatchSong)
        retriveDialog.show()
        
    @pyqtSlot()
    def on_ImportSongBtn_clicked(self):
        curPath=QDir.currentPath()    #获取系统当前目录
        dlgTitle="添加音乐"       #对话框标题
        filter="音频文件(*.mp3 *.aac)"   #文件过滤器

        fileList,filterUsed=QFileDialog.getOpenFileNames(self,dlgTitle,curPath,filter,options=QFileDialog.ReadOnly)
        for filename in fileList:
            flag,newpath = self.songdata.add_fingerprints(filename)
            print(flag)
            if flag:
                self.addsongflag = True
                head,tail = os.path.split(newpath)
                songname = tail.split('.')[0]
                aItem = QListWidgetItem()
                aItem.setText(songname)
                aItem.setSelected(True)
                self.ui.SongList.addItem(aItem)
                song = QMediaContent(QUrl.fromLocalFile(newpath))
                self.playlist.addMedia(song)
    

    @pyqtSlot()
    def on_SearchBtn_clicked(self):
        matchtext = re.compile(self.ui.SearchLine.text())

        for i in range(self.ui.SongList.count()):
            item = self.ui.SongList.item(i)
            if re.search(matchtext, item.text()):
                item.setHidden(False)
            else:
                item.setHidden(True)

    @pyqtSlot(int)
    def on_MusicPositionSlider_sliderMoved(self, position):
        self.player.setPosition(position)

    def on_SongList_doubleClicked(self,index):
        self.playlist.setCurrentIndex(index.row())
        self.paused = False
        self.player.play()
        self.timer.start(200)
        self.ui.console_button_3.setIcon(qtawesome.icon('fa.pause', color='#F76677', font=18))
        #self.paused = False
        #self.lyricsDisplayer.load_lyrics(self.ui.SongList.currentItem().text())
        #self.LyricsItem = self.ui.SongList.currentItem().text()


# # 自定义槽函数
    def do_playMatchSong(self,songname,pos):
        for i in range(self.ui.SongList.count()):
            item = self.ui.SongList.item(i)
            if songname == item.text():
                self.ui.SongList.setCurrentRow(i)
                self.playlist.setCurrentIndex(i)
        self.player.setPosition(pos)
        self.player.play()

    def do_positionChanged(self,position):
        if (self.ui.MusicPositionSlider.isSliderDown()):
            return 
        self.ui.MusicPositionSlider.setSliderPosition(position)
        secs = position/1000
        mins = secs/60
        secs = secs%60
        self.__curpos = "%d:%d"%(mins,secs)
        self.ui.MusicTimeLbl.setText(self.__curpos+'/'+self.__duration)

    def do_durationChanged(self,duration):
        self.ui.MusicPositionSlider.setMaximum(duration)
        secs = duration/1000
        mins = secs/60
        secs = secs%60
        self.__duration = "%d:%d"%(mins,secs)
        self.ui.MusicTimeLbl.setText(self.__curpos+'/'+self.__duration)

    def do_currentChanged(self,index):
        self.ui.SongList.setCurrentRow(index)
        item = self.ui.SongList.currentItem()
        if item:
            self.ui.MusicNameLbl.setText("Now: "+ item.text())

    def closeEvent(self, event):
        if self.addsongflag:
            digTitle = "Question"
            strInfo = "是否保存添加歌曲的指纹?"
            defaultBtn = QMessageBox.NoButton
            result = QMessageBox.question(self,digTitle,strInfo,QMessageBox.Yes|QMessageBox.No,defaultBtn)
            if result == QMessageBox.Yes:
                self.songdata.save_fingerprints()
        event.accept()

# # 窗体测试

if __name__ == "__main__":
    
    curpath = os.getcwd()
    print(curpath)
    app = QApplication(sys.argv)
    form = QmyWidget(curpath)
    form.show()
    sys.exit(app.exec_())


