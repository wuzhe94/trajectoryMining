import numpy as np
import pandas as pd
import tensorflow as tf
from sklearn.preprocessing import OneHotEncoder

def geo_filter(tra):
	'''
	A function for filtering abnormal latitude and longitude.
	:param tra: A pd.DataFrame records the trajectory data,
	containing a column named 'lat', which means latitude,
	and a column named 'lon', which means longitude.
	:return: A pd.DataFrame without abnormal latitude and longitude.
	'''
	tra_data = tra[(tra.lat < r_lat) & (tra.lat > l_lat)
				 & (tra.lon > l_lon) & (tra.lon < r_lon)]
	tra_data = tra_data.reset_index()
	del tra_data['index']
	return tra_data


def lost_VIN(tra_previous, tra_current):
	'''
	Some of the cars, which don't have normal latitude and longitude data,
	would be filtered out by the function geo_filter.
	This function is to record the VIN numbers of these lost cars.
	:param tra_previous: The original trajectory pd.DataFrame without filtering,
	containing a column named 'VIN', which is the identification number of a car.
	:param tra_current: The current filtered trajectory pd.DataFrame,
	containing a column named 'VIN', which is the identification number of a car.
	:return: A list records the VIN numbers of the lost lost cars.
	'''
	lost_vin = []
	for i in tra_previous.VIN.unique():
		if i not in tra_current.VIN.unique():
			lost_vin.append(i)
	return lost_vin


def mat_generation(tra_data):
	'''
	Generate trajectory matrix for each car based on its latitude and longtitude.
	:param tra_data: A trajectory pd.DataFrame,
	containing a column named 'VIN', which is the identification number of a car,
	and columns named 'lat' and 'lon', represent latitude and longitude.
	:return: A dictionary. The key is the VIN number, and the value is the trajectory matrix.
	'''
	tra_mat = {}
	for vin in tra_data.VIN.unique():
		v = tra_data[tra_data.VIN == vin]
		v = v.reset_index()
		del v['index']

		for i in range(len(v)):
			v_lat = v.iloc[i].lat
			v_lon = v.iloc[i].lon

			lat_st = l_lat
			lat_ed = lat_st + interval
			lon_st = l_lon
			lon_ed = lon_st + interval

			for j in range(len(lat_interval)):
				if (lat_st <= v_lat) and (v_lat < lat_ed):
					for k in range(len(lon_interval)):
						if (lon_st <= v_lon) and (v_lon < lon_ed):
							tra_mat.setdefault(v.iloc[i].VIN,
											   np.zeros((len(lat_interval),
														 len(lon_interval))))
							tra_mat[v.iloc[i].VIN][j][k] += 1
							break
						else:
							lon_st = lon_ed
							lon_ed = lon_st + interval
					break
				else:
					lat_st = lat_ed
					lat_ed = lat_st + interval

	return tra_mat

def mapDict2matVector(tra_mat):
	'''
	Convert the trajectory matrix of each car to a vector.
	:param tra_mat: A dictionary generated by function mat_generation.
	:return: one list records the VIN numbers, and another list records the vectors.
	'''
	vin = []
	vec = []
	for i in list(tra_mat.items()):
		vin.append(i[0])
		vec.append(i[1])
	for v in range(len(vec)):
		vec[v] = vec[v].reshape(1, dimension)[0]

	return vin, vec

def freq(tra_data):
	'''
	Calculate the frequency of each car.
	:param tra_data: A trajectory pd.DataFrame.
	:return: A dictionary records the frequency of each car.
	'''
	freq = {}
	for i in tra.VIN.unique():
		freq.setdefault(i,0)
		freq[i] = len(tra_data[tra_data.VIN == i])
	return freq

def weight(freq):
	'''
	Calculate the weight of each car.
	:param freq: A dictionary records the frequency of each car.
	:return: A dictionary records the weight of each car.
	'''
	weight = {}
	mx = max(freq.values())
	for i, j in freq.items():
		weight[i] = (j / (mx + 0.01))
	return weight

def get_label(vin, label):
	'''
	Get the labels of cars that you are caring about.
	:param vin: The VIN number of the cars that you are looking for their labels.
	:param label: The label pd.DataFrame.
	:return: The labels of the cares that you are caring about.
	'''
	label_train = []
	for i in vin:
		label_train.append(label[label.VIN == i]['label'].iloc[0])
	return label_train

def vec4train(mat_train, label_train, vin_train, w):
	'''
	Convert the original data into a new data format, which is suitable for model training.
	:param mat_train: Trajectory matrices of the cars which are used for model training.
	:param label_train: Labels of the cars which are used for model training.
	:param vin_train: VIN numbers of the cars which are used for model training.
	:param w: to describe the different importance of different cars
	:return: Data in a new format which is suitable for model training.
	'''
	train_x = np.array(mat_train)
	train_y0 = np.array(label_train)
	train_y = []
	for i in range(len(train_x)):
		train_x[i] = train_x[i] / max(train_x[i]) * w[vin_train[i]] * 10

	for i in train_y0:
		# class 'U' ==> class 0
		if i == 'U':
			train_y.append([0])
		# class 'P' ==> class 1
		else:
			train_y.append([1])

	train_y = np.array(train_y)
	train_y = OneHotEncoder().fit_transform(train_y).todense()

	return train_x, train_y

def vec4predict(mat_test, vin_test, cont_test):
	'''
	Convert the original data into a new data format, which is suitable for model testing.
	:param mat_test: Trajectory matrices of the cars which are used for model testing.
	:param vin_test: VIN numbers of the cars which are used for model training.
	:param cont_test: to describe the different importance of different cars
	:return: Data in a new format which is suitable for model tresing.
	'''
	test_x = np.array(mat_test)
	for i in range(len(test_x)):
		test_x[i] = test_x[i] / max(test_x[i]) * cont_test[vin_test[i]] * 10

	return test_x

def weight_variable(shape):
	initial = tf.truncated_normal(shape, stddev=0.1)
	return tf.Variable(initial)

def bias_variable(shape):
	initial = tf.constant(0.1, shape = shape)
	return tf.Variable(initial)

def conv2d(x, W):
	return tf.nn.conv2d(x, W, strides = [1, 1, 1, 1], padding = 'SAME')

def max_pool_2x2(x):
	return tf.nn.max_pool(x, ksize = [1, 2, 2, 1],
						  strides = [1, 2, 2, 1], padding = 'SAME')

def generatebatch(x, y, n_examples, batch_size):
	for batch_i in range(n_examples // batch_size):
		start = batch_i * batch_size
		end = start + batch_size
		batch_xs = x[start:end]
		batch_ys = y[start:end]
		yield batch_xs, batch_ys

if __name__ == '__main__':

	# latitude and longitude interval span
	interval = 0.019

	# the range of latitude and longitude, take Shanghai city as an example
	l_lat = 30.9
	r_lat = 31.5
	l_lon = 121.1
	r_lon = 121.7

	# map Shanghai city into a matrix based on the latitude and longtitude
	lat_interval = np.arange(l_lat, r_lat, interval)
	lon_interval = np.arange(l_lon, r_lon, interval)

	dimension = len(lat_interval) * len(lon_interval)

	tra = pd.read_csv('tra.csv',
					  usecols = [1, 2, 3])

	label = pd.read_csv('label.csv',
						header = None,
						usecols = [0, 1],
						names = ['VIN', 'label'])

	tra_train = geo_filter(tra)

	lost_vin = lost_VIN(tra, tra_train)

	tra_mat_train = mat_generation(tra_train)

	vin_train, mat_train = mapDict2matVector(tra_mat_train)

	w = weight(freq(tra_train))

	label_train = get_label(vin_train, label)

	train_x, train_y = vec4train(mat_train, label_train, vin_train, w)

	trainX = train_x[:232]
	trainY = train_y[:232]

	testX = train_x[232:]
	testY = train_y[232:]

	# start constructing the tensorflow graph
	# x as input and y_ as output
	x = tf.placeholder("float", [None, dimension])
	y_ = tf.placeholder("float", [None, 2])

	# reshape the input to 4 dimension vectors
	x_mat = tf.reshape(x, [-1, len(lat_interval), len(lon_interval), 1])

	# the filter and bias of the first layer
	W_conv1 = weight_variable([2, 2, 1, 60])
	b_conv1 = bias_variable([60])

	# construct the hidden layer and max pooling layer
	h_conv1 = tf.nn.relu(conv2d(x_mat, W_conv1) + b_conv1)
	h_pool1 = max_pool_2x2(h_conv1)

	# the filter and bias of the second layer
	W_conv2 = weight_variable([2, 2, 60, 90])
	b_conv2 = bias_variable([90])

	# construct the hidden layer and max pooling layer
	h_conv2 = tf.nn.relu(conv2d(h_pool1, W_conv2) + b_conv2)
	h_pool2 = max_pool_2x2(h_conv2)

	# construct the full connected layer
	W_fc1 = weight_variable([(len(lat_interval) // 4 ) * (len(lat_interval) // 4 ) * 90, 1024])
	b_fc1 = bias_variable([1024])

	h_pool2_flat = tf.reshape(h_pool2, [-1, (len(lat_interval) // 4) * (len(lat_interval) // 4 ) * 90])
	h_fc1 = tf.nn.relu(tf.matmul(h_pool2_flat, W_fc1) + b_fc1)

	# drop out
	keep_prob = tf.placeholder("float")
	h_fc1_drop = tf.nn.dropout(h_fc1, keep_prob)

	# construct the output layer
	W_fc2 = weight_variable([1024, 2])
	b_fc2 = bias_variable([2])

	# construct the cnn
	y_conv = tf.nn.softmax(tf.matmul(h_fc1_drop, W_fc2) + b_fc2)

	# difine the cross_entropy
	cross_entropy = -tf.reduce_sum(y_ * tf.log(y_conv))

	# construct optimizer to minimize the cross entropy
	train_step = tf.train.AdamOptimizer(1e-5).minimize(cross_entropy)

	# calculate the accuracy
	correct_prediction = tf.equal(tf.argmax(y_conv, 1), tf.argmax(y_, 1))
	accuracy = tf.reduce_mean(tf.cast(correct_prediction, "float"))

	# start the tensorflow graph
	sess =tf.Session()
	sess.run(tf.global_variables_initializer())
	batch_size = 30

	with sess.as_default():
		cnt = 0
		for i in range(5000):
			if cnt == 0:
				g = generatebatch(trainX, trainY, trainY.shape[0], batch_size)
			batch_xs, batch_ys = next(g)
			cnt += 1
			if cnt == trainY.shape[0] // batch_size:
				cnt = 0

			train_step.run(feed_dict = {x: batch_xs, y_: batch_ys, keep_prob: 0.5})

	with sess.as_default():
		print(accuracy.eval(feed_dict = {x:testX, y_: testY, keep_prob: 1}))


