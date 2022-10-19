1. install miniconda
2. install git
3. open miniconda
	check cuda version: conda list cudatoolkit
	install touch:
		pip3 install torch torchvision torchaudio --extra-index-url https://download.pytorch.org/whl/cu116
		pip3 install torch torchvision torchaudio --extra-index-url https://download.pytorch.org/whl/cu113
		pip3 install torch torchvision torchaudio
4. clone:
	git clone https://github.com/ngoctuanqt/Real-ESRGAN.git
	cd Real-ESRGAN
5. config
	pip install basicsr
	pip install facexlib
	pip install gfpgan
	pip install -r requirements.txt
	python setup.py develop