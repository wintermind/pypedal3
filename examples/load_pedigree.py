from PyPedal import new_classes

if __name__ == '__main__':

	options = {
		pedfile = 'pedigrees/elevation.ped',
		sepchar = ',',
		pedformat = 'ASDnbx',
	}

	elevation = pyp_newclasses.loadPedigree(options)
