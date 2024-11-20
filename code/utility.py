from PyQt5.QtWidgets import QApplication, QMainWindow, QVBoxLayout, QWidget, QLabel
from PyQt5.QtCore import QTimer

import sys
import re
import time
import numpy as np
import pyqtgraph as pg

engin_id = "02f741aea21f545a9"
key = "AIzaSyDSBN3V4fpP4wRr0YVkNo4o9riXT170fb0"



class PlayWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setupUI()
    
    def setupUI(self):
        self.setWindowTitle("Music Player with Scrolling Lyrics")
        self.setGeometry(300, 300, 800, 600)

        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        layout = QVBoxLayout(central_widget)


        # Add the lyrics display widget
        self.lyrics_display = lyricsDisplayer()
        layout.addWidget(self.lyrics_display)
    
    def play_song(self, song_title):
        path = "./MusicData/"+song_title + ".lrc"
        self.lyrics_display.load_lyrics(path)
        self.lyrics_display.start_scroll_lyrics()
 





class lyricsDisplayer(QWidget):
    def __init__(self,parent=None):
        super().__init__(parent)
        self.setUI()


    def setUI(self):
        self.layout = QVBoxLayout()
        self.rows =5
        lyrics_lines = [
            "Enjoy Music",
            "",
            "",
            "",
            ""
        ]
        self.labels = []
        i = 0
        for line in lyrics_lines:
            label = QLabel(line)
            color = "black"
            if i == 0:
                color = "orange"
            label.setStyleSheet(f"font-family: 'Arial'; font-size: 32px; font-weight: bold; color: {color};")
            self.layout.addWidget(label)
            self.labels.append(label)
            i+=1
        
        self.setLayout(self.layout)

        #about lyrics scroll 
        # self.timer = QTimer()
        # self.timer.timeout.connect(self.update)
        # self.start_time = 0
        self.line_indexes = list(range(0,5))

    def load_lyrics(self,title):
        path = "./MusicData/"+title + ".lrc"
        pattern = re.compile(r"\[(\d+):(\d+\.\d+)\](.+)")
        self.lyrics_list = []
        with open(path,'r') as file:
            for line in file:
                match = pattern.match(line)
                if match:
                    minutes = int(match.group(1))
                    seconds = float(match.group(2))
                    timestamp = minutes * 60 + seconds
                    text = match.group(3)
                    self.lyrics_list.append((timestamp, text))
        print("lyrics load sucess!")
        return self.lyrics_list
    
    # def start_scroll_lyrics(self):
    #     self.start_time = time.time()
    #     self.timer.start(100)

    def update(self,current_time=None):#find the to be displayed lrics and show
        # current_time = time.time() - self.start_time
        
        index = 0
        while index < len(self.lyrics_list) and current_time > self.lyrics_list[index][0]:#查找到播放要显示的地方
            index += 1
        if index != 0:
            index = index -1
        # print(f"current time is f{current_time}, lyrics second row time if f{self.lyrics_list[index][0]}")
        # print(f"find  the proper index is in f{index}")
        if index>=len(self.lyrics_list):
            return
        color = 'black'
        for i in range(0,self.rows):
            if index <=int(self.rows/2):#刚开始
                self.labels[i].setText(self.lyrics_list[i][1])#设置歌词
                if index == i:
                    color = 'orange'
                else:
                    color = 'black'
            elif index >= len(self.lyrics_list)-int(self.rows/2):#到末尾
                self.labels[i].setText(self.lyrics_list[len(self.lyrics_list)-self.rows+i][1])#设置歌词
                if index == len(self.lyrics_list)-self.rows+i:
                    color = 'orange'
                else:
                    color = 'black'
            else:
                self.labels[i].setText(self.lyrics_list[index-self.rows//2 + i][1])#设置歌词
                if i==self.rows//2:
                    color = 'orange'
                else:
                    color = 'black'
            self.labels[i].setStyleSheet(f"font-family: 'Arial'; font-size: 32px; font-weight: bold; color: {color};")
        # while self.line_indexes[0] < len(self.lyrics_list) and current_time >= self.lyrics_list[self.line_indexes[0]][0]:
        #     # self.label.setText(self.lyrics_list[self.line_indexes[0]][1])
        #     for i in range(0,self.rows):
        #         self.labels[i].setText(self.lyrics_list[self.line_indexes[i]][1])
        #         self.line_indexes[i] += 1

        # if self.line_indexes[self.rows-1] >= len(self.lyrics_list):
        #     self.timer.stop()


    # def pause(self):
    #     self.timer.stop()
    
    # def Continue(self):
    #     self.timer.start(100)
    
# def load_lyrics(path):
#     pattern = re.compile(r"\[(\d+):(\d+\.\d+)\](.+)")
#     lyrics_list = []
#     with open(path,'r') as file:
#         for line in file:
#             match = pattern.match(line)
#             if match:
#                 minutes = int(match.group(1))
#                 seconds = float(match.group(2))
#                 timestamp = minutes * 60 + seconds
#                 text = match.group(3)
#                 lyrics_list.append((timestamp, text))
    
#     return lyrics_list

if __name__=="__main__":
    
    app = QApplication(sys.argv)
    mw = PlayWindow()
    mw.show()
    mw.play_song("Radiohead - Fake Plastic Trees")
    sys.exit(app.exec_())
    # print(load_lyrics("./MusicData/Radiohead - Fake Plastic Trees.lrc"))