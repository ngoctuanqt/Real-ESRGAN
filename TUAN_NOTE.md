1. install miniconda https://docs.conda.io/en/latest/miniconda.html
2. install git https://git-scm.com/download/win
3. open miniconda
	check cuda version: conda list cudatoolkit or nvidia-smi
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
	

6. set context menu:

	Run Registry Editor (regedit.exe)

	Go to HKEY_CLASSES_ROOT > Directory > Background > shell

	Add a key named AnacondaPrompt and set its value to Anaconda Prompt Here

	Add a key under this key called command, and set its value to cmd.exe /K C:\Users\user\Anaconda3\Scripts\activate.bat change the location to wherever your Anaconda installation is located.
