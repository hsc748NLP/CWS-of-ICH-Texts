import sys
import os
import shutil
from collections import Counter
from wordcloud import WordCloud
import matplotlib.pyplot as plt
from matplotlib.font_manager import FontProperties
from PyQt5 import QtGui, QtCore
from PyQt5.QtWidgets import QApplication, QMainWindow, QFileDialog
import MainWindow
import AutosegWindow
import AnalysisWindow
from roberta_6 import wordsegall_txt

font = FontProperties(fname=r"Fonts\simhei.ttf")


'''
如果需要导入其他项目中的模块，
在本py文件最上方添加
sys.path.append("../")
sys.path.append("../项目所在文件夹路径")
'''

fileArray = r''  # 存储读取文件路径


class MyMainwin(QMainWindow, MainWindow.Ui_MainWindow):  # 主窗口
    def __init__(self):
        super(MyMainwin, self).__init__()
        self.setupUi(self)
        self.setWindowFlags(QtCore.Qt.WindowCloseButtonHint)  # 仅保留关闭按钮
        self.setFixedSize(self.width(), self.height())  # 固定窗口大小
        self.setWindowIcon(QtGui.QIcon(r'logo.ico'))
        self.txt_list = []  # 存取读入的全部原始文本
        self.all_tokens = []  # 存取token形式待标注文本

        # 信号与槽
        self.pushButton.clicked.connect(self.open_directory)  # 读取文件夹
        self.pushButton_2.clicked.connect(self.data_preprocess)  # 数据预处理
        self.pushButton_4.clicked.connect(self.open_autosegwin)  # 打开自动分词子窗口
        self.pushButton_5.clicked.connect(self.open_analysiswin)  # 打开数据分析子窗口

        # 实例化子窗口
        self.autosegwin = Autosegwin()  # 实例化自动分词子窗口
        self.analysiswin = Analysiswin()  # 实例化数据分析子窗

    def closeEvent(self, event):  # 点击右上角关闭后，所有关联子窗口均关闭
        sys.exit(0)

    def open_directory(self):
        global fileArray
        dir_path = r'{}'.format(QFileDialog.getExistingDirectory(self, '打开文件夹', '.'))
        # print(dir_path)
        self.lineEdit.setText(dir_path)  # 将文件夹路径传入lineEdit
        fileArray = fun(dir_path)  # 遍历文件夹
        self.txt_list = []
        for path in fileArray[:5]:  # 展示前5个文件
            lines = reader(path)
            self.txt_list.extend(lines)
        ex_txt = '语料库样例：\n' + '\n'.join([each.strip() for each in self.txt_list if each.strip()])
        self.textEdit.setText(ex_txt)  # 选取前10行文本传入textEdit

    def data_preprocess(self):  # 将语料转化为token格式
        global fileArray
        self.textEdit.setText('正在转换语料格式，请等候...')
        QApplication.processEvents()  # 实时刷新页面
        self.txt_list = []
        if os.path.exists('./temp'):
            shutil.rmtree('./temp')  # 清空缓存文件夹
        os.mkdir('./temp')
        for path in fileArray:
            outs = []
            filename = path.split('\\')[-1].split('.')[0]
            # print(filename)
            lines = reader(path)
            self.txt_list.extend(lines)
            for para in lines:
                para = para.replace('\u3000', '').replace('\t', '').replace(' ', '').replace('。', '。$').strip()
                if para:
                    line_list = [[item + '\tB-tag' for item in list(line)] for line in para.split('$') if line]
                    outs.extend(line_list)
                # para = para.replace('\u3000', '').replace('\t', '').replace(' ', '').strip()
                # if para:
                #     self.all_tokens.append(list(para))
            out_path = r'./temp/' + filename + '_token.txt'
            output(out_path, outs)  # 在temp目录下保存token格式文本
        ex_txt = '格式转换完成，请点击“自动分词”以继续...'
        self.textEdit.append(ex_txt)  # 选取前5个句子传入textEdit

    def open_autosegwin(self):
        self.autosegwin.show()
        # 将读取的语料库原始文本全部文本传入textEdit
        self.autosegwin.textEdit.setText('\n'.join([each.strip() for each in self.txt_list if each.strip()]))

    def open_analysiswin(self):
        self.analysiswin.show()


word_list = []  # 存储自动分词后的全部词汇
word_list_no_stop = []  # 存储自动分词后的去停用词后词汇


class Autosegwin(QMainWindow, AutosegWindow.Ui_MainWindow):  # 自动分词窗口
    def __init__(self):
        super(Autosegwin, self).__init__()
        self.setupUi(self)
        self.setWindowFlags(QtCore.Qt.WindowCloseButtonHint)  # 仅保留关闭按钮
        self.setFixedSize(self.width(), self.height())  # 固定窗口大小
        self.setWindowIcon(QtGui.QIcon(r'logo.ico'))
        self.pushButton_2.clicked.connect(self.open_write_dir)  # 读取保存路径
        self.pushButton.clicked.connect(self.auto_tag)  # 调用模型自动分词
        self.out_dir = r'./'  # 存储文件输出路径

    # 读取输出文件夹路径
    def open_write_dir(self):
        dir_path = r'{}'.format(
            QFileDialog.getExistingDirectory(self, '选择文件保存路径', '.'))  # "." 代表程序运行目录，"/" 代表当前盘符的根目录
        # print('文件输出路径：{}'.format(dir_path))
        self.lineEdit.setText(dir_path)  # 将文件夹路径传入lineEdit_in
        self.out_dir = dir_path + '/'  # 路径存入 self.out_dir

    def auto_tag(self):
        global word_list
        if os.path.exists('./out'):
            shutil.rmtree('./out')  # 清空缓存文件夹
        os.mkdir('./out')
        if self.radioButton.isChecked():
            # print('CRF')
            self.crf_tag()

        elif self.radioButton_2.isChecked():
            # print('RoBERTa')
            self.roberta_tag()

        global word_list_no_stop  # 为数据分析模块做准备
        # 读取停用词表
        stopwords_path = r'stopwords.txt'
        stopwords = reader(stopwords_path)
        stopword_list = [each.strip() for each in stopwords if each.strip()]
        # 去停用词
        word_list_no_stop = []
        for word in word_list:
            if word not in stopword_list:
                word_list_no_stop.append(word)

    def crf_tag(self):
        self.textEdit_2.setText('CRF分词中...')
        QApplication.processEvents()  # 实时刷新页面
        global word_list
        fileArray = fun('./temp')
        os.chdir(r'crf')
        # print(os.getcwd())
        for path in fileArray:
            filename = path.split('\\')[-1]
            # print(filename)
            cmd = 'crf_test -m model6 ../temp/' + filename + ' > ../out/' + filename.replace('_token', '_output')
            os.system(r'{}'.format(cmd))
            self.textEdit_2.append('文件 {} 已分词...'.format(filename.replace('_token', '')))
            QApplication.processEvents()  # 实时刷新页面
        os.chdir(r'../')
        # print(os.getcwd())
        outfileArray = fun('./out')
        all_line = []
        word_list = []
        for path in outfileArray:
            filename = path.split('\\')[-1]
            # print(filename)
            outpath = self.out_dir + filename.replace('_output', '_分词后')  # 保存路径
            outlines = []  # 存储待输出至文件文本
            lines = reader(path)
            tokens = get_tokens(lines)
            word = ''
            for temp in tokens:
                line = ''
                for token in temp:
                    char = token.split('\t')[0]
                    # line += char
                    ind = token.split('\t')[-1].split('-')[0]
                    if ind == 'B' or ind == 'M':
                        line += char
                        word += char
                    elif ind == 'E' or ind == 'S':
                        line += char + '/'
                        word += char
                        word_list.append(word)
                        word = ''
                outlines.append(line)
                all_line.append(line)
            texts = ''.join(outlines)
            outfile(outpath, texts)
        self.textEdit_2.append('\n'.join(all_line))  # 显示分词后文本
        QApplication.processEvents()  # 实时刷新页面

    def roberta_tag(self):
        self.textEdit_2.setText('RoBERTa分词中...')
        QApplication.processEvents()  # 实时刷新页面
        global word_list
        all_line = []
        word_list = []
        fileArray = fun('./temp')
        for path in fileArray:
            filename = path.split('\\')[-1]
            # print(filename)
            wordsegall_txt.process_txt(raw_path=path, output='./out/labeled_results.txt', max_seq_length=128, eval_batch_size=8)

            outpath = self.out_dir + filename.replace('_token', '_分词后')  # 保存路径
            outlines = []  # 存储待输出至文件文本
            lines = reader('./out/labeled_results.txt')
            tokens = get_tokens(lines)
            word = ''
            for temp in tokens:
                line = ''
                for token in temp:
                    char = token.split('\t')[0]
                    # line += char
                    ind = token.split('\t')[-1].split('-')[0]
                    if ind == 'B' or ind == 'I':
                        line += char
                        word += char
                    elif ind == 'E' or ind == 'S':
                        line += char + '/'
                        word += char
                        word_list.append(word)
                        word = ''
                outlines.append(line)
                all_line.append(line)
            texts = ''.join(outlines)
            outfile(outpath, texts)
            self.textEdit_2.append('文件 {} 已分词...'.format(filename.replace('_token', '')))
            QApplication.processEvents()  # 实时刷新页面
        self.textEdit_2.append(''.join(all_line))  # 显示分词后文本
        QApplication.processEvents()  # 实时刷新页面


class Analysiswin(QMainWindow, AnalysisWindow.Ui_MainWindow):  # 数据分析窗口
    def __init__(self):
        super(Analysiswin, self).__init__()
        self.setupUi(self)
        self.setWindowFlags(QtCore.Qt.WindowCloseButtonHint)  # 仅保留关闭按钮
        self.setFixedSize(self.width(), self.height())  # 固定窗口大小
        self.setWindowIcon(QtGui.QIcon(r'logo.ico'))
        self.pushButton.clicked.connect(self.count_len_freq)  # 统计词长
        self.pushButton_2.clicked.connect(self.count_word_freq)  # 统计词频
        self.pushButton_3.clicked.connect(self.word_cloud)  # 生成词云

    def count_len_freq(self):  # 统计词长分布
        global word_list_no_stop
        len_list = []
        for word in word_list_no_stop:
            length = len(word)
            len_list.append(length)
        len_count = count_freq(len_list, 0, False)
        # print(len_count)
        # self.label.setText(str(len_count))
        x = [each[0] for each in len_count[:10]]
        y = [each[1] for each in len_count[:10]]
        plt.plot(x, y)
        # plt.xticks(range(len(y)), x, fontproperties=font)
        # plt.show()
        plt.savefig(r'plot.png')
        plt.close()
        # 读取图片并传入前端label
        jpg = QtGui.QPixmap(r'plot.png').scaled(self.label.width(), self.label.height())
        self.label.setPixmap(jpg)

    def count_word_freq(self):  # 统计词频分布
        global word_list_no_stop
        word_count = count_freq(word_list_no_stop, 1)
        # print(word_count)
        # self.label.setText(str(word_count))
        x = [each[0] for each in word_count[:10]]
        y = [each[1] for each in word_count[:10]]
        plt.bar(range(len(y)), y)
        plt.xticks(range(len(y)), x, fontproperties=font)
        # plt.show()
        plt.savefig(r'bar.png')
        plt.close()
        # 读取图片并传入前端label
        jpg = QtGui.QPixmap(r'bar.png').scaled(self.label.width(), self.label.height())
        self.label.setPixmap(jpg)

    def word_cloud(self):
        global word_list_no_stop
        word_count = count_freq(word_list_no_stop, 1)
        freq_dict = {}
        for each in word_count:
            freq_dict[each[0]] = int(each[1])
        # 生成词云并保存
        wc = WordCloud(font_path=r"Fonts\simhei.ttf", background_color="white", max_words=500, scale=1, width=800, height=600)
        wc.generate_from_frequencies(freq_dict)
        wc.to_file(r'wordcloud.png')
        # 读取图片并传入前端label
        jpg = QtGui.QPixmap(r'wordcloud.png').scaled(self.label.width(), self.label.height())
        self.label.setPixmap(jpg)


def fun(path):
    fileArray=[]
    for root,dirs,files in os.walk(path):
        for fn in files:
            eachpath=str(root+'\\'+fn)
            fileArray.append(eachpath)
    return fileArray


def reader(path):
    with open(path, 'r', encoding='utf-8') as f:
        lines = f.readlines()
        return lines


def output(path,tokens):
    with open(path,'wb') as f:
        for temp in tokens:
            for token in temp:
                txt = token + '\n'
                txt = txt.encode('utf-8')
                f.write(txt)
            enter = '\n'
            enter = enter.encode('utf-8')
            f.write(enter)


def outfile(path, texts):
    with open(path, 'w', encoding='utf-8') as f:
        f.write(texts + '\n')


def get_tokens(lines):
    tokens = []
    temp = []
    for i, line in enumerate(lines):
        line = line.strip()
        if line:
            temp.append(line)
        else:
            if temp:
                tokens.append(temp)
                temp = []
    if temp:
        tokens.append(temp)  # 防止最后一句加不进来
    # print('tokens len:', len(tokens))
    return tokens


def count_freq(d_list, n, rev=True):
    c_dict = dict(Counter(d_list))
    d_count = sorted(c_dict.items(), key=lambda x: x[n], reverse=rev)
    return d_count


if __name__ == '__main__':
    app = QApplication(sys.argv)
    MainWindow = MyMainwin()
    MainWindow.show()
    sys.exit(app.exec_())