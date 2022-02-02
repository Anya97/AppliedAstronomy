'''
Basic lib for reading base files v 0.3
Parsing file headers and reading one or all channels at once
More or less pep8 formatted
Will ad some docs when it'll be bug free.

import struct
import array
import numpy as np


def updateHeader(fn='', AP=0):
    if fn == '':
        print 'basefile error: no file to load'
        return None
    global df
    with open(fn, 'r+b') as df:
        df.seek(84)
        df.write(struct.pack('i', AP))
    print ' header updated, check filesize.'
# WARNING only base files ver 1.2+ are supported


# We'll test the speed later for now 'as is'
# do we need a simple header to be returned from here?
# will be added later
# loadSingle should be used only for huge files, to prevent RAM overflow.
def loadSingle(fn='', ch=0):
    if fn == '':
        print 'basefile error: no file to load'
        return None
    # WARNING only base files ver 1.2+ are supported
    print 'basefile: working with %s for %d channel' % (fn, ch)
    # file handler across all functions
    global df
    with open(fn, 'rb') as df:
        chans, res, periods, = parseHeader()[0:3]  # only the first three needed
        print ' basefile: data dimensions in file are', chans, res, periods
        # preparing arrays, need a check if data is really should be global
        # global data
        data = np.zeros((periods, res), dtype=np.complex)
        print ' prepared array shape is:', data.shape
        # N[chans] channel spectra with M[res] for each AP[periods], another N channels after!
        # 1st AP: |ch0 * nFFT|ch1 * nFFT|..|chN * nFFT|
        # ...
        # Nth AP: |ch0|ch1|..|chN|
        # Each nFFT position contain two floats (4 byte) complex(re, im)
        # OMG no eof exceptions on read(), stay sharp, not to catch garbage data in arrays!
        if ch + 1 > chans:
            print 'basefile error: selected channel is out of bounds!'
            return None
        # Loading data
        for x in range(periods):
            for z in range(chans):
                if z == ch:
                    for y in range(res):
                        # print x, y, z debug only
                        data[x, y] = \
                            complex(struct.unpack('f', df.read(4))[0],
                                    struct.unpack('f', df.read(4))[0])
                else:
                    df.read(8 * res)  # Two floats [4byte] * res to skip a channel AP
    print 'basefile: array read data is ready.'
    return data


# will return [nChannels][mAPs][qFFT]
def loadMulti(fn='', dbg=False):
    if fn == '':
        print 'basefile error: no file to load'
        return None
    # WARNING: only base files ver 1.2+ are supported atm
    if dbg is True:
        print 'basefile: working with %s, loading all channels' % fn
    # file handler across all functions
    global df
    with open(fn, 'rb') as df:
        chans, res, periods, sess, ascan, ast1, ast2, year, day, hour, minute, second = \
            parseHeader(dbg)  # only the first three needed
        # preparing arrays, need a check if data is really should be global - nope
        # global data
        data = np.zeros((chans, periods, res), dtype=np.complex)
        '''
        need a check if this is equal!
        checked!
        for x in range(periods):
            for z in range(chans):
                for y in range(res):
                    data[z, x, y] = \
                        complex(struct.unpack('f', df.read(4))[0],
                                struct.unpack('f', df.read(4))[0])
        !CHEKED!
        '''
        ad = array.array('f')
        ad.fromfile(df, chans * res * periods * 2)
        # print len(ad) debug purpose only
        for z in range(chans):
            for i in range(periods):
                for j in range(res):
                    datIdx = chans * res * 2 * i + z * res * 2 + j * 2
                    data[z, i, j] = \
                        complex(ad[datIdx], ad[datIdx + 1])  # im and re swapped!
                    # There may be another swap, in storage block possibly, seems fine now :)
    if dbg is True:
        print 'basefile: array read data is ready.'
    return (data, chans, res, periods, sess, ascan, ast1, ast2, year, day, hour, minute, second)


# basic filter for base file
def filterBasefile(fn='', tocut=512, dbg=False):
    if fn == '':
        print 'basefile error: no file to load'
        return None
    # WARNING: only base files ver 1.2+ are supported atm
    if dbg is True:
        print 'basefile: working with %s, loading all channels' % fn
    # file handler across all functions
    global df
    with open(fn, 'r+b') as df:  # we'll update files without copy, be carefull!
        chans, res, periods, sess, ascan, ast1, ast2, year, day, hour, minute, second = \
            parseHeader(dbg)  # only the first three needed
        ad = array.array('f')
        ad.fromfile(df, chans * res * periods * 2)
        # print len(ad) debug purpose only
        for z in range(chans):
            for i in range(periods):
                for j in range(res):
                    if j < tocut or j > res - tocut:
                        datIdx = chans * res * 2 * i + z * res * 2 + j * 2
                        ad[datIdx] = 0.
                        ad[datIdx + 1] = 0.
        df.seek(112)
        ad.tofile(df)
    if dbg is True:
        print 'basefile: array read and filtered'
    # May be other return values, for now just None or tocat & header
    return (tocut, chans, res, periods, sess, ascan, ast1, ast2, year, day, hour, minute, second)


# basic header parser, we should add different base versions later on
def parseHeader(dbg=False):
    # TODO: Implement basefile version < 1.2 header
    if dbg is True:
        print 'basefile: attempting to read header data'
    # our favorite binary seporator is \x00 (c-string end sign)
    ver = str(df.read(8)).strip('\x00')
    sess = str(df.read(20)).strip('\x00')
    nscan, = struct.unpack('i', df.read(4))
    ascan = str(df.read(20)).strip('\x00')
    ist1, = struct.unpack('i', df.read(4))
    ast1 = str(df.read(4)).strip('\x00')
    pol1, = struct.unpack('i', df.read(4))
    ist2, = struct.unpack('i', df.read(4))
    ast2 = str(df.read(4)).strip('\x00')
    pol2, = struct.unpack('i', df.read(4))
    chans, = struct.unpack('i', df.read(4))
    res, = struct.unpack('i', df.read(4))
    periods, = struct.unpack('i', df.read(4))
    # print ' Header size till AP is:', df.tell() debug purpose only
    # timestruct here, I guess no need for creating structure yet
    year, = struct.unpack('i', df.read(4))
    day, = struct.unpack('i', df.read(4))
    hour, = struct.unpack('i', df.read(4))
    minute, = struct.unpack('i', df.read(4))
    second, = struct.unpack('i', df.read(4))
    samplesP, = struct.unpack('i', df.read(4))
    if dbg is True:
        print ' Base file version:', str(ver)
        print ' Session name:', sess
        print ' Scan number', nscan
        print ' Scan name:', ascan
        print ' Station 1:', ist1, ast1, pol1
        print ' Station 2:', ist2, ast2, pol2
        print ' Base file parameters:'
        print ' Channels:', chans
        print ' Spectrum resolution:', res  # so called D
        print ' Accumulation Periods inside base file:', periods  # so called P
        print ' Timestamp: %04d.%03d.%02d:%02d:%02d:%d' \
            % (year, day, hour, minute, second, samplesP)
    # May be we'll update this later if we'll need more data in other functions
    # for now just some absolutly must values: sess, ascan, ast1, ast2, chans, res, periods
    # if you need more, just add, be shure not to change order, for other scripts to work
        # print 'Header offset is:', df.tell()
    return (chans, res, periods, sess, ascan, ast1, ast2, year, day, hour, minute, second)
