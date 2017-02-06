# -*- coding: utf-8 -*-

import wave
from tkinter import *
from tkinter import filedialog
import numpy as np
import os
import struct


class Application(Frame):
    container = 0
    information = 0
    information_ext = 0
    information_ext_bits = ''
    information_ext_len = ''
    information_ext_len_bits = ''
    bytes_arr = []
    bytes_arr_len = 0
    bytes_arr_len_bits = 0
    maxInfo = 0
    infolen = 0
    infoLenTMP = 0
    infoString = ''
    infoHeader = 0
    maxFrames = 0

    def __init__(self, root):
        Frame.__init__(self, root, background="white")
        self.master.title('Steganography')
        self.maxInfoLabelText = StringVar()
        self.maxInfoLabelText.set("You can hide " + str(self.maxInfo) + " bites with LSB \nand  " +
                                  str(int(self.maxInfo/1024)) + " with echo data hiding")
        self.mainFrame = Frame(root).grid(row=0)
        self.fileFrame = Frame(root).grid(row=1)
        self.hideFrame = Frame(root)
        self.ButtonLSB = Button(self.hideFrame,
                                text="Use LSB",
                                command=lambda: self.lsb()).grid(column=1, row=5, sticky=E)
        self.ButtonEcho = Button(self.hideFrame,
                                 text="Use echo",
                                 command=lambda: self.echo()).grid(column=1, row=6, sticky=W)

        self.LabelContainerButton = Label(self.fileFrame, text="Chose container:")
        self.ContainerButton = Button(self.fileFrame, text="Chose container", command=lambda: self.openfile())
        self.LabelContainerButton.grid(row=1, column=0, sticky=E)
        self.ContainerButton.grid(row=1, column=1, sticky=W)

        self.LabelInfoButton = Label(self.fileFrame, text="Chose data to hide:")
        self.InfoButton = Button(self.fileFrame, text="Chose data to hide", command=lambda: self.open_any_file())
        self.LabelInfoButton.grid(row=2, column=0, sticky=E)
        self.InfoButton.grid(row=2, column=1, sticky=W)

        self.LabelHiddenButton = Label(self.fileFrame, text="Read hidden message")
        self.HiddenButton = Button(self.fileFrame, text="Chose file", command=lambda: self.odczytajukryte())
        self.LabelHiddenButton.grid(row=3, column=0, sticky=E)
        self.HiddenButton.grid(row=3, column=1, sticky=W)
        self.maxInfoLabel = Label(self.fileFrame, textvariable=self.maxInfoLabelText)
        self.maxInfoLabel.grid(column=0, row=4, sticky=W)

    def lsb(self):
        print("LSB METHOD START!")
        self.container.rewind()
        newFile = wave.open('output.wav', 'wb')
        newFile.setparams(self.container.getparams())
        newFile.setframerate(newFile.getframerate())

        ##############
        #   Hiding   #
        ##############

        for i in range(0, self.maxFrames, 1):
            frame = self.container.readframes(1)
            frame_int = int.from_bytes(frame, byteorder='big')
            if 1 <= i < 33:                                        # hiding length of data
                if int(self.bytes_arr_len_bits[i-1]) == 0:
                    frameNew = self.zero_lbs(frame_int)
                else:
                    frameNew = self.one_lsb(frame_int)

            elif 33 <= i <= 64:                                    # hiding extension length
                if int(self.information_ext_len_bits[i-33]) == 0:
                    frameNew = self.zero_lbs(frame_int)
                else:
                    frameNew = self.one_lsb(frame_int)

            elif 65 <= i <= 65 + self.information_ext_len:         # hiding extension
                if int(self.information_ext_bits[i-66]) == 0:
                    frameNew = self.zero_lbs(frame_int)
                else:
                    frameNew = self.one_lsb(frame_int)

            elif 66 + self.information_ext_len <= i <= 66 + self.information_ext_len + self.bytes_arr_len:
                if int(self.bytes_arr[i-67 - self.information_ext_len]) == 0:      # hiding data
                    frameNew = self.zero_lbs(frame_int)
                else:
                    frameNew = self.one_lsb(frame_int)

            else:
                frameNew = self.zero_lbs(frame_int)

            frame = frameNew.to_bytes(4, byteorder='big')
            newFile.writeframes(frame)

        print("Hiding witch LSB complete!")
        newFile.close()

    @staticmethod
    def zero_lbs(number):

        if number % 2 == 0:
            LSBZero = number
        else:
            LSBZero = number - 1

        return LSBZero

    @staticmethod
    def one_lsb(number):

        if number % 2 == 1:
            LSBOne = number
        else:
            LSBOne = number + 1
        return LSBOne

    def echo(self):

        print("ECHO METHOD START!")
        delay = 0.002  # in seconds

        ###########################
        #  Create copy with echo  #
        ###########################

        framerate = self.container.getframerate()
        frames = self.container.getnframes()
        channels = self.container.getnchannels()

        echo_data = self.container.readframes(frames)
        dataWithEcho = np.frombuffer(echo_data, dtype='h').reshape(-1, channels)

        echo_output = wave.open('echo.wav', 'wb')
        echo_output.setparams(self.container.getparams())

        for i in range(0, frames):
            if i > delay * framerate:
                arrayTmp = []
                value = dataWithEcho[i] + 0.1 * dataWithEcho[i - int(delay * framerate)]
                arrayTmp.append(int(value[0]))
                arrayTmp.append(int(value[1]))
                packed_value = struct.pack('hh', arrayTmp[0], arrayTmp[1])
            else:
                arrayTmp = []
                value = dataWithEcho[i]
                arrayTmp.append(value[0])
                arrayTmp.append(value[1])
                packed_value = struct.pack('hh', arrayTmp[0], arrayTmp[1])

            echo_output.writeframes(packed_value)

        echo_output.close()

        ####################
        #  Hiding in echo  #
        ####################

        Zero = self.container
        Zero.rewind()

        One = wave.open('echo.wav', 'rb')
        One.rewind()
        tmp = 0
        stego_echo = wave.open('output_echo.wav', 'wb')
        stego_echo.setparams(self.container.getparams())

        for i in range(self.container.getnframes()):
            if i == 0:
                FrameOne = One.readframes(1)
                Zero.readframes(1)
                frame_int = int.from_bytes(FrameOne, byteorder='big')
                frameNew = self.one_lsb(frame_int)
                frame = frameNew.to_bytes(4, byteorder='big')
                stego_echo.writeframes(frame)

            elif 1 <= i <= 32:                                      # hiding data length
                FrameOne = One.readframes(1024)
                FrameZero = Zero.readframes(1024)
                if int(self.bytes_arr_len_bits[tmp]) == 0:
                    stego_echo.writeframes(FrameZero)
                else:
                    stego_echo.writeframes(FrameOne)
                tmp += 1

            elif 33 <= i <= 64:                                      # hiding extension length
                FrameOne = One.readframes(1024)
                FrameZero = Zero.readframes(1024)
                if int(self.information_ext_len_bits[i-33]) == 0:
                    stego_echo.writeframes(FrameZero)
                else:
                    stego_echo.writeframes(FrameOne)

            elif 65 <= i <= 65 + self.information_ext_len:         # hiding extension
                FrameOne = One.readframes(1024)
                FrameZero = Zero.readframes(1024)
                if int(self.information_ext_bits[i-66]) == 0:
                    stego_echo.writeframes(FrameZero)
                else:
                    stego_echo.writeframes(FrameOne)

            elif 67 + self.information_ext_len <= i <= 67 + self.information_ext_len + self.bytes_arr_len:
                FrameOne = One.readframes(1024)                     # hiding data
                FrameZero = Zero.readframes(1024)
                if int(self.bytes_arr[i-68 - self.information_ext_len]) == 0:
                    stego_echo.writeframes(FrameZero)
                else:
                    stego_echo.writeframes(FrameOne)
            else:
                One.readframes(1024)
                FrameZero = Zero.readframes(1024)
                stego_echo.writeframes(FrameZero)

        stego_echo.close()
        print('Echo data hiding complete')

    def openfile(self):
        f = wave.open(filedialog.askopenfilename(filetypes=(("Audio Files", "*.wav"),
                                                            ("All files", "*.*"))), 'rb')
        self.container = f
        self.maxInfo = f.getnframes()
        self.maxInfoLabelText.set("You can hide " + str(self.maxInfo) + " bites with LSB \nand  " +
                                  str(int(self.maxInfo/1024)) + " with echo data hiding")
        print(self.maxInfoLabelText.get())
        self.maxFrames = self.container.getnframes()

        if self.container != 0 and self.information != 0:
            if self.maxInfo < self.infolen * 16:
                self.maxInfoLabelText.set('Container is to small')
            else:
                self.maxInfoLabel.grid_forget()
                self.hideFrame.grid(row=5, column=0, sticky=W)

    def infotobits(self, file_string):
        self.infoString = ""
        for i in range(self.infolen):
            stringbit = ''
            stringTMP = ''
            charTMP = int(ord(file_string[i]))
            for j in range(8):
                stringTMP += str(int(charTMP % 2))
                charTMP /= 2
            stringbit += stringTMP[15]
            stringbit += stringTMP[14]
            stringbit += stringTMP[13]
            stringbit += stringTMP[12]
            stringbit += stringTMP[11]
            stringbit += stringTMP[10]
            stringbit += stringTMP[9]
            stringbit += stringTMP[8]
            stringbit += stringTMP[7]
            stringbit += stringTMP[6]
            stringbit += stringTMP[5]
            stringbit += stringTMP[4]
            stringbit += stringTMP[3]
            stringbit += stringTMP[2]
            stringbit += stringTMP[1]
            stringbit += stringTMP[0]
            self.infoString += stringbit
            self.infolen = len(self.infoString)
        print(self.infoString)

    def odczytajukryte(self):
        self.bytes_arr = []
        self.infoString = ''
        howManyCharsInfo = ''
        howManyCharsExt = ''
        extBitString = ''
        infoBitString = ''
        ext = ''

        stegoFile = wave.open(filedialog.askopenfilename(filetypes=(("Audio Files", "*.wav"), ("All files", "*.*"))),
                              'rb')

        frame = stegoFile.readframes(1)
        frame = int.from_bytes(frame, byteorder='big')
        ukrytyBit = frame % 2

        if ukrytyBit == 0:
            print('\nInformation hidden with LSB')

            for i in range(0, 32):
                frame = stegoFile.readframes(1)
                frame = int.from_bytes(frame, byteorder='big')
                ukrytyBit = frame % 2
                howManyCharsInfo += str(ukrytyBit)

            for i in range(0, 32):
                frame = stegoFile.readframes(1)
                frame = int.from_bytes(frame, byteorder='big')
                ukrytyBit = frame % 2
                howManyCharsExt += str(ukrytyBit)

            ext_len = int(howManyCharsExt, 2)
            info_len = int(howManyCharsInfo, 2)
            stegoFile.readframes(1)

            for i in range(0, ext_len*8):
                frame = stegoFile.readframes(1)
                frame = int.from_bytes(frame, byteorder='big')
                ukrytyBit = frame % 2
                extBitString += str(ukrytyBit)
            self.information_ext = self.bits_to_ext(extBitString)
            frame = stegoFile.readframes(1)

            for i in range(0, info_len):
                frame = stegoFile.readframes(1)
                frame = int.from_bytes(frame, byteorder='big')
                ukrytyBit = frame % 2
                infoBitString += str(ukrytyBit)

            for i in range(len(infoBitString)):
                self.bytes_arr.append(infoBitString[i])

        else:
            print('\nInformation hidden with echo method')
            oldFile = wave.open(filedialog.askopenfilename(filetypes=(("Audio Files", "*.wav"), ("All files", "*.*"))),
                                'rb')
            oldFile.readframes(1)
            for i in range(0, 32):
                hiddenFrames = stegoFile.readframes(1024)
                oldFrames = oldFile.readframes(1024)
                if oldFrames == hiddenFrames:
                    howManyCharsInfo += '0'
                else:
                    howManyCharsInfo += '1'
            howManyCharsInfo = self.frombits(howManyCharsInfo)

            for i in range(0, 32):
                hiddenFrames = stegoFile.readframes(1024)
                oldFrames = oldFile.readframes(1024)
                if oldFrames == hiddenFrames:
                    howManyCharsExt += '0'
                else:
                    howManyCharsExt += '1'
            howManyCharsExt = self.frombits(howManyCharsExt)
            stegoFile.readframes(1024)
            oldFile.readframes(1024)

            for i in range(0, int(howManyCharsExt)*8):
                hiddenFrames = stegoFile.readframes(1024)
                oldFrames = oldFile.readframes(1024)
                if oldFrames == hiddenFrames:
                    ext += '0'
                else:
                    ext += '1'
            self.information_ext = self.bits_to_ext(ext)
            stegoFile.readframes(2048)
            oldFile.readframes(2048)

            for i in range(0, int(howManyCharsInfo)):
                hiddenFrames = stegoFile.readframes(1024)
                oldFrames = oldFile.readframes(1024)
                if oldFrames == hiddenFrames:
                    infoBitString += '0'
                else:
                    infoBitString += '1'

            for i in range(0, len(infoBitString)):
                self.bytes_arr.append(infoBitString[i])
            oldFile.close()

        file = open('newFileAfter.txt', 'w+')
        for i in range(len(self.bytes_arr)):
            string = 'byte_arr[' + str(i) + ']\t == \t' + str(self.bytes_arr[i]) + '\n'
            file.write(string)

        file.close()
        stegoFile.close()
        self.new_any_file()
        print(self.infoString)

    @staticmethod
    def tobits(x):
        bitstringpom = ''
        bitstring = ''
        for i in range(32):
            bitstringpom += str(x % 2)
            x = int(x / 2)

        for i in range(len(bitstringpom) - 1, -1, -1):
            bitstring += bitstringpom[i]

        return bitstring

    @staticmethod
    def frombits(x):
        return int(x, 2)

    def init(self):
        width = 400
        height = 400

        xwidth = self.winfo_screenwidth()
        yheight = self.winfo_screenheight()

        x = (xwidth / 2) - (width / 2)
        y = (yheight / 2) - (height / 2)
        self.master.geometry('%dx%d+%d+%d' % (width, height, x, y))

    def ext_to_bits(self, ext):
        bits = ''
        for i in range(len(ext), 0, -1):
            char = int(ord(ext[i-1]))
            for j in range(0, 8, 1):
                bit = int(char % 2)
                char /= 2
                bits += str(bit)

        for i in range(len(bits), 0, -1):
            self.information_ext_bits += bits[i-1]
        print(self.information_ext_bits)

    @staticmethod
    def bits_to_ext(bits):
        ext = ''
        char_tmp = ''
        for i in range(1, len(bits)+1):
            char_tmp += bits[i-1]
            if i % 8 == 0:
                ext += chr(int(char_tmp, 2))
                char_tmp = ''
        return ext

    def open_any_file(self):

        self.bytes_arr = []
        filename_ext = filedialog.askopenfilename()
        filename, file_extension = os.path.splitext(filename_ext)
        print(file_extension)
        file = open(filename_ext, 'rb')
        self.information_ext = file_extension
        self.ext_to_bits(self.information_ext)
        self.information_ext_len = len(self.information_ext)*8
        self.information_ext_len_bits = self.tobits(len(self.information_ext))

        while True:
            data = file.read(1)
            if not data:
                break
            else:
                byte = data
                byte_int = int.from_bytes(byte, byteorder='big')
                x = self.tobits(byte_int)
                for i in range(32):
                    self.bytes_arr.append(str(x)[i])
        self.bytes_arr_len = len(self.bytes_arr)
        self.bytes_arr_len_bits = self.tobits(len(self.bytes_arr))
        file.close()

        self.information = 1

        file = open('newFileBefore.txt', 'w+')
        for i in range(len(self.bytes_arr)):
            string = 'byte_arr[' + str(i) + ']\t == \t' + str(self.bytes_arr[i]) + '\n'
            file.write(string)

        file.close()

        if self.container != 0 and self.information != 0:
            if self.maxInfo < self.infolen * 16:
                self.maxInfoLabelText.set('Container is to small')
            else:
                self.maxInfoLabel.grid_forget()
                self.hideFrame.grid(row=5, column=0, sticky=W)

    def new_any_file(self):
        newFilename = 'steganography_output' + self.information_ext
        file_output = open(newFilename, 'wb+')
        bits = ''
        for i in range(1, len(self.bytes_arr) + 1):
            bits += str(self.bytes_arr[i - 1])
            if i % 32 == 0:
                data = self.frombits(bits).to_bytes(1, byteorder='big')
                bits = ''
                file_output.write(data)
        print("information decoded")
        file_output.close()

    def compare_files(self):                 # debugging hidden data before and after steganography

        fileBefore = open('newFileBefore.txt', 'r')

        fileAfter = open('newFileAfter.txt', 'r')

        for i in range(len(self.bytes_arr)):
            while True:
                dataBefore = fileBefore.readline()
                dataAfter = fileAfter.readline()
                if not dataBefore or not dataAfter:
                    break
                else:
                    if dataAfter != dataBefore:
                        string = 'dataAfter: ' + dataAfter + '\tdataBefore' + dataBefore
                        print(string)

        fileBefore.close()
        fileAfter.close()


class main:
    @staticmethod
    def window():
        program = Tk()
        app = Application(program)
        app.init()
        program.resizable(width=FALSE, height=FALSE)

        app.mainloop()


if __name__ == '__main__':
    main.window()
