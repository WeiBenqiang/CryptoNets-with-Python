
# A wrapper for the SEAL library. The wrapper can support basic operations such as
# encoding, decoding and squaring, as mush as initializing variables, genereting new keys
# and freeing memory.

import ctypes
import numpy as np
import os.path

class SEAL:

	def __init__(self):
		self.lib = ctypes.cdll.LoadLibrary('./SEAL/libseal.so')
		for i in range(5):
			if (not (
				os.path.isfile("./keys/evaluation-"+str(i))
				and os.path.isfile("./keys/public-"+str(i))
				and os.path.isfile("./keys/secret-"+str(i))
				)):
				print("Key missing: generating new keys...")
				self.lib.generate_new_keys()
				print("Done.")
				break
		self.lib.initialize()
		self.lib.square_tensor.argtypes = [ctypes.POINTER(ctypes.c_uint64), ctypes.POINTER(ctypes.c_uint64), ctypes.c_int, ctypes.c_int]
		self.lib.encrypt_tensor.argtypes = [ctypes.POINTER(ctypes.c_uint64), ctypes.POINTER(ctypes.c_uint64), ctypes.c_int, ctypes.c_int]
		self.lib.decrypt_tensor.argtypes = [ctypes.POINTER(ctypes.c_uint64), ctypes.POINTER(ctypes.c_uint64), ctypes.c_int, ctypes.c_int]
		self.lib.k_list.argtypes = [ctypes.POINTER(ctypes.c_uint64)]

		self.k_list = []
		k_list_c_vector = (ctypes.c_uint64 * 20)()
		self.lib.k_list(k_list_c_vector)
		for t in range(5):
			k_list_row = []
			for k in range(4):
				k_list_row.append(int(k_list_c_vector[(t*4)+k]))
			self.k_list.append(k_list_row)
		k_list_c_vector = None
		k_list_row = None

		self.q_list = [36028797014376449, 36028797013327873, 1152921504241942529, 1152921504369344513]

		self.n_parm = 4096

		self.enc_poly_size = (self.n_parm + 1) * len(self.q_list) * 2 # (n + 1) * q_size * 2

	def generate_new_keys(self):
		self.lib.generate_new_keys()

	def encrypt_tensor(self, input_tensor):
		shape = input_tensor.shape
		assert shape[-1] == 5, "Error while encrypting a tensor:\n\tinput_tensor should has size[-1] = 5"

		# compute sizes
		input_size = input_tensor.size
		input_axis0_size = shape[0]
		data_size = input_size // input_axis0_size # ignore first dimension in input_tensor.shape
		poly_groups_count = input_axis0_size // self.n_parm
		if ((input_axis0_size % self.n_parm) != 0):
			poly_groups_count = poly_groups_count + 1
		output_axis0_size = poly_groups_count * self.enc_poly_size
		output_size = output_axis0_size * data_size
		data_size = data_size // 5 # ignore last dimension in input_tensor.shape too

		# lib function call
		input_tensor.shape = (input_size,)
		input_c_vector = (ctypes.c_uint64 * (input_size))()
		for i in range(input_size):
			input_c_vector[i] = input_tensor[i]
		output_c_vector = (ctypes.c_uint64 * (output_size))()
		self.lib.encrypt_tensor(input_c_vector, output_c_vector, input_axis0_size, data_size)

		# compute output_tensor
		output_tensor = np.empty((output_size), dtype=np.uint64)
		for i in range(output_size):
			output_tensor[i] = output_c_vector[i]
		shape = (output_axis0_size,) + shape[1:] # output shape
		output_tensor.shape = shape
		input_c_vector = None
		output_c_vector = None
		input_tensor = None
		return output_tensor

	def decrypt_tensor(self, input_tensor, output_axis0_size=10000):
		shape = input_tensor.shape
		assert (shape[0] % self.enc_poly_size) == 0, "Error while decrypting a tensor:\n\tinput_tensor should have size[0] multiple of (" + str(self.n_parm) + " + 1) * " + str(len(self.q_list)) + " * 2 = " + str(self.enc_poly_size)
		assert shape[-1] == 5, "Error while decrypting a tensor:\n\tinput_tensor should has size[-1] = 5"
		assert ((shape[0] // self.enc_poly_size) * 4096) >= output_axis0_size, "Error while decrypting a tensor:\n\toutput_axis0_size too big"

		# compute sizes
		input_size = input_tensor.size
		input_axis0_size = shape[0]
		data_size = input_size // input_axis0_size # ignore first dimension in input_tensor.shape
		output_size = output_axis0_size * data_size
		data_size = data_size // 5 # ignore last dimension in input_tensor.shape

		# lib function call
		input_tensor.shape = (input_size,)
		input_c_vector = (ctypes.c_uint64 * (input_size))()
		for i in range(input_size):
			input_c_vector[i] = input_tensor[i]
		output_c_vector = (ctypes.c_uint64 * (output_size))()
		self.lib.decrypt_tensor(input_c_vector, output_c_vector, output_axis0_size, data_size)

		# compute output_tensor
		output_tensor = np.empty((output_size), dtype=np.uint64)
		for i in range(output_size):
			output_tensor[i] = output_c_vector[i]
		shape = (output_axis0_size,) + shape[1:] # output shape
		output_tensor.shape = shape
		input_c_vector = None
		output_c_vector = None
		input_tensor = None
		return output_tensor

	def square_tensor(self, input_tensor):
		shape = input_tensor.shape
		assert (shape[0] % self.enc_poly_size) == 0, "Error while squaring a tensor:\n\tinput_tensor should have size[0] multiple of (" + str(self.n_parm) + " + 1) * " + str(len(self.q_list)) + " * 2 = " + str(self.enc_poly_size)
		assert shape[-1] == 5, "Error while squaring a tensor:\n\tinput_tensor should has size[-1] = 5"

		# compute sizes
		input_size = input_tensor.size
		input_axis0_size = shape[0]
		data_size = input_size // input_axis0_size # ignore first dimension in input_tensor.shape

		# lib function call
		input_tensor.shape = (input_size,)
		input_c_vector = (ctypes.c_uint64 * (input_size))()
		for i in range(input_size):
			input_c_vector[i] = input_tensor[i]
		output_c_vector = (ctypes.c_uint64 * (input_size))()
		data_size = data_size // 5 #adegua data size allo standard del wrap in c++
		self.lib.square_tensor(input_c_vector, output_c_vector, input_axis0_size, data_size)

		# compute output_tensor
		output_tensor = np.empty((input_size), dtype=np.uint64)
		for i in range(input_size):
			output_tensor[i] = output_c_vector[i]
		output_tensor.shape = shape
		input_c_vector = None
		output_c_vector = None
		input_tensor = None
		return output_tensor

	def check(self, tensoreA, tensoreB):
		print("")
		if (tensoreA.size!=tensoreB.size):
			print("I due tensori hanno dimensioni diverse:")
			print(tensoreA.shape)
			print(tensoreB.shape)
			return
		tensoreA.shape = (tensoreA.size,)
		tensoreB.shape = (tensoreA.size,)
		confronto = (tensoreA==tensoreB)
		for i in range(tensoreB.size):
			if (not confronto[i]):
				print("Differenza in i =", i)
				print(tensoreA[i])
				print(tensoreB[i])
				return
		print("Sono uguali!")

	def deallocate(self):
		self.lib.deallocate()
		self.lib = None