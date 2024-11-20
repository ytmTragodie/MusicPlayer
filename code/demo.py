import hashlib
import os
import random as rd
import time
from collections import defaultdict
from heapq import *

import librosa
import numpy as np
import scipy.signal
import soundfile as sf

from matplotlib import pyplot as plt

N_FFT = 8192   # window length
ZONE_WIDTH = 5
SNR = 5 # signal noise rating
N = 10 # once testpart number
D = 22050*1 # testpart during time 6s > ZONE_WIDTH
ADD_NOISE = 1 # add noise to test
curpath = os.getcwd()

def calculate_fingerprint(id,songpath):
    fingerprint = defaultdict(list)
    y, sr = librosa.load(songpath)
    
    amplitude_spectrum = np.abs(librosa.stft(y,n_fft=N_FFT)[50:1551])
    f_size,t_size = amplitude_spectrum.shape
    highpeak_spectrum = []
    lowpeak_spectrum = []
   
    for i in range(t_size):
        amplitude_frame = amplitude_spectrum[:, i]
        amplitude_frame = amplitude_frame - max(amplitude_frame) / 2
        # 普通的找极值点办法
        # peaks, _ = scipy.signal.find_peaks(amplitude_frame, height=10, distance=5) 
        # 超过最大值的一半为高阈值，当音量较小时，可能不可信，取和10比较的较大值
        highpeaks, _ = scipy.signal.find_peaks(amplitude_frame, height=max(max(amplitude_frame)/2,10), distance=5) 
        lowpeaks,_ = scipy.signal.find_peaks(amplitude_frame, height=10, distance=5)
        lowpeaks = list(set(lowpeaks)-set(highpeaks))
        highpeak_spectrum.append(highpeaks)
        lowpeak_spectrum.append(lowpeaks)
    # 剔除low-low peaks 组成的指纹
    for i in range(t_size - ZONE_WIDTH):
        for fh1 in highpeak_spectrum[i]:
            for j in range(ZONE_WIDTH):
                for fh2 in highpeak_spectrum[i+j+1]:
                    hash = hashlib.md5("{}:{}:{}".format(fh1,fh2,j+1).encode("utf-8")).hexdigest()
                    fingerprint[hash].append((id,i+j+1))
                for fl2 in lowpeak_spectrum[i+j+1]:
                    hash = hashlib.md5("{}:{}:{}".format(fh1,fl2,j+1).encode("utf-8")).hexdigest()
                    fingerprint[hash].append((id,i+j+1))
        for fl1 in lowpeak_spectrum[i]:
            for j in range(ZONE_WIDTH):
                for fh2 in highpeak_spectrum[i+j+1]:
                    hash = hashlib.md5("{}:{}:{}".format(fl1,fh2,j+1).encode("utf-8")).hexdigest()
                    fingerprint[hash].append((id,i+j+1))
    
    return fingerprint

def compare_fingerprint(FPs,m,partfp):
    # 输出匹配率前五的歌曲和时间信息
    match = [defaultdict(int) for _ in range(m)]
    match_heap = [(-1,-1,-1)]*5
    heapify(match_heap)
    for k,vlist in partfp.items():
        result = FPs.get(k,[])
        for r in result:
            for v in vlist: 
                d = np.abs(r[1] - v[1])
                song_id = r[0]
                match[song_id][d] += 1
                if match_heap[0][0] < match[song_id][d]:
                    tmp = [x[1] for x in match_heap]
                    if song_id not in tmp:
                        heapreplace(match_heap, (match[song_id][d],song_id,d*2048/22050))
                    elif match_heap[tmp.index(song_id)][0] < match[song_id][d]:
                        match_heap[tmp.index(song_id)] = (match[song_id][d],song_id,d*2048/22050)
    return match_heap
    
def compare_fingerprint2(FPs,m,partfp):
    # 只输出匹配率最高的一首歌和时间信息
    match = [defaultdict(int) for _ in range(m)]
    match_id = -1
    match_timediff = -1
    max_count = -1

    for k,vlist in partfp.items():
        result = FPs.get(k,[])
        for r in result:
            for v in vlist: 
                d = np.abs(r[1] - v[1])
                song_id = r[0]
                match[song_id][d] += 1
                if max_count < match[song_id][d]:
                    match_timediff = d
                    match_id = song_id
                    max_count = match[song_id][d]     
    match_timediff *= 2048/22050
    return match_id, match_timediff, max_count

def random_test_N(FPs,Songs,testpath, N, add_noise = 0, SNR = None):
    """
    从歌曲路径中随机选取N首歌的片段，加噪处理后进行匹配，输出测试结果
    """
    for root,dir,files in os.walk(testpath):
        testlist = rd.sample(files,k=N)
        suc = 0
        match_time = 0
        match_avgp = 0
        for name in testlist:
            testname = root + '/' + name
            print("test song: ",name)
            testsong, _ = librosa.load(testname)
            ni = rd.randint(8192, len(testsong) - D - 1)
            print("test start time: {}s".format(ni/22050))
            start = ni
            end = ni + D
            test = testsong[start:end]

            if add_noise:
                Ps = np.sum(test**2) / D
                noise = np.random.rand(D)
                Pn = np.sum(noise**2) / D
                k = np.sqrt(Ps/(Pn*(10**(SNR/10))))
                noise_SNR = k*noise
                test += noise_SNR

            partpath = curpath+'/TestPart/'+name
            sf.write(partpath,test,22050)
            time1 = time.time()
            fingerprint = calculate_fingerprint(-1,partpath)
            fingercount = sum(len(v) for v in fingerprint.values())
            print("test audio fingerhash count: ",fingercount)
            match_id, match_timediff, max_count = compare_fingerprint2(FPs,len(Songs.keys()),fingerprint)
            if Songs.get(match_id):
                match_song = Songs[match_id]
            else:
                match_song = 'NotFound'
            if match_song == name.split('.')[0] and abs(match_timediff - ni/22050) < 1:
                suc += 1
                match_avgp += max_count / fingercount
                print("match success")
            else:
                print("match failed")
            match_time += time.time() - time1
            print("match song: ",match_song)
            print("match start time:{}s".format(match_timediff))
            print("match fhash count: ",max_count)
            print("match percent: ",max_count / (fingercount+1))
            print("---------------------------------------")
    print("total test: {}, success {} ".format(N,suc))
    print("avg matcg percent: {}".format(match_avgp / suc))
    print("total assume time: {}".format(match_time))

class SongData():
    def __init__(self, path):
        self.Fingerprints = defaultdict(list)
        self.Songs = defaultdict(str)
        self.datapath = path
        self.load_fingerprint()

    def load_fingerprint(self):
        try:
            self.Fingerprints = np.load(self.datapath+'/Fingerprints.npy',allow_pickle=True).item()
            self.Songs = np.load(self.datapath+'/Songs.npy',allow_pickle=True).item()
        except:
            print('No Song')
            return

    def add_fingerprints(self, add_song_path):
        # 添加的歌曲放入MusicData文件夹下
        flag = 0
        newpath = ''
        cur_id = len(list(self.Songs.keys()))
        if add_song_path.endswith(".mp3"):
            head,tail = os.path.split(add_song_path)
            name = tail.split('.')[0]
            newpath = self.datapath+'/MusicData/'+tail
            if name not in self.Songs.values():
                # 复制歌曲到MusicData中方便播放
                if add_song_path != newpath:
                    os.system("copy "+add_song_path.replace('/','\\')+' '+newpath.replace('/','\\'))
                self.Songs[cur_id] = name
                fhash = calculate_fingerprint(cur_id,add_song_path)
                for k,v in fhash.items():
                    self.Fingerprints[k] += v
                flag = 1
                print("add success "+name)
            else:
                print("already exist")
        return flag,newpath

    def save_fingerprints(self):
        np.save(self.datapath+"/Fingerprints.npy",self.Fingerprints,allow_pickle=True)
        np.save(self.datapath+"/Songs.npy",self.Songs,allow_pickle=True)
        print("save done")

if __name__ == "__main__":
    SD = SongData(curpath)
    random_test_N(SD.Fingerprints,SD.Songs,curpath+'/MusicData',N,ADD_NOISE,SNR)

