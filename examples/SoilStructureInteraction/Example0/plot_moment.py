import os
import re
import sys
import numpy as np
from xml.etree import ElementTree as ET


def parse_xml_to_elements_and_data(path):
	if not os.path.exists(path):
		raise FileNotFoundError(path)
	raw = open(path, 'r', encoding='utf-8', errors='ignore').read()

	try:
		tree = ET.fromstring(raw)
	except ET.ParseError:
		raise

	# Extract elements: node1 and node2 from ElementOutput entries in document order
	elements = []
	for elem in tree.findall('.//ElementOutput'):
		node1 = elem.attrib.get('node1')
		node2 = elem.attrib.get('node2')
		# convert to int when possible, otherwise keep as string
		try:
			n1 = int(node1) if node1 is not None else -1
		except Exception:
			n1 = node1
		try:
			n2 = int(node2) if node2 is not None else -1
		except Exception:
			n2 = node2
		elements.append((n1, n2))

	elements_arr = np.array(elements)

	# Extract <Data> block text
	data_elem = tree.find('.//Data')
	if data_elem is None or data_elem.text is None:
		raise ValueError('No <Data> block with numeric content found')

	data_text = data_elem.text
	float_re = re.compile(r'[+-]?\d*\.?\d+(?:[eE][+-]?\d+)?')
	rows = []
	for line in data_text.splitlines():
		line = line.strip()
		if not line:
			continue
		nums = float_re.findall(line)
		if not nums:
			continue
		rows.append([float(x) for x in nums])

	if not rows:
		raise ValueError('No numeric rows parsed from <Data> block')

	data_arr = np.array(rows, dtype=float)

	return elements_arr, data_arr


if __name__ == '__main__':
	# Default path relative to script
	default = os.path.join(os.path.dirname(__file__), 'Results', 'pile_force_pile_Core0_globalForce.xml')
	path = sys.argv[1] if len(sys.argv) > 1 else default

	elements, data = parse_xml_to_elements_and_data(path)
	print(elements.shape)
	print(data.shape)
	time = data[:, 0]
	data = data[:, 1:]  # remove time column
	Px = data[:, 0::12]  # shear forces x    
	Py = data[:, 1::12]  # shear forces y
	Pz = data[:, 2::12]  # axial forces z
	Mx = data[:, 3::12]  # moments x
	My = data[:, 4::12]  # moments y
	Mz = data[:, 5::12]  # torsional moments z
	
    # add the last 
	lastPx = -data[:, -12]
	lastPy = -data[:, -11]
	lastPz = -data[:, -10]
	lastMx = -data[:, -9]
	lastMy = -data[:, -8]   
	lastMz = -data[:, -7]
	Px = np.hstack([Px, lastPx[:, np.newaxis]])
	Py = np.hstack([Py, lastPy[:, np.newaxis]])
	Pz = np.hstack([Pz, lastPz[:, np.newaxis]])
	Mx = np.hstack([Mx, lastMx[:, np.newaxis]])
	My = np.hstack([My, lastMy[:, np.newaxis]])
	Mz = np.hstack([Mz, lastMz[:, np.newaxis]])
	Px = Px[-1, :]
	Py = Py[-1, :]
	Pz = Pz[-1, :]
	Mx = Mx[-1, :]
	My = My[-1, :]
	Mz = Mz[-1, :]
	
	
    # Simple plots
	import matplotlib.pyplot as plt
	depths  = np.linspace(-5, 2, elements.shape[0] + 1)  # example depths for plotting
	fig, ax = plt.subplots(3, 2, figsize=(6, 8), constrained_layout=True)
	ax[0, 0].plot(Px, depths, "-", alpha=1.0)
	ax[0, 1].plot(Py, depths, "-", alpha=1.0)
	ax[1, 0].plot(Pz, depths, "-", alpha=1.0)
	ax[1, 1].plot(Mx, depths, "-", alpha=1.0)
	ax[2, 0].plot(My, depths, "-", alpha=1.0)
	ax[2, 1].plot(Mz, depths, "-", alpha=1.0)
	ax[0, 1].set_title('Shear Forces Py')
	ax[1, 0].set_title('Axial Forces Pz')
	ax[1, 1].set_title('Moments Mx')
	ax[2, 0].set_title('Moments My')
	ax[0, 0].set_title('Shear Forces Px')
	ax[2, 1].set_title('Torsional Moments Mz')
	for a in ax.flatten():
		a.grid(True, which='both', linestyle='--', alpha=0.5)
		a.set_xlabel('Force / Moment')
		a.set_ylabel('Depth')
		# line at the center
		# a.axhline(0, color='black', linewidth=0.8, linestyle='--', alpha=0.7)
		a.axvline(0, color='black', linewidth=0.8, linestyle='-', alpha=0.7)
	# save figure 
	import os 
	os.chdir(os.path.dirname(__file__))
	fig.savefig('pile_forces_moments.png', dpi=300, bbox_inches='tight')
	plt.show()


