import numpy as np
import pandas as pd
import tensorflow as tf
from sklearn.preprocessing import OneHotEncoder

# latitude and longitude interval span
interval = 0.02

# the range of latitude and longitude, take Shanghai city as an example
l_lat = 31.0
r_lat = 31.4
l_lon = 121.2
r_lon = 121.7

# map Shanghai city into a matrix based on the latitude and longtitude
lat_interval = np.arange(l_lat, r_lat, interval)
lon_interval = np.arange(l_lon, r_lon, interval)

def geo_filter(tra):
    tra_data = tra[(tra.lat < r_lat) & (tra.lat > l_lat)
                 & (tra.lon > l_lon) & (tra.lon < r_lon)]
    tra_data = tra_data.reset_index()
    del tra_data['index']
    return tra_data


def lost_VIN(tra_previous, tra_current):
	lost_vin = []
	for i in tra_previous.VIN.unique():
		if i not in tra_current.VIN.unique():
			lost_vin.append(i)
	return lost_vin


def mat_generation(tra):
	tra_mat = {}
	for vin in tra.VIN.unique():
		v = tra[tra.VIN == vin]
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

def mapDict2matVector(map_dict):
    vin = []
    mat = []
    for i in list(map_dict.items()):
        vin.append(i[0])
        mat.append(i[1])
    for m in range(len(mat)):
        mat[m] = mat[m].reshape(1, 500)[0]
    return vin,mat

def freq(tra):
    freq = {}
    for i in tra.VIN.unique():
        freq.setdefault(i,0)
        freq[i] = len(tra[tra.VIN == i])
    return freq

def weight(freq):
	weight = {}
    mx = max(freq.values())
    for i,j in freq.items():
        weight[i] = (j / mx)
    return weight

def get_label(vin):
    label_train = []
    for i in vin:
        label_train.append(label[label.VIN == i]['label'].iloc[0])
    return label_train

def vec4train(mat_train, label_train, vin_train):
	train_x = np.array(mat_train)
	train_y0 = np.array(label_train)
	train_y = []
	for i in range(len(train_x)):
		train_x[i] = train_x[i] / max(train_x[i]) * cont[vin_train[i]] * 10

	for i in train_y0:
		# uber ======== 0
		if i == 'U':
			train_y.append([0])
		# private ======== 1
		else:
			train_y.append([1])

	train_y = np.array(train_y)
	train_y = OneHotEncoder().fit_transform(train_y).todense()

	return train_x, train_y

def vec4predict(mat_test, vin_test):
	test_x = np.array(mat_test)
	for i in range(len(test_x)):
		test_x[i] = test_x[i] / max(test_x[i]) * cont_test[vin_test[i]] * 10

	return test_x