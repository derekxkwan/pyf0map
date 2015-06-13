from __future__ import division
from scipy.io import wavfile
import amfm_decompy.pYAAPT as pyaapt
import amfm_decompy.basic_tools as basic
import numpy as np
import sys
import os.path as pth

class voiceToInst():
	def __init__(self, inputSound, targetSound):
		self.inputSound = basic.SignalObj(inputSound)
		self.inputFs = self.inputSound.fs
		#self.inputPitch = pyaapt.yaapt(self.inputSound, **{'f0-min': 75.0, 'f0-max': 500.0, 'frame_length':15.0, 'frame_space': 10.0})
		self.inPutPitch = pyaapt.yaapt(self.inputSound)
		self.inputF0 = self.inputPitch.values
		self.targetF0 = self.avgTargetF0(targetSound)
		self.targetFs, self.targetSound = wavfile.read(targetSound)
		self.resampleInputF0()
		self.na = None
		self.relateF0()
		self.zeroThresh = 5 #number of 0s in na factor array to count as a break in between input sound words

	def resampleInputF0(self):
		#resamples inputF0 from original fs to target fs
		if self.inputFs != self.targetFs:
			factor = self.inputFs/self.targetFs
			indices = np.round(np.arange(0, len(self.inputF0), factor))
			indices = indices[indices < len(self.inputF0)].astype(int)
			self.inputF0 = self.inputF0[indices.astype(int)]

	def avgTargetF0(self, targetSound):
		ipt = basic.SignalObj(targetSound)
		pch = pyaapt.yaapt(ipt, **{'frame_length':30.0, 'f0-min': 10.0, 'f0-max': 300.0, 'frame_space': 20.0})
		nonZero = filter(lambda x: x > 0, pch.values)
		print(np.mean(nonZero))
		return np.mean(nonZero)

	def relateF0(self):
		#convert from absolute Hz in inputF0 to ratio with targetF0 for factor array (na)
		self.na = np.divide(self.inputF0, self.targetF0)
		#self.na = filter(lambda x: x >0, self.na)

	def speedx(self, sound_array, factor):
		""" Multiplies the sound's speed by some `factor` """
		indices = np.round( np.arange(0, len(sound_array), factor) )
		indices = indices[indices < len(sound_array)].astype(int)
		return sound_array[ indices.astype(int) ]
	
	
	def stretch(self, window_size, h):
		""" Stretches the sound by a factor `f` """
		phase  = np.zeros(window_size)
		hanning_window = np.blackman(window_size)
		result = np.zeros( len(self.na))
		j = 0
		i = 0
		zeroCount = 0
		while j < len(self.na):
			if self.na[j] != 0:
				if zeroCount != 0:
					zeroCount = 0
	 			#f = 1/(2**(1.0 * self.na[j] / 12.0))
				f = 1/self.na[j]
				# two potentially overlapping subarrays
				
				a1 = self.targetSound[i: i + window_size]
				a2 = self.targetSound[i + h: i + window_size + h]
				
				# resynchronize the second array on the first
				#print("winSize: %f, a2Size: %f" % (np.shape(hanning_window)[0], np.shape(a2)[0]))
				s1 =  np.fft.fft(hanning_window * a1)	
				s2 =  np.fft.fft(hanning_window * a2)
				phase = (phase + np.angle(s2/s1)) % 2*np.pi
				a2_rephased = np.fft.ifft(np.abs(s2)*np.exp(1j*phase))
				resid = a2 - a2_rephased
				to_speed = a2_rephased+(resid*0.25)
				speedFactor = 1/f
				if speedFactor < 0.001:
					speedFactor = 1
				addBack = self.speedx(to_speed, speedFactor)
				newWin = np.hanning(addBack.shape[0])
				addBack *= newWin
				#print addBack.shape[0]

				# add to result
				#i2 = int(i/f)
				i2 = j
				diff = len(addBack) - (len(result)-i2)
				if diff > 0:
					result = np.pad(result, (0, diff), 'constant', constant_values=(0))
				#print("addBack: %f, resultLeft: %f" % (addBack.shape[0], len(result)-i2))
				result[i2 : i2 + addBack.shape[0]] += addBack
				i += h*f
			else:
				zeroCount += 0
				if (zeroCount > self.zeroThresh) and (i != 0):
					i=0
			j += h
			
		result = ((2**(16-4)) * result/result.max()) # normalize (16bit)
	
		return result.astype('int16')
	
	def pitchshift(self, window_size=2**12, h=2**5):
		""" Changes the pitch of a sound by ``n`` semitones. """
		#factor = 2**(1.0 * n / 12.0)
		stretched = self.stretch(window_size, h)
		return stretched[window_size:]

x = voiceToInst(sys.argv[1], sys.argv[2])
transposed = x.pitchshift()

outName = sys.argv[1].split('.')[0] + 'out-0.wav'

while pth.isfile(outName) == True:
	nameSpl = outName.split('out-')
	outName = nameSpl[0]+'out-'+str(int(nameSpl[1][0]) + 1) + '.wav'

wavfile.write(outName, x.targetFs, transposed)
